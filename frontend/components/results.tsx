import { WaterGlass } from "@/components/water-glass";
import { formatCarbon, formatEnergy, formatMs, formatUsd, formatWater } from "@/lib/format";
import type { ChatResult } from "@/lib/types";

function Row({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <div className="flex items-baseline justify-between gap-4 border-b py-3 last:border-b-0">
      <dt className="text-sm text-muted-foreground">{label}</dt>
      <dd className="tabular text-right">
        <span className="font-display text-xl font-semibold">{value}</span>
        {hint && <span className="block text-xs text-muted-foreground">{hint}</span>}
      </dd>
    </div>
  );
}

export function Results({ result }: { result: ChatResult }) {
  const water = formatWater(result.footprint.water_l);
  const energy = formatEnergy(result.footprint.energy_wh);
  const carbon = formatCarbon(result.footprint.carbon_g);

  return (
    <section aria-labelledby="footprint-heading" className="space-y-6">
      <h2 id="footprint-heading" className="sr-only">
        Footprint of this answer
      </h2>

      <div className="flex items-center gap-6 rounded-xl border bg-card p-5 sm:p-6">
        <WaterGlass liters={result.footprint.water_l} className="h-36 w-28 shrink-0" />
        <div>
          <p className="text-sm text-muted-foreground">Water used, estimated</p>
          <p className="tabular font-display text-5xl font-bold leading-none text-tide sm:text-6xl">
            {water.value}
            <span className="ml-2 text-2xl font-semibold sm:text-3xl">{water.unit}</span>
          </p>
          <p className="mt-3 text-sm text-muted-foreground">
            Cooling and power generation for this one answer. The glass level is on a log scale.
          </p>
        </div>
      </div>

      <dl className="rounded-xl border bg-card px-5">
        <Row
          label="Tokens"
          value={(result.input_tokens + result.output_tokens).toLocaleString()}
          hint={`${result.input_tokens.toLocaleString()} in, ${result.output_tokens.toLocaleString()} out`}
        />
        <Row label="Cost" value={formatUsd(result.cost_usd)} />
        <Row label="First token" value={formatMs(result.ttft_ms)} />
        <Row
          label="Total time"
          value={formatMs(result.latency_ms)}
          hint={`${result.tokens_per_sec} tokens per second`}
        />
        <Row label="Energy" value={`${energy.value} ${energy.unit}`} />
        <Row label="Carbon" value={`${carbon.value} ${carbon.unit}`} />
      </dl>

      {result.equivalents.length > 0 && (
        <div>
          <h3 className="font-display text-lg font-semibold">About the same as</h3>
          <ul className="mt-2 space-y-1.5 text-muted-foreground">
            {result.equivalents.map((e) => (
              <li key={e.kind}>
                <span className="tabular font-semibold text-foreground">
                  {e.label.slice(0, e.label.length - e.unit.length).trim()}
                </span>{" "}
                {e.unit}
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}
