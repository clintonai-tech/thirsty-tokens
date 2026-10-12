import { waterLevel } from "@/lib/format";

interface Props {
  /** Liters of water for the answer; undefined shows an empty glass. */
  liters?: number;
  className?: string;
}

const W = 120;
const H = 160;

/** A tapered glass. The fill height is decorative (log scale); the numbers carry the data. */
export function WaterGlass({ liters, className }: Props) {
  const level = liters === undefined ? 0 : waterLevel(liters);
  const top = H - 8 - level * (H - 20);
  const glass = "M16 8 H104 L94 150 Q93 154 88 154 H32 Q27 154 26 150 Z";

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className={className} role="presentation" aria-hidden>
      <defs>
        <clipPath id="glass-clip">
          <path d={glass} />
        </clipPath>
        <linearGradient id="water-fill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="var(--water-top)" />
          <stop offset="1" stopColor="var(--water-deep)" />
        </linearGradient>
      </defs>
      <g clipPath="url(#glass-clip)">
        {liters !== undefined && (
          <g className="water-rise" style={{ ["--from" as string]: `${H - top}px` }}>
            <g transform={`translate(0 ${top})`}>
              <g className="water-wave">
                <path
                  d="M0 4 Q15 -2 30 4 T60 4 T90 4 T120 4 T150 4 T180 4 T210 4 T240 4 V200 H0 Z"
                  fill="url(#water-fill)"
                />
              </g>
            </g>
          </g>
        )}
      </g>
      <path d={glass} fill="none" stroke="var(--glass)" strokeWidth="3" strokeLinejoin="round" />
    </svg>
  );
}
