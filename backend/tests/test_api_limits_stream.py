import json
from collections.abc import Iterator
from types import SimpleNamespace
from typing import Any

import boto3
import pytest
from fastapi.testclient import TestClient
from moto import mock_aws

from thirsty_tokens import app as app_module
from thirsty_tokens.config import MAX_OUTPUT_TOKENS, Settings
from thirsty_tokens.limits import LimitsRepository


def _chunk(text: str | None = None, usage: tuple[int, int] | None = None) -> SimpleNamespace:
    choices = [SimpleNamespace(delta=SimpleNamespace(content=text))] if usage is None else []
    u = SimpleNamespace(prompt_tokens=usage[0], completion_tokens=usage[1]) if usage else None
    return SimpleNamespace(choices=choices, usage=u)


@pytest.fixture
def table() -> Iterator[Any]:
    with mock_aws():
        t = boto3.resource("dynamodb", region_name="eu-north-1").create_table(
            TableName="t",
            KeySchema=[
                {"AttributeName": "pk", "KeyType": "HASH"},
                {"AttributeName": "sk", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "pk", "AttributeType": "S"},
                {"AttributeName": "sk", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        yield t


@pytest.fixture
def limits(table: Any) -> LimitsRepository:
    return LimitsRepository(table)


def _client(limits: LimitsRepository | None, **settings: Any) -> TestClient:
    app_module.app.dependency_overrides[app_module.get_limits] = lambda: limits
    app_module.app.dependency_overrides[app_module.get_settings] = lambda: Settings(**settings)
    return TestClient(app_module.app)


@pytest.fixture(autouse=True)
def _clear_overrides() -> Iterator[None]:
    yield
    app_module.app.dependency_overrides.clear()


@pytest.fixture
def llm(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    state: dict[str, Any] = {"calls": [], "chunks": None, "error": None}

    def fake_completion(**kwargs: Any) -> Any:
        state["calls"].append(kwargs)
        if state["error"]:
            raise state["error"]
        if kwargs.get("stream"):
            return iter(state["chunks"] or [])
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="hello"))],
            usage=SimpleNamespace(prompt_tokens=12, completion_tokens=34),
        )

    monkeypatch.setattr(app_module.litellm, "completion", fake_completion)
    # $1 per input token and $2 per output token would blow any cap; use $/token = 1e-5 / 2e-5.
    monkeypatch.setattr(
        app_module.litellm,
        "cost_per_token",
        lambda **kw: (kw["prompt_tokens"] * 1e-5, kw["completion_tokens"] * 2e-5),
    )
    return state


def _events(body: str) -> list[tuple[str, dict[str, Any]]]:
    out = []
    for block in body.strip().split("\n\n"):
        event, data = block.split("\n")
        out.append((event.removeprefix("event: "), json.loads(data.removeprefix("data: "))))
    return out


def test_chat_includes_footprint_and_equivalents(limits: LimitsRepository, llm: Any) -> None:
    body = _client(limits).post("/chat", json={"model": "nova-pro", "prompt": "hi"}).json()
    assert body["footprint"]["energy_wh"] == pytest.approx(0.0006 * (34 + 0.1 * 12))
    assert [e["kind"] for e in body["equivalents"]] == [
        "phone_charges",
        "google_searches",
        "kettle_seconds",
        "water_sips",
    ]


def test_chat_settles_actual_cost(limits: LimitsRepository, llm: Any) -> None:
    _client(limits).post("/chat", json={"model": "nova-pro", "prompt": "hi"})
    assert limits.spent_micro() == round((12 * 1e-5 + 34 * 2e-5) * 1e6)  # 800


def test_budget_429_is_friendly_and_skips_llm(limits: LimitsRepository, llm: Any) -> None:
    client = _client(limits, daily_spend_cap_usd=0.0001)  # 100 micro-USD < worst case
    r = client.post("/chat", json={"model": "nova-pro", "prompt": "hi"})
    assert r.status_code == 429
    assert r.json()["reason"] == "daily_budget"
    assert "come back tomorrow" in r.json()["detail"]
    assert int(r.headers["retry-after"]) > 0
    assert llm["calls"] == []


def test_rate_limit_429_after_n_requests(limits: LimitsRepository, llm: Any) -> None:
    client = _client(limits, daily_request_limit=2)
    for _ in range(2):
        assert client.post("/chat", json={"model": "nova-pro", "prompt": "hi"}).status_code == 200
    r = client.post("/chat", json={"model": "nova-pro", "prompt": "hi"})
    assert r.status_code == 429
    assert r.json()["reason"] == "rate_limit"
    assert len(llm["calls"]) == 2


def test_ip_comes_from_request_context_not_forwarded_for(
    limits: LimitsRepository, llm: Any
) -> None:
    client = _client(limits, daily_request_limit=1)
    ctx = json.dumps({"http": {"sourceIp": "9.9.9.9"}})

    def post(forwarded: str) -> int:
        headers = {"x-amzn-request-context": ctx, "x-forwarded-for": forwarded}
        return client.post(
            "/chat", json={"model": "nova-pro", "prompt": "hi"}, headers=headers
        ).status_code

    assert post("1.1.1.1") == 200
    assert post("2.2.2.2") == 429  # spoofed X-Forwarded-For does not get a fresh quota


def test_failed_llm_call_refunds_reservation(limits: LimitsRepository, llm: Any) -> None:
    llm["error"] = RuntimeError("boom")
    r = _client(limits).post("/chat", json={"model": "nova-pro", "prompt": "hi"})
    assert r.status_code == 502
    assert limits.spent_micro() == 0


def test_validation_errors_do_not_consume_quota(limits: LimitsRepository, llm: Any) -> None:
    client = _client(limits, daily_request_limit=1)
    assert client.post("/chat", json={"model": "nope", "prompt": "hi"}).status_code == 404
    assert client.post("/chat", json={"model": "nova-pro", "prompt": "hi"}).status_code == 200


def test_stream_event_order_and_done_payload(limits: LimitsRepository, llm: Any) -> None:
    llm["chunks"] = [_chunk("Hel"), _chunk("lo"), _chunk(usage=(12, 34))]
    r = _client(limits).post("/chat/stream", json={"model": "nova-pro", "prompt": "hi"})
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/event-stream")
    events = _events(r.text)
    assert [e for e, _ in events] == ["token", "token", "done"]
    assert [d["text"] for e, d in events if e == "token"] == ["Hel", "lo"]
    done = events[-1][1]
    assert done["input_tokens"] == 12 and done["output_tokens"] == 34
    assert done["cost_usd"] == pytest.approx(12 * 1e-5 + 34 * 2e-5)
    assert {"latency_ms", "ttft_ms", "tokens_per_sec", "footprint", "equivalents"} <= done.keys()
    assert done["ttft_ms"] <= done["latency_ms"]
    assert len(done["equivalents"]) == 4
    call = llm["calls"][0]
    assert call["stream"] is True and call["max_tokens"] == MAX_OUTPUT_TOKENS
    assert limits.spent_micro() == 800


def test_stream_without_usage_falls_back_to_estimate(limits: LimitsRepository, llm: Any) -> None:
    llm["chunks"] = [_chunk("some answer text")]
    r = _client(limits).post("/chat/stream", json={"model": "nova-pro", "prompt": "hi"})
    done = _events(r.text)[-1][1]
    assert done["output_tokens"] > 0


def test_stream_429_is_plain_json_before_streaming(limits: LimitsRepository, llm: Any) -> None:
    r = _client(limits, daily_request_limit=0).post(
        "/chat/stream", json={"model": "nova-pro", "prompt": "hi"}
    )
    assert r.status_code == 429
    assert r.headers["content-type"].startswith("application/json")


def test_stream_provider_failure_before_first_chunk_is_http_error(
    limits: LimitsRepository, llm: Any
) -> None:
    llm["error"] = RuntimeError("boom")
    r = _client(limits).post("/chat/stream", json={"model": "nova-pro", "prompt": "hi"})
    assert r.status_code == 502
    assert limits.spent_micro() == 0


def test_stream_mid_stream_error_emits_event_and_keeps_reservation(
    limits: LimitsRepository, llm: Any
) -> None:
    def broken() -> Iterator[SimpleNamespace]:
        yield _chunk("partial")
        raise RuntimeError("connection reset")

    llm["chunks"] = broken()
    r = _client(limits).post("/chat/stream", json={"model": "nova-pro", "prompt": "hi"})
    events = _events(r.text)
    assert [e for e, _ in events] == ["token", "error"]
    assert "reset" not in events[-1][1]["detail"]  # no raw provider error to the client
    assert limits.spent_micro() > 0  # usage unknown after partial output: reservation kept


def test_no_table_configured_disables_limits(llm: Any) -> None:
    r = _client(None).post("/chat", json={"model": "nova-pro", "prompt": "hi"})
    assert r.status_code == 200
