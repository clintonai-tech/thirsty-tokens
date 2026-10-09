from dataclasses import dataclass

from thirsty_tokens.footprint.coefficients import (
    EU_GRID_G_CO2E_PER_KWH,
    INPUT_TOKEN_ENERGY_RATIO,
    TIER_WH_PER_OUTPUT_TOKEN,
    WATER_L_PER_KWH,
)


@dataclass(frozen=True)
class Footprint:
    """Estimated footprint of one request."""

    energy_wh: float
    carbon_g: float
    water_l: float


def calculate(tier: str, input_tokens: int, output_tokens: int) -> Footprint:
    """Estimate energy, carbon and water for a request. Pure and deterministic."""
    if input_tokens < 0 or output_tokens < 0:
        raise ValueError("token counts must be non-negative")
    try:
        wh_per_output = TIER_WH_PER_OUTPUT_TOKEN[tier]
    except KeyError:
        raise ValueError(f"unknown tier: {tier!r}") from None

    energy_wh = wh_per_output * (output_tokens + INPUT_TOKEN_ENERGY_RATIO * input_tokens)
    kwh = energy_wh / 1000
    return Footprint(
        energy_wh=energy_wh,
        carbon_g=kwh * EU_GRID_G_CO2E_PER_KWH,
        water_l=kwh * WATER_L_PER_KWH,
    )
