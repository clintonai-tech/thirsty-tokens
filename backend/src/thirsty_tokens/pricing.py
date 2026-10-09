import litellm

from thirsty_tokens.registry import ModelInfo, Pricing


def cost_usd(input_tokens: int, output_tokens: int, pricing: Pricing) -> float:
    """Cost in USD from token counts and per-million-token prices."""
    return (
        input_tokens * pricing.input_per_million_usd
        + output_tokens * pricing.output_per_million_usd
    ) / 1_000_000


def estimate_cost(info: ModelInfo, input_tokens: int, output_tokens: int) -> float:
    """Cost for a model: the `models.yaml` override if present, else LiteLLM's cost map."""
    if info.pricing is not None:
        return cost_usd(input_tokens, output_tokens, info.pricing)
    prompt_cost, completion_cost = litellm.cost_per_token(
        model=info.litellm_model,
        prompt_tokens=input_tokens,
        completion_tokens=output_tokens,
    )
    return float(prompt_cost + completion_cost)
