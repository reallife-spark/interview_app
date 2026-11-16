"""Application service that composes providers, prompts, guardrails and caps."""

from __future__ import annotations

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
)
from interview_practice.prompts.schemas import (
    AnswerEvaluation,
    QuestionSet,
    SchemaError,
    parse_json_object,
    validate_answer_evaluation,
    validate_question_set,
)
from interview_practice.providers import build_provider
from interview_practice.providers.base import (
    Completion,
    CompletionRequest,
    Provider,
    ProviderError,
)
from interview_practice.session import SessionState
from interview_practice.tailoring import build_tailored_context
from interview_practice.usage import CallUsage


class EngineError(RuntimeError):
    """A user-facing error with no secret or raw provider payload."""


@dataclass(frozen=True, slots=True)
class QuestionGenerationResult:
    question_set: QuestionSet
    warnings: tuple[str, ...]
    notice: str
    technique: str
    usage: CallUsage


@dataclass(frozen=True, slots=True)
class EvaluationResult:
    evaluation: AnswerEvaluation
    warnings: tuple[str, ...]
    technique: str
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
        self.prompts = PromptLibrary()
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

        requirements = ""
        if technique == "chained":
            first_completion, _ = self._call(
                self.prompts.chain_stage_one(
                    role=role,
                    job_description=context.text,
                    canary=self.session.canary,
                )
            )
            first_guard = self._check_output(first_completion.text)
            warnings.extend(first_guard.warnings)
            requirements = first_guard.text

        completion, usage = self._call(
            self.prompts.question_set(
                technique,
                role=role,
                job_description=context.text,
                difficulty=difficulty,
                count=count,
                canary=self.session.canary,
                requirements=requirements,
            ),
            response_format={"type": "json_object"},
        )
        guarded = self._check_output(completion.text)
        warnings.extend(guarded.warnings)
        try:
            payload = parse_json_object(guarded.text)
            question_set = validate_question_set(payload)
        except SchemaError as exc:
            raise EngineError(
                "The model returned an invalid question-set JSON object. "
                "Try again or switch prompt technique."
            ) from exc
        return QuestionGenerationResult(
            question_set=question_set,
            warnings=tuple(warnings),
            notice=context.notice,
            technique=technique,
            usage=usage,
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

        warnings: list[str] = []
        self._extend_unique(warnings, self._check_input(question, "question"))
        self._extend_unique(warnings, self._check_input(answer, "answer"))
        if job_description.strip():
            self._extend_unique(
                warnings, self._check_input(job_description, "job description")
            )

        completion, usage = self._call(
            self.prompts.answer_evaluation(
                technique,
                question=question,
                answer=answer,
                job_description=job_description,
                canary=self.session.canary,
            ),
            response_format={"type": "json_object"},
        )
        guarded = self._check_output(completion.text)
        warnings.extend(guarded.warnings)
        try:
            payload = parse_json_object(guarded.text)
            evaluation = validate_answer_evaluation(payload)
        except SchemaError as exc:
            raise EngineError(
                "The model returned an invalid evaluation JSON object. "
                "Try again or switch prompt technique."
            ) from exc
        return EvaluationResult(
            evaluation=evaluation,
            warnings=tuple(warnings),
            technique=technique,
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
    ) -> ChatResult:
        user_message = user_message.strip()
        if not user_message:
            raise EngineError("Write a message first.")
        warnings = list(self._check_input(user_message, "chat message"))
        if job_description.strip() and not history:
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
            )
        )
        guarded = self._check_output(completion.text)
        warnings.extend(guarded.warnings)
        return ChatResult(
            reply=guarded.text,
            warnings=tuple(warnings),
            technique=technique,
            persona=persona,
            usage=usage,
        )

    def _call(
        self,
        messages: list[ChatMessage],
        *,
        response_format: dict[str, Any] | None = None,
    ) -> tuple[Completion, CallUsage]:
        try:
            self.session.can_call(self.settings)
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
        supports_reasoning = (
            True if model_info is None else model_info.supports("reasoning")
        )
        max_tokens = min(self.settings.max_tokens, self.settings.max_output_tokens)
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
        return completion, usage

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
