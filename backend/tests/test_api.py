from types import SimpleNamespace
from typing import Any

import pytest
from fastapi.testclient import TestClient

from thirsty_tokens import app as app_module
from thirsty_tokens.config import MAX_OUTPUT_TOKENS


@pytest.fixture
def client() -> TestClient:
    return TestClient(app_module.app)


@pytest.fixture
def mock_litellm(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    calls: dict[str, Any] = {}

    def fake_completion(**kwargs: Any) -> SimpleNamespace:
        calls.update(kwargs)
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="hello"))],
            usage=SimpleNamespace(prompt_tokens=12, completion_tokens=34),
        )

    monkeypatch.setattr(app_module.litellm, "completion", fake_completion)
    monkeypatch.setattr(app_module.litellm, "cost_per_token", lambda **_: (0.001, 0.00023))
    return calls


def test_health(client: TestClient) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_models_lists_registry(client: TestClient) -> None:
    r = client.get("/models")
    assert r.status_code == 200
    assert len(r.json()) == 5
    assert {"id", "display_name", "provider", "tier"} <= r.json()[0].keys()


def test_chat_maps_tokens_cost_and_latency(
    client: TestClient, mock_litellm: dict[str, Any]
) -> None:
    r = client.post("/chat", json={"model": "nova-micro", "prompt": "hi"})
    assert r.status_code == 200
    body = r.json()
    assert body["text"] == "hello"
    assert body["input_tokens"] == 12
    assert body["output_tokens"] == 34
    assert body["cost_usd"] == pytest.approx(0.00123)
    assert body["latency_ms"] >= 0
    assert mock_litellm["model"] == "bedrock/eu.amazon.nova-micro-v1:0"
    assert mock_litellm["aws_region_name"] == "eu-north-1"


def test_chat_enforces_max_output_tokens_even_if_client_sends_more(
    client: TestClient, mock_litellm: dict[str, Any]
) -> None:
    r = client.post("/chat", json={"model": "nova-micro", "prompt": "hi", "max_tokens": 100000})
    assert r.status_code == 200
    assert mock_litellm["max_tokens"] == MAX_OUTPUT_TOKENS == 500


def test_chat_unknown_model_404(client: TestClient, mock_litellm: dict[str, Any]) -> None:
    r = client.post("/chat", json={"model": "gpt-9", "prompt": "hi"})
    assert r.status_code == 404
    assert mock_litellm == {}


def test_chat_prompt_too_long_422(client: TestClient, mock_litellm: dict[str, Any]) -> None:
    r = client.post("/chat", json={"model": "nova-micro", "prompt": "x" * 2001})
    assert r.status_code == 422
    assert mock_litellm == {}


def test_chat_empty_prompt_422(client: TestClient, mock_litellm: dict[str, Any]) -> None:
    r = client.post("/chat", json={"model": "nova-micro", "prompt": ""})
    assert r.status_code == 422


def test_chat_uses_pricing_override_when_present(
    client: TestClient, mock_litellm: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    from thirsty_tokens.registry import ModelInfo, Pricing, Registry

    override = Registry(
        [
            ModelInfo(
                id="x",
                display_name="X",
                provider="p",
                tier="small",
                litellm_model="bedrock/x",
                pricing=Pricing(input_per_million_usd=1.0, output_per_million_usd=2.0),
            )
        ]
    )
    app_module.app.dependency_overrides[app_module.get_registry] = lambda: override
    try:
        r = client.post("/chat", json={"model": "x", "prompt": "hi"})
    finally:
        app_module.app.dependency_overrides.clear()
    assert r.json()["cost_usd"] == pytest.approx((12 * 1.0 + 34 * 2.0) / 1_000_000)
