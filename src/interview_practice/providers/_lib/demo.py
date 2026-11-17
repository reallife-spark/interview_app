"""Deterministic demo provider used when no API key is configured."""

from __future__ import annotations

import json

from interview_practice.providers.base import Completion, CompletionRequest

DEMO_MODEL = "demo/interview-coach"


class DemoProvider:
    name = "demo"

    def list_models(self) -> list[str]:
        return [DEMO_MODEL]

    def complete(self, request: CompletionRequest) -> Completion:
        prompt = "\n".join(message.content for message in request.messages)
        lowered = prompt.lower()
        if "judge" in lowered or "firstpassevaluation" in lowered:
            text = _judge()
        elif "rubric" in lowered or "criteria covering" in lowered:
            text = _rubric()
        elif "questionset" in lowered or (
            "question" in lowered and "generate" in lowered
        ):
            text = _question_set()
        elif "answerevaluation" in lowered or "evaluate" in lowered:
            text = _answer_evaluation()
        else:
            text = _chat_reply()

        prompt_tokens = max(1, len(prompt) // 4)
        completion_tokens = max(1, len(text) // 4)
        return Completion(
            text=text,
            model=DEMO_MODEL,
            provider=self.name,
            latency_ms=0,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            cost_usd=0.0,
            finish_reason="stop",
        )


def _question_set() -> str:
    return json.dumps(
        {
            "role": "AI engineer",
            "questions": [
                {
                    "id": "q1",
                    "category": "technical",
                    "difficulty": "medium",
                    "question": (
                        "How would you evaluate a RAG system before shipping it?"
                    ),
                    "why": "Tests retrieval quality, grounding and failure analysis.",
                    "answer_points": [
                        "Separate retrieval from generation metrics",
                        "Use a labelled question-answer set",
                        "Check grounding, latency and cost",
                    ],
                },
                {
                    "id": "q2",
                    "category": "behavioural",
                    "difficulty": "medium",
                    "question": (
                        "Tell me about a time you changed a design after user "
                        "feedback."
                    ),
                    "why": "Tests reflection and stakeholder communication.",
                    "answer_points": [
                        "Situation and constraint",
                        "Specific user evidence",
                        "Trade-off and measured outcome",
                    ],
                },
                {
                    "id": "q3",
                    "category": "system-design",
                    "difficulty": "hard",
                    "question": (
                        "Design a prompt-evaluation pipeline for a "
                        "customer-facing assistant."
                    ),
                    "why": (
                        "Tests end-to-end thinking under safety and cost "
                        "constraints."
                    ),
                    "answer_points": [
                        "Versioned prompts and datasets",
                        "Automatic and human review",
                        "Regression gates and rollback",
                    ],
                },
            ],
        },
        indent=2,
    )


def _judge() -> str:
    return json.dumps(
        {
            "score": 78,
            "verdict": "Good with one evidence gap",
            "criteria": [
                {
                    "name": "Correctness",
                    "score": 80,
                    "rationale": "Names the right evaluation concepts.",
                },
                {
                    "name": "Evidence",
                    "score": 70,
                    "rationale": "Needs a concrete dataset and threshold.",
                },
                {
                    "name": "Communication",
                    "score": 84,
                    "rationale": "Clear structure and trade-offs.",
                },
            ],
            "rationale": (
                "The answer is technically sound but should add a measurable "
                "release gate and a rollback rule."
            ),
        },
        indent=2,
    )


def _rubric() -> str:
    return json.dumps(
        {
            "role": "AI engineer",
            "criteria": [
                {
                    "key": "technical_depth",
                    "label": "Technical depth",
                    "weight": 30,
                    "descriptors": [
                        "Names concrete systems and trade-offs",
                        "Avoids unsupported claims",
                    ],
                },
                {
                    "key": "problem_solving",
                    "label": "Problem solving",
                    "weight": 25,
                    "descriptors": [
                        "Explains diagnosis and alternatives",
                        "Uses evidence to choose a path",
                    ],
                },
                {
                    "key": "communication",
                    "label": "Communication",
                    "weight": 25,
                    "descriptors": [
                        "Structures the answer clearly",
                        "Checks understanding",
                    ],
                },
                {
                    "key": "role_fit",
                    "label": "Role fit",
                    "weight": 20,
                    "descriptors": [
                        "Connects examples to the role",
                        "Shows motivation and ownership",
                    ],
                },
            ],
        },
        indent=2,
    )


def _answer_evaluation() -> str:
    return json.dumps(
        {
            "score": 72,
            "summary": (
                "The answer names the core retrieval and generation checks, but "
                "the evaluation design needs a labelled set and a regression gate."
            ),
            "strengths": [
                "Separates retrieval from generation",
                "Mentions grounding and cost",
            ],
            "gaps": [
                "No concrete dataset or sample size",
                "No release threshold or rollback rule",
            ],
            "improved_answer": (
                "I would build a labelled set of question-answer pairs, score "
                "retrieval recall and answer groundedness separately, add "
                "latency and cost budgets, and block a release when the "
                "regression suite drops below the agreed threshold."
            ),
            "next_steps": [
                "Write one metric definition per failure mode",
                "Add a small regression set before the next practice attempt",
            ],
        },
        indent=2,
    )


def _chat_reply() -> str:
    return (
        "Demo coach: I can help you prepare for an AI engineering interview. "
        "Try the Prepare tab for a question set, or paste an answer in Practice "
        "for structured feedback. In live mode this reply comes from OpenRouter."
    )
