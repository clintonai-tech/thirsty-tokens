# ADR-0008: Footprint estimation by model tier

- Status: accepted
- Date: 2026-10-09

## Context
We want energy, carbon and water per request. Closed models (Nova, Claude) do not publish parameter counts, hardware or measured energy, and Bedrock gives no per-request energy data. Any number we show is an estimate.

## Decision
Pure, deterministic functions (no LLMs), with every constant in `footprint/coefficients.py` next to its source and retrieval date (2026-10-09):
- **Energy** = Wh per output token by tier (small 0.0002, medium 0.0006, large 0.0015) x (output tokens + 0.1 x input tokens). Anchored on Epoch AI (~0.3 Wh for 500 output tokens, ~0.0006 Wh/token) and "How Hungry is AI?" (arXiv 2505.09598): Llama-3.1-8B ~0.00017, Llama-3.3-70B ~0.0008, Claude-3.7 Sonnet ~0.0032 Wh/token. The 0.1 input ratio is an assumption.
- **Carbon** = kWh x 211.2 gCO2e/kWh, the EU-27 average for 2024 (Ember via Our World in Data). EU rather than Sweden because EU inference profiles can route across regions.
- **Water** = kWh x 5.29 L/kWh = on-site 0.18 + off-site 5.11, from the AWS multipliers in arXiv 2505.09598 (PUE 1.14 is included in the energy anchors).
- Unknown tier or negative tokens raise `ValueError`; zero tokens give zero.
- The UI and API label all figures as estimates.

## Consequences
- Models in the same tier get the same footprint per token; differences in the chart come from token counts, not model-specific energy. This is stated on the methodology page.
- The off-site water factor is US-weighted and probably too high for the EU, and AWS reports lower on-site WUE (0.12 L/kWh). Water is therefore an upper-leaning estimate.
- Coefficients span roughly 2x either way. Uncertainty ranges are out of scope (PLAN.md).
- Revisit when providers publish measured per-model energy.
