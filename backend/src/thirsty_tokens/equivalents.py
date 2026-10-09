"""Relatable equivalents for a footprint. Pure and deterministic; no LLMs involved.

All reference values are round, typical figures (approximate, not precise measurements).
"""

import math
from typing import Final

from pydantic import BaseModel

from thirsty_tokens.footprint import Footprint

CONSTANTS: Final[dict[str, float]] = {
    # Typical smartphone battery, ~13 Wh (e.g. iPhone 15: 12.98 Wh). Retrieved 2026-10-09.
    "phone_charge_wh": 13.0,
    # Energy of one Google search, ~0.3 Wh. Google, "Powering a Google search" (2009), still
    # the most-cited figure; Google reported 0.24 Wh for a median Gemini prompt in 2025.
    # https://googleblog.blogspot.com/2009/01/powering-google-search.html
    "google_search_wh": 0.3,
    # A typical EU electric kettle draws about 2 kW, i.e. 2000 J per second.
    "kettle_power_w": 2000.0,
    # One sip of water, ~20 mL (commonly cited range 15-25 mL).
    "sip_l": 0.02,
    # One drop of water, ~0.05 mL (IEC/medical standard drop).
    "drop_l": 0.00005,
}

_SECONDS_PER_WH_KETTLE: Final[float] = 3600 / CONSTANTS["kettle_power_w"]


class Equivalent(BaseModel):
    kind: str
    value: float
    unit: str
    label: str


def _round_sig(x: float, sig: int = 2) -> float:
    if x == 0:
        return 0.0
    return round(x, sig - 1 - math.floor(math.log10(abs(x))))


def _fmt(x: float) -> str:
    return f"{x:,.0f}" if x >= 100 else f"{x:g}"


def _make(kind: str, value: float, unit: str) -> Equivalent:
    v = _round_sig(value)
    return Equivalent(kind=kind, value=v, unit=unit, label=f"{_fmt(v)} {unit}")


def _phone(energy_wh: float) -> Equivalent:
    charges = energy_wh / CONSTANTS["phone_charge_wh"]
    if charges < 1:
        return _make("phone_charges", charges * 100, "% of a phone charge")
    return _make("phone_charges", charges, "phone charges")


def _searches(energy_wh: float) -> Equivalent:
    return _make("google_searches", energy_wh / CONSTANTS["google_search_wh"], "Google searches")


def _kettle(energy_wh: float) -> Equivalent:
    seconds = energy_wh * _SECONDS_PER_WH_KETTLE
    if seconds < 1:
        return _make("kettle_seconds", seconds * 1000, "milliseconds of boiling a kettle")
    if seconds < 120:
        return _make("kettle_seconds", seconds, "seconds of boiling a kettle")
    if seconds < 7200:
        return _make("kettle_seconds", seconds / 60, "minutes of boiling a kettle")
    return _make("kettle_seconds", seconds / 3600, "hours of boiling a kettle")


def _sips(water_l: float) -> Equivalent:
    sips = water_l / CONSTANTS["sip_l"]
    if sips < 1:
        return _make("water_sips", water_l / CONSTANTS["drop_l"], "drops of water")
    return _make("water_sips", sips, "sips of water")


def equivalents(footprint: Footprint) -> list[Equivalent]:
    """Phone charges, Google searches, kettle time and sips of water, each in a readable unit."""
    return [
        _phone(footprint.energy_wh),
        _searches(footprint.energy_wh),
        _kettle(footprint.energy_wh),
        _sips(footprint.water_l),
    ]
