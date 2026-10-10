"""Footprint coefficients. Every value is an ESTIMATE, not a measurement.

Closed models do not publish their size or hardware, so energy is assigned per tier
(small / medium / large) from public benchmarks. Retrieved 2026-10-09.
"""

from typing import Final

# Energy per OUTPUT token, in Wh. Includes server and data-center overhead.
# Anchors:
# - Epoch AI, "How much energy does ChatGPT use?": ~0.3 Wh for ~500 output tokens on a
#   ~100B-active-parameter model => ~0.0006 Wh/token. (medium)
#   https://epoch.ai/gradient-updates/how-much-energy-does-chatgpt-use
# - "How Hungry is AI?" (arXiv 2505.09598v6), Table 4, 100 in / 300 out tokens:
#   Llama-3.1-8B 0.052 Wh => ~0.00017 Wh/token (small); Llama-3.3-70B 0.237 Wh => ~0.0008
#   (medium); Claude-3.7 Sonnet 0.950 Wh => ~0.0032 (large, upper end).
#   https://arxiv.org/abs/2505.09598
# Choices: small ~ 8B-class, medium ~ Epoch/70B-class, large between Epoch and the Claude figure.
TIER_WH_PER_OUTPUT_TOKEN: Final[dict[str, float]] = {
    "small": 0.0002,
    "medium": 0.0006,
    "large": 0.0015,
}

# Input (prefill) tokens cost less than output tokens: they are processed in parallel.
# Epoch AI treats input as negligible for short prompts (our limit is 2,000 characters).
# The 0.1 ratio is an assumption, not a published figure.
INPUT_TOKEN_ENERGY_RATIO: Final[float] = 0.1

# EU-27 average electricity carbon intensity, 2024: 211.2 gCO2e/kWh (Ember data via Our World
# in Data). EU average rather than Sweden's, because EU inference profiles may route across
# regions. EEA reports the same trend: 2024 intensity was 11% below 2023.
# https://ourworldindata.org/grapher/carbon-intensity-electricity
# https://www.eea.europa.eu/en/analysis/indicators/greenhouse-gas-emission-intensity-of-1
EU_GRID_G_CO2E_PER_KWH: Final[float] = 211.2

# Water per kWh of IT energy = on-site cooling + off-site (electricity generation).
# Both from "How Hungry is AI?" Table 1, AWS multipliers (PUE 1.14 is already inside the Wh
# figures above). The off-site value is a US-weighted average and likely overstates the EU,
# so treat water as an upper-leaning estimate. AWS reports a lower on-site WUE (0.12 L/kWh
# in its 2026 fact sheets, https://sustainability.aboutamazon.com/aws-sustainability-fact-sheets).
WATER_ON_SITE_L_PER_KWH: Final[float] = 0.18
WATER_OFF_SITE_L_PER_KWH: Final[float] = 5.11
WATER_L_PER_KWH: Final[float] = WATER_ON_SITE_L_PER_KWH + WATER_OFF_SITE_L_PER_KWH
