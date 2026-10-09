from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel


class Pricing(BaseModel):
    input_per_million_usd: float
    output_per_million_usd: float


class ModelInfo(BaseModel):
    id: str
    display_name: str
    provider: str
    tier: Literal["small", "medium", "large"]
    litellm_model: str
    pricing: Pricing | None = None


class Registry:
    def __init__(self, models: list[ModelInfo]) -> None:
        ids = [m.id for m in models]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate model id in registry")
        self._models = {m.id: m for m in models}

    @classmethod
    def from_yaml(cls, path: Path) -> "Registry":
        data = yaml.safe_load(path.read_text())
        return cls([ModelInfo.model_validate(m) for m in data["models"]])

    def list(self) -> list[ModelInfo]:
        return list(self._models.values())

    def get(self, model_id: str) -> ModelInfo | None:
        return self._models.get(model_id)
