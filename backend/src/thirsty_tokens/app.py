import logging
import time
from functools import lru_cache
from pathlib import Path
from typing import Annotated

import litellm
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

from thirsty_tokens.config import MAX_OUTPUT_TOKENS, Settings
from thirsty_tokens.errors import map_llm_error
from thirsty_tokens.pricing import cost_usd
from thirsty_tokens.registry import ModelInfo, Registry

logger = logging.getLogger(__name__)


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


@lru_cache
def get_settings() -> Settings:
    return Settings()


def get_registry(settings: Annotated[Settings, Depends(get_settings)]) -> Registry:
    return _load_registry(str(settings.models_path))


@lru_cache
def _load_registry(path: str) -> Registry:
    return Registry.from_yaml(Path(path))


app = FastAPI(title="thirsty-tokens")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/models")
def models(registry: Annotated[Registry, Depends(get_registry)]) -> list[ModelInfo]:
    return registry.list()


@app.post("/chat")
def chat(
    req: ChatRequest,
    settings: Annotated[Settings, Depends(get_settings)],
    registry: Annotated[Registry, Depends(get_registry)],
) -> ChatResponse:
    info = registry.get(req.model)
    if info is None:
        raise HTTPException(status_code=404, detail=f"unknown model: {req.model}")
    if len(req.prompt) > settings.max_input_chars:
        raise HTTPException(
            status_code=422, detail=f"prompt exceeds {settings.max_input_chars} characters"
        )

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
        if info.pricing is not None:
            cost = cost_usd(usage.prompt_tokens, usage.completion_tokens, info.pricing)
        else:
            cost = float(
                litellm.completion_cost(completion_response=response, model=info.litellm_model)
            )
    except Exception as exc:
        # Full detail stays in the server log; the client gets a safe, mapped message.
        logger.warning("chat failed: model=%s error=%s", info.id, type(exc).__name__, exc_info=True)
        status, message = map_llm_error(exc)
        raise HTTPException(status_code=status, detail=message) from exc

    return ChatResponse(
        model=info.id,
        text=response.choices[0].message.content or "",
        input_tokens=usage.prompt_tokens,
        output_tokens=usage.completion_tokens,
        cost_usd=cost,
        latency_ms=latency_ms,
    )
