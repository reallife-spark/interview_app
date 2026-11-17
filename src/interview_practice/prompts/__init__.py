"""Prompt techniques, personas and the public prompt-construction facade."""

from interview_practice.prompts._lib.catalog import (
    DEFAULT_TECHNIQUE,
    TECHNIQUE_ORDER,
    technique_options,
)
from interview_practice.prompts._lib.library import PromptLibrary
from interview_practice.prompts._lib.personas import persona_options
from interview_practice.prompts.domains import (
    DEFAULT_DOMAIN,
    DOMAIN_PROFILES,
    DomainProfile,
    domain_options,
    get_domain,
)
from interview_practice.prompts.personas import (
    DEFAULT_PERSONA,
    PERSONA_ORDER,
    Persona,
)
from interview_practice.prompts.styles import (
    DEFAULT_STYLE,
    RESPONSE_STYLES,
    ResponseStyle,
    get_style,
    style_options,
)
from interview_practice.prompts.techniques import PROMPT_VERSION, Technique

__all__ = [
    "DEFAULT_DOMAIN",
    "DEFAULT_PERSONA",
    "DEFAULT_STYLE",
    "DEFAULT_TECHNIQUE",
    "DOMAIN_PROFILES",
    "DomainProfile",
    "RESPONSE_STYLES",
    "ResponseStyle",
    "PERSONA_ORDER",
    "PROMPT_VERSION",
    "Persona",
    "PromptLibrary",
    "TECHNIQUE_ORDER",
    "Technique",
    "domain_options",
    "get_domain",
    "get_style",
    "persona_options",
    "style_options",
    "technique_options",
]
