import { formatCarbon, formatEnergy, formatUsd, formatWater, waterLevel } from "@/lib/format";

describe("format", () => {
  it("formats tiny dollar amounts without exponents", () => {
    expect(formatUsd(0.00041)).toBe("$0.00041");
    expect(formatUsd(0.0000123)).toBe("$0.000012");
    expect(formatUsd(0.5)).toBe("$0.50");
    expect(formatUsd(0)).toBe("$0");
  });

  it("picks readable units", () => {
    expect(formatWater(0.0008)).toEqual({ value: "0.8", unit: "mL" });
    expect(formatWater(0.000002)).toEqual({ value: "2", unit: "µL" });
    expect(formatEnergy(0.15)).toEqual({ value: "150", unit: "mWh" });
    expect(formatCarbon(0.03)).toEqual({ value: "30", unit: "mg CO₂e" });
  });

  it("keeps the glass level within bounds", () => {
    expect(waterLevel(0)).toBe(0);
    expect(waterLevel(1e-9)).toBeCloseTo(0.04);
    expect(waterLevel(5)).toBe(1);
  });
});
