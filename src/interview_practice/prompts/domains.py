"""Personal-domain prompt profiles for interview preparation."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DomainProfile:
    key: str
    label: str
    instruction: str


DOMAIN_PROFILES: tuple[DomainProfile, ...] = (
    DomainProfile(
        key="ai_engineering",
        label="AI engineering",
        instruction=(
            "Focus on LLM applications, retrieval, evaluation, model serving, "
            "data quality and production trade-offs."
        ),
    ),
    DomainProfile(
        key="it",
        label="IT and infrastructure",
        instruction=(
            "Focus on systems, networking, reliability, security operations and "
            "incident response."
        ),
    ),
    DomainProfile(
        key="finance",
        label="Finance",
        instruction=(
            "Focus on controls, reconciliation, risk, reporting accuracy and "
            "regulatory constraints."
        ),
    ),
    DomainProfile(
        key="hr",
        label="HR and people",
        instruction=(
            "Focus on structured interviewing, fairness, stakeholder handling and "
            "confidentiality."
        ),
    ),
    DomainProfile(
        key="communication",
        label="Communication",
        instruction=(
            "Focus on clear structure, audience adaptation, evidence and "
            "follow-up questions."
        ),
    ),
)

_DOMAIN_BY_KEY = {profile.key: profile for profile in DOMAIN_PROFILES}
DEFAULT_DOMAIN = "ai_engineering"


def get_domain(key: str) -> DomainProfile:
    return _DOMAIN_BY_KEY.get(key, _DOMAIN_BY_KEY[DEFAULT_DOMAIN])


def domain_options() -> tuple[DomainProfile, ...]:
    return DOMAIN_PROFILES
