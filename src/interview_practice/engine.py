"""Application service that composes providers, prompts, guardrails and caps."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from interview_practice.config import Settings
from interview_practice.cost import (
    CatalogError,
    ModelCatalog,
    default_catalog,
    estimate_cost,
    fetch_model_catalog,
)
from interview_practice.guardrails import GuardrailPipeline, GuardrailResult
from interview_practice.messages import ChatMessage
from interview_practice.prompts import (
    DEFAULT_PERSONA,
    DEFAULT_TECHNIQUE,
    PromptLibrary,
    SystemPromptIntegrityError,
    validate_system_messages,
)
from interview_practice.prompts.schemas import (
    AnswerEvaluation,
    InterviewRubric,
    JudgeScore,
    QuestionSet,
    SchemaError,
    parse_json_object,
    validate_answer_evaluation,
    validate_interview_rubric,
    validate_judge_score,
    validate_question_set,
)
from interview_practice.providers import build_provider
from interview_practice.providers.base import (
    Completion,
    CompletionRequest,
    Provider,
    ProviderError,
)
from interview_practice.retrieval import MemoryUnavailable, QuestionMemory
from interview_practice.session import GlobalBudget, SessionState
from interview_practice.tailoring import build_tailored_context
from interview_practice.usage import CallUsage


class EngineError(RuntimeError):
    """A user-facing error with no secret or raw provider payload."""


MAX_ROLE_CHARS = 120
MAX_QUESTION_CHARS = 500
MAX_ANSWER_CHARS = 4000
MAX_CHAT_CHARS = 4000


@dataclass(frozen=True, slots=True)
class QuestionGenerationResult:
    question_set: QuestionSet
    warnings: tuple[str, ...]
    notice: str
    technique: str
    usage: CallUsage
    usages: tuple[CallUsage, ...] = ()
    total_cost_usd: float | None = None


@dataclass(frozen=True, slots=True)
class EvaluationResult:
    evaluation: AnswerEvaluation
    warnings: tuple[str, ...]
    technique: str
    usage: CallUsage


@dataclass(frozen=True, slots=True)
class JudgeResult:
    judge: JudgeScore
    warnings: tuple[str, ...]
    usage: CallUsage


@dataclass(frozen=True, slots=True)
class RubricResult:
    rubric: InterviewRubric
    warnings: tuple[str, ...]
    usage: CallUsage


@dataclass(frozen=True, slots=True)
class ChatResult:
    reply: str
    warnings: tuple[str, ...]
    technique: str
    persona: str
    usage: CallUsage


class InterviewEngine:
    def __init__(
        self,
        settings: Settings,
        *,
        provider: Provider | None = None,
        session: SessionState | None = None,
        catalog: ModelCatalog | None = None,
        global_budget: GlobalBudget | None = None,
    ) -> None:
        try:
            settings.validate()
        except ValueError as exc:
            raise EngineError(str(exc)) from exc
        self.settings = settings
        try:
            self.provider = provider or build_provider(settings)
        except ProviderError as exc:
            raise EngineError(str(exc)) from exc
        self.session = session or SessionState()
        self.catalog = catalog or default_catalog()
        self.global_budget = global_budget or GlobalBudget(
            max_calls_per_day=settings.global_max_calls_per_day,
            max_cost_per_day=settings.global_max_cost_per_day,
            max_calls_per_minute=settings.global_rate_per_minute,
        )
        self.prompts = PromptLibrary()
        self._question_memory: QuestionMemory | None = None
        self.guardrails = GuardrailPipeline(
            max_input_chars=settings.max_input_chars,
            max_output_chars=max(12_000, settings.max_output_tokens * 8),
            strict=settings.strict_safety,
        )

    def refresh_catalog(self) -> bool:
        if self.settings.provider != "openrouter":
            return False
        try:
            self.catalog = fetch_model_catalog(
                api_key=self.settings.openrouter_api_key
            )
        except CatalogError:
            return False
        return True

    def list_models(self) -> list[str]:
        try:
            return self.provider.list_models()
        except ProviderError as exc:
            raise EngineError(str(exc)) from exc

    def generate_questions(
        self,
        *,
        role: str,
        job_description: str,
        difficulty: str = "medium",
        count: int = 5,
        technique: str = DEFAULT_TECHNIQUE,
    ) -> QuestionGenerationResult:
        role = role.strip() or "AI engineer"
        self._check_length(role, "role", MAX_ROLE_CHARS)
        difficulty = difficulty.strip().lower()
        if difficulty not in {"easy", "medium", "hard"}:
            raise EngineError("Difficulty must be easy, medium, or hard.")
        if not 1 <= count <= 8:
            raise EngineError("Question count must be between 1 and 8.")

        warnings: list[str] = []
        self._extend_unique(warnings, self._check_input(role, "role"))
        if job_description.strip():
            self._extend_unique(
                warnings, self._check_input(job_description, "job description")
            )

        query = f"{role} {difficulty} {job_description[:2000]}"
        context = build_tailored_context(
            job_description,
            query=query,
            enable_lexical_rag=self.settings.enable_lexical_rag,
            max_chars=self.settings.max_input_chars,
        )
        if context.text:
            self._extend_unique(
                warnings, self._check_input(context.text, "job description")
            )

        usages: list[CallUsage] = []
        requirements = ""
        if technique == "chained":
            first_messages = self.prompts.chain_stage_one(
                role=role,
                job_description=context.text,
                canary=self.session.canary,
                domain=self.settings.domain_profile,
                style=self.settings.response_style,
            )
            first_completion, first_usage = self._call(
                self.prompts.with_budget(
                    first_messages, self._effective_max_tokens()
                )
            )
            self._add_notice(first_completion, warnings)
            usages.append(first_usage)
            first_guard = self._check_output(first_completion.text)
            warnings.extend(first_guard.warnings)
            requirements = first_guard.text

        messages = self.prompts.with_budget(
            self.prompts.question_set(
                technique,
                role=role,
                job_description=context.text,
                difficulty=difficulty,
                count=count,
                canary=self.session.canary,
                requirements=requirements,
                domain=self.settings.domain_profile,
                style=self.settings.response_style,
            ),
            self._effective_max_tokens(),
        )
        completion, usage = self._call(
            messages,
            response_format={"type": "json_object"},
        )
        self._add_notice(completion, warnings)
        usages.append(usage)
        guarded = self._check_output(completion.text)
        warnings.extend(guarded.warnings)
        try:
            payload = parse_json_object(guarded.text)
            question_set = validate_question_set(payload)
        except SchemaError as exc:
            if self._is_truncated(completion):
                raise EngineError(self._truncation_message("question set")) from exc
            raise EngineError(
                "The model returned an invalid question-set JSON object. "
                "Try again or switch prompt technique."
            ) from exc
        if self.settings.enable_question_memory:
            model = self._active_model()
            try:
                memory = self._get_memory()
                duplicate = any(
                    memory.has_near_duplicate(
                        question.question,
                        provider=self.settings.provider,
                        model=model,
                    )
                    for question in question_set.questions
                )
                if duplicate:
                    warnings.append(
                        "Near-duplicate question detected; regenerated once."
                    )
                    retry_messages = self.prompts.with_budget(
                        self.prompts.question_set(
                            technique,
                            role=role,
                            job_description=context.text,
                            difficulty=difficulty,
                            count=count,
                            canary=self.session.canary,
                            requirements=(
                                requirements
                                + "\nAvoid questions close to earlier questions."
                            ),
                            domain=self.settings.domain_profile,
                            style=self.settings.response_style,
                        ),
                        self._effective_max_tokens(),
                    )
                    retry_completion, retry_usage = self._call(
                        retry_messages,
                        response_format={"type": "json_object"},
                    )
                    self._add_notice(retry_completion, warnings)
                    usages.append(retry_usage)
                    retry_guard = self._check_output(retry_completion.text)
                    self._extend_unique(warnings, retry_guard.warnings)
                    try:
                        question_set = validate_question_set(
                            parse_json_object(retry_guard.text)
                        )
                    except SchemaError as retry_exc:
                        if self._is_truncated(retry_completion):
                            raise EngineError(
                                self._truncation_message("question set")
                            ) from retry_exc
                        raise
                memory.add_questions(
                    question_set.questions,
                    provider=self.settings.provider,
                    model=model,
                )
            except MemoryUnavailable:
                self._extend_unique(
                    warnings,
                    (
                        "Question memory unavailable; duplicate check skipped.",
                    ),
                )
            except SchemaError as exc:
                raise EngineError(
                    "Question memory could not be updated."
                ) from exc
        return QuestionGenerationResult(
            question_set=question_set,
            warnings=tuple(warnings),
            notice=context.notice,
            technique=technique,
            usage=usage,
            usages=tuple(usages),
            total_cost_usd=_total_cost(usages),
        )

    def evaluate_answer(
        self,
        *,
        question: str,
        answer: str,
        job_description: str = "",
        technique: str = DEFAULT_TECHNIQUE,
    ) -> EvaluationResult:
        question = question.strip()
        answer = answer.strip()
        if not question:
            raise EngineError("Choose or write a question first.")
        if not answer:
            raise EngineError("Write an answer before requesting feedback.")
        self._check_length(question, "question", MAX_QUESTION_CHARS)
        self._check_length(answer, "answer", MAX_ANSWER_CHARS)

        warnings: list[str] = []
        self._extend_unique(warnings, self._check_input(question, "question"))
        self._extend_unique(warnings, self._check_input(answer, "answer"))
        if job_description.strip():
            self._extend_unique(
                warnings, self._check_input(job_description, "job description")
            )

        messages = self.prompts.with_budget(
            self.prompts.answer_evaluation(
                technique,
                question=question,
                answer=answer,
                job_description=job_description,
                canary=self.session.canary,
                domain=self.settings.domain_profile,
                style=self.settings.response_style,
            ),
            self._effective_max_tokens(),
        )
        completion, usage = self._call(
            messages,
            response_format={"type": "json_object"},
        )
        self._add_notice(completion, warnings)
        guarded = self._check_output(completion.text)
        warnings.extend(guarded.warnings)
        try:
            payload = parse_json_object(guarded.text)
            evaluation = validate_answer_evaluation(payload)
        except SchemaError as exc:
            if self._is_truncated(completion):
                raise EngineError(self._truncation_message("evaluation")) from exc
            raise EngineError(
                "The model returned an invalid evaluation JSON object. "
                "Try again or switch prompt technique."
            ) from exc
        self.session.last_question = question
        self.session.last_answer = answer
        return EvaluationResult(
            evaluation=evaluation,
            warnings=tuple(warnings),
            technique=technique,
            usage=usage,
        )

    def generate_rubric(
        self,
        *,
        role: str,
        job_description: str = "",
    ) -> RubricResult:
        role = role.strip() or "AI engineer"
        self._check_length(role, "role", MAX_ROLE_CHARS)
        warnings: list[str] = []
        if job_description.strip():
            self._extend_unique(
                warnings, self._check_input(job_description, "job description")
            )
        messages = self.prompts.with_budget(
            self.prompts.rubric(
                role=role,
                job_description=job_description,
                canary=self.session.canary,
                domain=self.settings.domain_profile,
                style=self.settings.response_style,
            ),
            self._effective_max_tokens(),
        )
        completion, usage = self._call(
            messages,
            response_format={"type": "json_object"},
        )
        self._add_notice(completion, warnings)
        guarded = self._check_output(completion.text)
        self._extend_unique(warnings, guarded.warnings)
        try:
            rubric = self._parse_rubric(guarded.text, role)
        except SchemaError as exc:
            if self._is_truncated(completion):
                raise EngineError(self._truncation_message("rubric")) from exc
            repair = ChatMessage(
                "user",
                "The previous rubric did not match the schema: "
                f"{exc}. Return one JSON object only. Use only these keys: "
                "technical_depth, problem_solving, communication, role_fit, "
                "collaboration, ownership. Every weight must be an integer and "
                "the weights must total exactly 100.",
            )
            repair_messages = [
                *messages[:-1],
                ChatMessage("user", messages[-1].content + "\n\n" + repair.content),
            ]
            completion, usage = self._call(
                repair_messages,
                response_format={"type": "json_object"},
            )
            self._add_notice(completion, warnings)
            guarded = self._check_output(completion.text)
            self._extend_unique(warnings, guarded.warnings)
            try:
                rubric = self._parse_rubric(guarded.text, role)
            except SchemaError as retry_exc:
                if self._is_truncated(completion):
                    raise EngineError(
                        self._truncation_message("rubric")
                    ) from retry_exc
                raise EngineError(
                    "The model returned an invalid rubric: "
                    f"{retry_exc}. Try again, raise Max output tokens, or "
                    "switch models."
                ) from retry_exc
        return RubricResult(rubric=rubric, warnings=tuple(warnings), usage=usage)

    def _parse_rubric(self, text: str, role: str) -> InterviewRubric:
        payload = parse_json_object(text)
        return validate_interview_rubric(payload, default_role=role)

    def _is_truncated(self, completion: Completion) -> bool:
        return completion.finish_reason in {"length", "max_tokens"}

    def _effective_max_tokens(self) -> int:
        return min(self.settings.max_tokens, self.settings.max_output_tokens)

    def _truncation_message(self, label: str) -> str:
        return (
            f"The {label} output was truncated at the "
            f"{self._effective_max_tokens()}-token output cap before it was "
            "complete. Raise Max output tokens or reduce the requested detail."
        )

    def judge_answer(
        self,
        *,
        question: str,
        answer: str,
        evaluation: AnswerEvaluation,
    ) -> JudgeResult:
        if not self.settings.enable_llm_judge:
            raise EngineError("Enable the LLM judge in settings first.")
        question = question.strip()
        answer = answer.strip()
        if not question or not answer:
            raise EngineError("Question and answer are required for the judge.")
        messages = self.prompts.with_budget(
            self.prompts.judge(
                question=question,
                answer=answer,
                evaluation_json=json.dumps(evaluation.to_dict()),
                canary=self.session.canary,
                domain=self.settings.domain_profile,
                style=self.settings.response_style,
            ),
            self._effective_max_tokens(),
        )
        completion, usage = self._call(
            messages,
            response_format={"type": "json_object"},
        )
        guarded = self._check_output(completion.text)
        warnings = list(guarded.warnings)
        self._add_notice(completion, warnings)
        try:
            judge = validate_judge_score(parse_json_object(guarded.text))
        except SchemaError as exc:
            if self._is_truncated(completion):
                raise EngineError(self._truncation_message("judge")) from exc
            raise EngineError(
                "The judge returned an invalid JSON object. Try again."
            ) from exc
        return JudgeResult(
            judge=judge,
            warnings=tuple(warnings),
            usage=usage,
        )

    def chat(
        self,
        *,
        user_message: str,
        history: list[ChatMessage],
        job_description: str = "",
        technique: str = DEFAULT_TECHNIQUE,
        persona: str = DEFAULT_PERSONA,
        current_question: str = "",
        current_evaluation: str = "",
    ) -> ChatResult:
        user_message = user_message.strip()
        if not user_message:
            raise EngineError("Write a message first.")
        self._check_length(user_message, "chat message", MAX_CHAT_CHARS)
        warnings = list(self._check_input(user_message, "chat message"))
        if job_description.strip():
            self._extend_unique(
                warnings, self._check_input(job_description, "job description")
            )
        completion, usage = self._call(
            self.prompts.chat(
                technique,
                history=history,
                user_message=user_message,
                job_description=job_description,
                canary=self.session.canary,
                persona=persona,
                current_question=current_question,
                current_evaluation=current_evaluation,
                domain=self.settings.domain_profile,
                style=self.settings.response_style,
            )
        )
        self._add_notice(completion, warnings)
        guarded = self._check_output(completion.text)
        warnings.extend(guarded.warnings)
        if self._is_truncated(completion):
            self._extend_unique(
                warnings,
                ("The reply hit the output cap and may be truncated.",),
            )
        return ChatResult(
            reply=guarded.text,
            warnings=tuple(warnings),
            technique=technique,
            persona=persona,
            usage=usage,
        )

    def _active_model(self) -> str:
        if self.settings.provider == "demo":
            return "demo/interview-coach"
        if self.settings.provider == "local":
            return self.settings.local_model
        return self.settings.model

    def _get_memory(self) -> QuestionMemory:
        if self._question_memory is None:
            self._question_memory = QuestionMemory(self.settings)
        return self._question_memory

    def _call(
        self,
        messages: list[ChatMessage],
        *,
        response_format: dict[str, Any] | None = None,
    ) -> tuple[Completion, CallUsage]:
        try:
            self.session.can_call(self.settings)
            self.global_budget.acquire()
        except RuntimeError as exc:
            raise EngineError(str(exc)) from exc
        if self.settings.provider == "demo":
            model = "demo/interview-coach"
        elif self.settings.provider == "local":
            model = self.settings.local_model
        else:
            model = self.settings.model
        model_info = self.catalog.get(model)
        supports_json = bool(model_info and model_info.supports("response_format"))
        supports_reasoning = bool(
            model_info and model_info.supports("reasoning")
        )
        max_tokens: int | None = (
            None
            if self.settings.provider == "local"
            and self.settings.local_uncapped_output
            else min(self.settings.max_tokens, self.settings.max_output_tokens)
        )
        request = CompletionRequest(
            messages=messages,
            model=model,
            temperature=self.settings.temperature,
            max_tokens=max_tokens,
            top_p=self.settings.top_p,
            reasoning_effort=(
                self.settings.reasoning_effort
                if self.settings.provider == "openrouter" and supports_reasoning
                else None
            ),
            response_format=response_format if supports_json else None,
        )
        try:
            validate_system_messages(messages, self.session.canary)
        except SystemPromptIntegrityError as exc:
            raise EngineError("System prompt integrity check failed.") from exc
        try:
            completion = self.provider.complete(request)
        except ProviderError as exc:
            raise EngineError(str(exc)) from exc
        cost_info = self.catalog.get(completion.model) or model_info
        estimated = estimate_cost(
            completion.prompt_tokens,
            completion.completion_tokens,
            cost_info,
        )
        if completion.cost_usd is not None:
            cost = completion.cost_usd
            source = "provider"
        elif estimated is not None:
            cost = estimated
            source = "estimate"
        else:
            cost = None
            source = "unavailable"
        usage = CallUsage(
            model=completion.model,
            provider=completion.provider,
            prompt_tokens=completion.prompt_tokens,
            completion_tokens=completion.completion_tokens,
            total_tokens=completion.total_tokens,
            cost_usd=cost,
            cost_source=source,
            latency_ms=completion.latency_ms,
        )
        self.session.record(usage)
        self.global_budget.record(usage)
        return completion, usage

    @staticmethod
    def _add_notice(completion: Completion, warnings: list[str]) -> None:
        if completion.notice and completion.notice not in warnings:
            warnings.append(completion.notice)

    @staticmethod
    def _check_length(text: str, label: str, limit: int) -> None:
        if len(text) > limit:
            raise EngineError(
                f"{label.capitalize()} must be at most {limit} characters."
            )

    def _check_input(self, text: str, label: str) -> tuple[str, ...]:
        result = self.guardrails.check_input(text)
        if not result.allowed:
            reason = result.blocked_reason or "unsafe input"
            raise EngineError(f"{label.capitalize()} blocked: {reason}")
        return result.warnings

    def _check_output(self, text: str) -> GuardrailResult:
        result = self.guardrails.check_output(text, canary=self.session.canary)
        if not result.allowed:
            raise EngineError(
                "The model output was blocked by the safety guard: "
                + (result.blocked_reason or "unsafe output")
            )
        return result

    @staticmethod
    def _extend_unique(target: list[str], values: tuple[str, ...]) -> None:
        for value in values:
            if value not in target:
                target.append(value)


def _total_cost(usages: list[CallUsage]) -> float | None:
    if not usages or any(usage.cost_usd is None for usage in usages):
        return None
    return sum(usage.cost_usd or 0.0 for usage in usages)
