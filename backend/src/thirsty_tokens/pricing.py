from thirsty_tokens.registry import Pricing


def cost_usd(input_tokens: int, output_tokens: int, pricing: Pricing) -> float:
    """Cost in USD from token counts and per-million-token prices."""
    return (
        input_tokens * pricing.input_per_million_usd
        + output_tokens * pricing.output_per_million_usd
    ) / 1_000_000
