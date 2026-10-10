import pytest

from thirsty_tokens.footprint import calculate


def test_medium_tier_fixed_values() -> None:
    # energy = 0.0006 * (300 + 0.1 * 100) = 0.186 Wh
    fp = calculate("medium", input_tokens=100, output_tokens=300)
    assert fp.energy_wh == pytest.approx(0.186)
    assert fp.carbon_g == pytest.approx(0.186 / 1000 * 211.2)  # 0.03928 g
    assert fp.water_l == pytest.approx(0.186 / 1000 * 5.29)  # 0.000984 L


@pytest.mark.parametrize(("tier", "wh"), [("small", 0.062), ("medium", 0.186), ("large", 0.465)])
def test_tiers_scale_energy(tier: str, wh: float) -> None:
    assert calculate(tier, 100, 300).energy_wh == pytest.approx(wh)


def test_zero_tokens_is_zero() -> None:
    fp = calculate("large", 0, 0)
    assert (fp.energy_wh, fp.carbon_g, fp.water_l) == (0, 0, 0)


def test_input_tokens_cost_less_than_output_tokens() -> None:
    assert calculate("small", 1000, 0).energy_wh < calculate("small", 0, 1000).energy_wh


def test_unknown_tier_raises() -> None:
    with pytest.raises(ValueError, match="unknown tier"):
        calculate("huge", 1, 1)


def test_negative_tokens_raise() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        calculate("small", -1, 0)
