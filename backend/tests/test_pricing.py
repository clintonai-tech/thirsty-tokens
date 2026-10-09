import pytest

from thirsty_tokens.pricing import cost_usd
from thirsty_tokens.registry import Pricing


def test_cost_from_per_million_prices() -> None:
    p = Pricing(input_per_million_usd=1.0, output_per_million_usd=5.0)
    assert cost_usd(1_000_000, 1_000_000, p) == pytest.approx(6.0)


def test_cost_small_request() -> None:
    p = Pricing(input_per_million_usd=3.0, output_per_million_usd=15.0)
    assert cost_usd(100, 200, p) == pytest.approx(0.0033)


def test_zero_tokens_cost_zero() -> None:
    p = Pricing(input_per_million_usd=3.0, output_per_million_usd=15.0)
    assert cost_usd(0, 0, p) == 0.0
