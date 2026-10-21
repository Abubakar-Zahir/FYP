import type { ScoredHook } from "@/lib/api/types";
import { cn } from "@/lib/utils";

const STRONG_SCORE = 75;
const OKAY_SCORE = 60;
const RING_RADIUS = 22;
const RING_CIRCUMFERENCE = 2 * Math.PI * RING_RADIUS;

function scoreColor(score: number): string {
  if (score >= STRONG_SCORE) return "text-success";
  if (score >= OKAY_SCORE) return "text-accent";
  return "text-warning";
}

function ScoreRing({ score }: { score: number }) {
  const filled = (score / 100) * RING_CIRCUMFERENCE;
  return (
    <div className={cn("relative grid size-14 shrink-0 place-items-center", scoreColor(score))}>
      <svg aria-hidden viewBox="0 0 56 56" className="absolute inset-0 -rotate-90">
        <circle cx="28" cy="28" r={RING_RADIUS} fill="none" stroke="var(--color-edge)" strokeWidth="4" />
        <circle
          cx="28"
          cy="28"
          r={RING_RADIUS}
          fill="none"
          stroke="currentColor"
          strokeWidth="4"
          strokeLinecap="round"
          strokeDasharray={`${filled} ${RING_CIRCUMFERENCE}`}
        />
      </svg>
      <span className="text-sm font-semibold text-ink tabular-nums">{score}</span>
    </div>
  );
}

/** Score always ships with its top 3 factors (NFR-10, frontend.md UI rule 3). */
export function HookScoreCard({ hook, rank }: { hook: ScoredHook; rank: number }) {
  const maxImpact = Math.max(...hook.top_factors.map((factor) => Math.abs(factor.impact)));

  return (
    <div className={cn("glass-inset flex gap-4 p-4", rank === 1 && "border-accent/50 bg-accent-soft")}>
      <ScoreRing score={hook.score} />
      <div className="min-w-0 flex-1">
        <p dir="auto" className="font-medium">
          <span className="sr-only">Score {hook.score} out of 100. </span>
          {hook.text}
        </p>
        <ul className="mt-2.5 space-y-1.5" aria-label="Top factors">
          {hook.top_factors.map((factor) => {
            const positive = factor.impact >= 0;
            return (
              <li key={factor.label} className="grid grid-cols-[1fr_5rem] items-center gap-3 text-xs">
                <span className="truncate text-muted">
                  <span className={positive ? "text-success" : "text-danger"}>{positive ? "+" : "−"}</span> {factor.label}
                </span>
                <span className="h-1.5 overflow-hidden rounded-pill bg-surface-strong" aria-hidden>
                  <span
                    className={cn("block h-full rounded-pill", positive ? "bg-success/80" : "bg-danger/80")}
                    style={{ width: `${(Math.abs(factor.impact) / maxImpact) * 100}%` }}
                  />
                </span>
              </li>
            );
          })}
        </ul>
      </div>
    </div>
  );
}
