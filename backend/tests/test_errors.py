from typing import Any

import httpx
import pytest
from fastapi.testclient import TestClient
from litellm import exceptions as llm_exc

from thirsty_tokens import app as app_module
from thirsty_tokens.errors import map_llm_error

SECRET = "arn:aws:bedrock:eu-north-1:123456789012:secret-detail"


def _resp(status: int) -> httpx.Response:
    return httpx.Response(status, request=httpx.Request("POST", "https://example.invalid"))


CASES: list[tuple[Exception, int]] = [
    (llm_exc.RateLimitError(SECRET, "bedrock", "m", _resp(429)), 429),
    (llm_exc.Timeout(SECRET, "m", "bedrock"), 504),
    (llm_exc.ContentPolicyViolationError(SECRET, "m", "bedrock", _resp(400)), 422),
    (llm_exc.BadRequestError(SECRET, "m", "bedrock", _resp(400)), 502),
    (llm_exc.NotFoundError(SECRET, "m", "bedrock", _resp(404)), 502),
    (llm_exc.AuthenticationError(SECRET, "bedrock", "m", _resp(401)), 502),
    (llm_exc.ServiceUnavailableError(SECRET, "bedrock", "m", _resp(503)), 502),
    (RuntimeError(SECRET), 502),
]


@pytest.mark.parametrize(("exc", "status"), CASES)
def test_map_llm_error_status_and_no_leak(exc: Exception, status: int) -> None:
    code, message = map_llm_error(exc)
    assert code == status
    assert SECRET not in message


@pytest.mark.parametrize(("exc", "status"), CASES)
def test_chat_returns_clean_error_instead_of_500(
    exc: Exception, status: int, monkeypatch: pytest.MonkeyPatch
) -> None:
    def boom(**_: Any) -> None:
        raise exc

    monkeypatch.setattr(app_module.litellm, "completion", boom)
    r = TestClient(app_module.app).post("/chat", json={"model": "nova-micro", "prompt": "hi"})
    assert r.status_code == status
    assert set(r.json()) == {"detail"}
    assert SECRET not in r.text


def test_chat_logs_error_detail_server_side(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    def boom(**_: Any) -> None:
        raise llm_exc.NotFoundError(SECRET, "m", "bedrock", _resp(404))

    monkeypatch.setattr(app_module.litellm, "completion", boom)
    TestClient(app_module.app).post("/chat", json={"model": "nova-micro", "prompt": "hi"})
    assert "NotFoundError" in caplog.text
    assert "model=nova-micro" in caplog.text
