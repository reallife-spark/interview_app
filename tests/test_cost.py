from interview_practice.cost import (
    ModelCatalog,
    ModelInfo,
    default_catalog,
    estimate_cost,
    format_usd,
)


def test_catalog_parses_per_token_prices() -> None:
    payload = {
        "data": [
            {
                "id": "openai/gpt-6-luna",
                "name": "Luna",
                "context_length": 128000,
                "pricing": {"prompt": "0.000001", "completion": "0.000002"},
                "supported_parameters": ["temperature", "max_tokens"],
            }
        ]
    }
    catalog = ModelCatalog.from_payload(payload)
    info = catalog.get("openai/gpt-6-luna")
    assert info is not None
    assert info.prompt_per_million == 1.0
    assert info.completion_per_million == 2.0
    assert info.context_length == 128000
    assert info.supported_parameters == ("temperature", "max_tokens")


def test_model_info_reports_supported_parameters() -> None:
    info = ModelInfo(
        id="x",
        supported_parameters=("response_format", "temperature"),
    )
    assert info.supports("response_format")
    assert info.supports_json_mode
    assert not info.supports("reasoning")


def test_estimate_cost_uses_prompt_and_completion() -> None:
    info = ModelInfo(
        id="x",
        prompt_per_million=1.0,
        completion_per_million=2.0,
    )
    assert estimate_cost(1_000_000, 500_000, info) == 2.0


def test_unknown_price_is_not_invented() -> None:
    assert estimate_cost(100, 100, None) is None
    assert estimate_cost(100, 100, ModelInfo(id="x")) is None
    assert format_usd(None) == "unavailable"


def test_default_catalog_contains_course_models_without_prices() -> None:
    catalog = default_catalog()
    models = catalog.for_course_models()
    assert len(models) == 3
    assert all(not model.has_price for model in models)
    assert format_usd(0.0) == "$0.00"
