export interface ModelInfo {
  id: string;
  display_name: string;
  provider: string;
  tier: "small" | "medium" | "large";
}

export interface Footprint {
  energy_wh: number;
  carbon_g: number;
  water_l: number;
}

export interface Equivalent {
  kind: string;
  value: number;
  unit: string;
  label: string;
}

export interface ChatResult {
  model: string;
  input_tokens: number;
  output_tokens: number;
  cost_usd: number;
  latency_ms: number;
  ttft_ms: number;
  tokens_per_sec: number;
  footprint: Footprint;
  equivalents: Equivalent[];
}
