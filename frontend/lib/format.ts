function trim(n: number, digits: number): string {
  const fixed = n.toFixed(digits);
  return fixed.includes(".") ? fixed.replace(/\.?0+$/, "") : fixed;
}

function sig(n: number): string {
  // two significant figures, never exponent notation
  if (n === 0) return "0";
  const digits = Math.max(0, 1 - Math.floor(Math.log10(Math.abs(n))));
  return trim(n, Math.min(digits, 12));
}

export function formatUsd(usd: number): string {
  if (usd === 0) return "$0";
  if (usd < 0.000001) return "<$0.000001";
  if (usd >= 0.01) return `$${usd.toFixed(2)}`;
  return `$${sig(usd)}`;
}

export function formatMs(ms: number): string {
  return ms >= 1000 ? `${trim(ms / 1000, 2)} s` : `${Math.round(ms)} ms`;
}

export function formatWater(liters: number): { value: string; unit: string } {
  if (liters >= 1) return { value: sig(liters), unit: "L" };
  const ml = liters * 1000;
  if (ml >= 0.01) return { value: sig(ml), unit: "mL" };
  return { value: sig(ml * 1000), unit: "µL" };
}

export function formatEnergy(wh: number): { value: string; unit: string } {
  if (wh >= 1) return { value: sig(wh), unit: "Wh" };
  if (wh >= 0.001) return { value: sig(wh * 1000), unit: "mWh" };
  return { value: sig(wh * 1_000_000), unit: "µWh" };
}

export function formatCarbon(grams: number): { value: string; unit: string } {
  if (grams >= 1) return { value: sig(grams), unit: "g CO₂e" };
  if (grams >= 0.001) return { value: sig(grams * 1000), unit: "mg CO₂e" };
  return { value: sig(grams * 1_000_000), unit: "µg CO₂e" };
}

/** Fill level 0..1 for the water glass: log scale from 0.01 mL (empty) to 10 mL (full). */
export function waterLevel(liters: number): number {
  if (liters <= 0) return 0;
  const level = (Math.log10(liters) + 5) / 3;
  return Math.min(1, Math.max(0.04, level));
}
