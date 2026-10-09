from pathlib import Path

import pytest

from thirsty_tokens.config import DEFAULT_MODELS_PATH
from thirsty_tokens.registry import ModelInfo, Registry


def test_loads_five_models_with_expected_tiers() -> None:
    registry = Registry.from_yaml(DEFAULT_MODELS_PATH)
    tiers = [m.tier for m in registry.list()]
    assert len(tiers) == 5
    assert sorted(tiers) == ["large", "medium", "medium", "small", "small"]


def test_all_models_use_eu_bedrock_profiles() -> None:
    for m in Registry.from_yaml(DEFAULT_MODELS_PATH).list():
        assert m.litellm_model.startswith("bedrock/eu.")


def test_get_unknown_returns_none() -> None:
    assert Registry.from_yaml(DEFAULT_MODELS_PATH).get("nope") is None


def test_duplicate_ids_rejected() -> None:
    m = ModelInfo(id="a", display_name="A", provider="p", tier="small", litellm_model="x")
    with pytest.raises(ValueError):
        Registry([m, m])


def test_invalid_tier_rejected(tmp_path: Path) -> None:
    f = tmp_path / "m.yaml"
    f.write_text(
        "models:\n  - {id: a, display_name: A, provider: p, tier: huge, litellm_model: x}\n"
    )
    with pytest.raises(ValueError):
        Registry.from_yaml(f)
