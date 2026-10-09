import pytest

from thirsty_tokens.equivalents import equivalents
from thirsty_tokens.footprint import Footprint


def _by_kind(wh: float, litres: float) -> dict[str, tuple[float, str]]:
    return {
        e.kind: (e.value, e.unit)
        for e in equivalents(Footprint(energy_wh=wh, carbon_g=0, water_l=litres))
    }


def test_fixed_values_for_one_phone_charge() -> None:
    eq = _by_kind(13.0, 0.2)
    assert eq["phone_charges"] == (1.0, "phone charges")
    assert eq["google_searches"] == (43.0, "Google searches")  # 13 / 0.3 = 43.33
    assert eq["kettle_seconds"] == (23.0, "seconds of boiling a kettle")  # 13 * 1.8 = 23.4
    assert eq["water_sips"] == (10.0, "sips of water")


def test_zero_footprint() -> None:
    eq = _by_kind(0, 0)
    assert eq["phone_charges"] == (0.0, "% of a phone charge")
    assert eq["kettle_seconds"] == (0.0, "milliseconds of boiling a kettle")
    assert eq["water_sips"] == (0.0, "drops of water")


def test_typical_small_query_uses_small_units() -> None:
    eq = _by_kind(0.186, 0.000984)  # ~medium model, 100 in / 300 out
    assert eq["phone_charges"] == (1.4, "% of a phone charge")
    assert eq["kettle_seconds"] == (330.0, "milliseconds of boiling a kettle")  # 0.3348 s
    assert eq["water_sips"] == (20.0, "drops of water")


@pytest.mark.parametrize(
    ("wh", "unit"),
    [
        (0.2, "milliseconds of boiling a kettle"),  # 0.36 s
        (0.6, "seconds of boiling a kettle"),  # 1.08 s
        (66.0, "seconds of boiling a kettle"),  # 118.8 s
        (67.0, "minutes of boiling a kettle"),  # 120.6 s
        (4000.0, "hours of boiling a kettle"),  # 7200 s
    ],
)
def test_kettle_unit_switches_with_magnitude(wh: float, unit: str) -> None:
    assert _by_kind(wh, 0)["kettle_seconds"][1] == unit


def test_deterministic() -> None:
    fp = Footprint(energy_wh=0.42, carbon_g=0.1, water_l=0.003)
    assert equivalents(fp) == equivalents(fp)


def test_labels_are_human_readable() -> None:
    labels = [e.label for e in equivalents(Footprint(energy_wh=1234.0, carbon_g=0, water_l=5.0))]
    assert labels[0] == "95 phone charges"
    assert labels[1] == "4,100 Google searches"
    assert labels[3] == "250 sips of water"
