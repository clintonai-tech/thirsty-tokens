import itertools
import json
import logging
import math
import time
from collections.abc import Iterator
from functools import lru_cache
from pathlib import Path
from typing import Annotated, Any

import boto3
import litellm
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from thirsty_tokens.config import MAX_OUTPUT_TOKENS, Settings
from thirsty_tokens.equivalents import Equivalent, equivalents
from thirsty_tokens.errors import map_llm_error
from thirsty_tokens.footprint import Footprint, calculate
from thirsty_tokens.limits import LimitExceeded, LimitsRepository, usd_to_micro
from thirsty_tokens.pricing import estimate_cost
from thirsty_tokens.registry import ModelInfo, Registry
from thirsty_tokens.sse import sse_event

logger = logging.getLogger(__name__)

LIMIT_MESSAGES = {
    "daily_budget": "Today's budget for this demo is used up. Please come back tomorrow (UTC).",
    "rate_limit": "You have reached today's request limit for this demo. Try again tomorrow.",
}


class ChatRequest(BaseModel):
    model: str
    prompt: str = Field(min_length=1)


class ChatResponse(BaseModel):
    model: str
    text: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    latency_ms: int
    footprint: Footprint
    equivalents: list[Equivalent]


@lru_cache
def get_settings() -> Settings:
    return Settings()


def get_registry(settings: Annotated[Settings, Depends(get_settings)]) -> Registry:
    return _load_registry(str(settings.models_path))


@lru_cache
def _load_registry(path: str) -> Registry:
    return Registry.from_yaml(Path(path))


@lru_cache
def _limits_for(table_name: str, region: str) -> LimitsRepository:
    table = boto3.resource("dynamodb", region_name=region).Table(table_name)
    return LimitsRepository(table)


def get_limits(settings: Annotated[Settings, Depends(get_settings)]) -> LimitsRepository | None:
    """None when no table is configured (local dev); production always sets TT_TABLE_NAME."""
    if settings.table_name is None:
        return None
    return _limits_for(settings.table_name, settings.aws_region)


app = FastAPI(title="thirsty-tokens")


@app.exception_handler(LimitExceeded)
def limit_exceeded_handler(_: Request, exc: LimitExceeded) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={"detail": LIMIT_MESSAGES[exc.reason], "reason": exc.reason},
        headers={"Retry-After": str(exc.retry_after)},
    )


def client_ip(request: Request) -> str:
    """Caller IP from the function URL request context (set by Lambda Web Adapter).

    Never from X-Forwarded-For or other client-controlled headers.
    """
    raw = request.headers.get("x-amzn-request-context")
    if raw:
        try:
            ip = json.loads(raw)["http"]["sourceIp"]
            if isinstance(ip, str) and ip:
                return ip
        except (ValueError, KeyError, TypeError):
            logger.warning("unparseable x-amzn-request-context")
    return request.client.host if request.client else "unknown"


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/models")
def models(registry: Annotated[Registry, Depends(get_registry)]) -> list[ModelInfo]:
    return registry.list()


def _admit(
    req: ChatRequest,
    request: Request,
    settings: Settings,
    registry: Registry,
    limits: LimitsRepository | None,
) -> tuple[ModelInfo, int]:
    """Validate, apply the IP rate limit, reserve worst-case spend. Returns (model, reserved)."""
    info = registry.get(req.model)
    if info is None:
        raise HTTPException(status_code=404, detail=f"unknown model: {req.model}")
    if len(req.prompt) > settings.max_input_chars:
        raise HTTPException(
            status_code=422, detail=f"prompt exceeds {settings.max_input_chars} characters"
        )
    if limits is None:
        return info, 0
    limits.hit_rate_limit(client_ip(request), settings.daily_request_limit)
    # Upper bound on input tokens: one token per UTF-8 byte (no tokenizer needed).
    worst = estimate_cost(info, len(req.prompt.encode()), MAX_OUTPUT_TOKENS)
    reserved = usd_to_micro(worst, round_up=True)
    limits.reserve_spend(reserved, usd_to_micro(settings.daily_spend_cap_usd))
    return info, reserved


def _settle(limits: LimitsRepository | None, reserved: int, actual: int) -> None:
    """Reconcile the reservation with what was really spent; never raises."""
    if limits is None or actual == reserved:
        return
    try:
        limits.settle_spend(actual - reserved)
    except Exception:
        logger.exception("failed to settle spend: reserved=%s actual=%s", reserved, actual)


def _metrics(
    info: ModelInfo, input_tokens: int, output_tokens: int
) -> tuple[float, Footprint, list[Equivalent]]:
    footprint = calculate(info.tier, input_tokens, output_tokens)
    return estimate_cost(info, input_tokens, output_tokens), footprint, equivalents(footprint)


@app.post("/chat")
def chat(
    req: ChatRequest,
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
    registry: Annotated[Registry, Depends(get_registry)],
    limits: Annotated[LimitsRepository | None, Depends(get_limits)],
) -> ChatResponse:
    info, reserved = _admit(req, request, settings, registry, limits)

    start = time.perf_counter()
    try:
        response = litellm.completion(
            model=info.litellm_model,
            messages=[{"role": "user", "content": req.prompt}],
            max_tokens=MAX_OUTPUT_TOKENS,
            aws_region_name=settings.aws_region,
        )
        latency_ms = round((time.perf_counter() - start) * 1000)
        usage = response.usage
        cost, footprint, eq = _metrics(info, usage.prompt_tokens, usage.completion_tokens)
    except Exception as exc:
        # Full detail stays in the server log; the client gets a safe, mapped message.
        logger.warning("chat failed: model=%s error=%s", info.id, type(exc).__name__, exc_info=True)
        _settle(limits, reserved, 0)
        status, message = map_llm_error(exc)
        raise HTTPException(status_code=status, detail=message) from exc

    _settle(limits, reserved, usd_to_micro(cost))
    return ChatResponse(
        model=info.id,
        text=response.choices[0].message.content or "",
        input_tokens=usage.prompt_tokens,
        output_tokens=usage.completion_tokens,
        cost_usd=cost,
        latency_ms=latency_ms,
        footprint=footprint,
        equivalents=eq,
    )


def _count_tokens(info: ModelInfo, text: str) -> int:
    try:
        return int(litellm.token_counter(model=info.litellm_model, text=text))
    except Exception:
        return math.ceil(len(text) / 4)


@app.post("/chat/stream")
def chat_stream(
    req: ChatRequest,
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
    registry: Annotated[Registry, Depends(get_registry)],
    limits: Annotated[LimitsRepository | None, Depends(get_limits)],
) -> StreamingResponse:
    info, reserved = _admit(req, request, settings, registry, limits)

    start = time.perf_counter()
    # Open the stream and read the first chunk before responding, so provider failures
    # still produce a real HTTP status instead of a 200 with an error event.
    try:
        chunks = iter(
            litellm.completion(
                model=info.litellm_model,
                messages=[{"role": "user", "content": req.prompt}],
                max_tokens=MAX_OUTPUT_TOKENS,
                aws_region_name=settings.aws_region,
                stream=True,
                stream_options={"include_usage": True},
            )
        )
        first = next(chunks, None)
    except Exception as exc:
        logger.warning(
            "chat stream failed: model=%s error=%s", info.id, type(exc).__name__, exc_info=True
        )
        _settle(limits, reserved, 0)
        status, message = map_llm_error(exc)
        raise HTTPException(status_code=status, detail=message) from exc

    rest = chunks if first is None else itertools.chain([first], chunks)
    events = _stream_events(info, req.prompt, rest, start, limits, reserved)
    return StreamingResponse(
        events,
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def _stream_events(
    info: ModelInfo,
    prompt: str,
    chunks: Iterator[Any],
    start: float,
    limits: LimitsRepository | None,
    reserved: int,
) -> Iterator[str]:
    parts: list[str] = []
    ttft_s: float | None = None
    usage: Any = None
    actual_micro: int | None = None
    try:
        for chunk in chunks:
            if chunk.choices:
                delta = chunk.choices[0].delta.content
                if delta:
                    if ttft_s is None:
                        ttft_s = time.perf_counter() - start
                    parts.append(delta)
                    yield sse_event("token", {"text": delta})
            if getattr(chunk, "usage", None):
                usage = chunk.usage

        latency_s = time.perf_counter() - start
        text = "".join(parts)
        if usage is not None:
            input_tokens, output_tokens = usage.prompt_tokens, usage.completion_tokens
        else:  # provider sent no usage: estimate, never report zero for a real answer
            input_tokens, output_tokens = _count_tokens(info, prompt), _count_tokens(info, text)
        cost, footprint, eq = _metrics(info, input_tokens, output_tokens)
        actual_micro = usd_to_micro(cost)

        ttft = ttft_s if ttft_s is not None else latency_s
        generation_s = latency_s - ttft if latency_s - ttft > 0 else latency_s
        yield sse_event(
            "done",
            {
                "model": info.id,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost_usd": cost,
                "latency_ms": round(latency_s * 1000),
                "ttft_ms": round(ttft * 1000),
                "tokens_per_sec": round(output_tokens / generation_s, 1) if generation_s else 0.0,
                "footprint": footprint.__dict__,
                "equivalents": [e.model_dump() for e in eq],
            },
        )
    except Exception as exc:
        logger.warning(
            "chat stream failed mid-way: model=%s error=%s",
            info.id,
            type(exc).__name__,
            exc_info=True,
        )
        _, message = map_llm_error(exc)
        yield sse_event("error", {"detail": message})
    finally:
        if actual_micro is None:
            # Aborted or failed: refund if nothing was generated, else keep the reservation
            # (usage unknown, so stay on the safe side of the cap).
            actual_micro = reserved if parts else 0
        _settle(limits, reserved, actual_micro)
