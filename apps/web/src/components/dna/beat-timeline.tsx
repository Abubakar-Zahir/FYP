import type { DnaBeat } from "@/lib/api/types";
import { cn } from "@/lib/utils";

const BEAT_COLORS = ["bg-accent", "bg-glow-2/80", "bg-glow-3/80", "bg-warning/70", "bg-success/70", "bg-accent-strong"];

export function BeatTimeline({ beats, lengthSeconds }: { beats: DnaBeat[]; lengthSeconds: number }) {
  return (
    <div>
      <div className="flex h-10 gap-1 overflow-hidden rounded-xl" aria-hidden>
        {beats.map((beat, index) => (
          <div
            key={beat.label}
            className={cn("grid min-w-0 place-items-center text-[11px] font-semibold text-on-accent", BEAT_COLORS[index % BEAT_COLORS.length])}
            style={{ flexGrow: beat.end_s - beat.start_s }}
          >
            <span className="truncate px-1">{beat.label}</span>
          </div>
        ))}
      </div>
      <div className="mt-1 flex justify-between font-mono text-[11px] text-subtle" aria-hidden>
        <span>0s</span>
        <span>{lengthSeconds}s</span>
      </div>

      <ol className="mt-5 space-y-2">
        {beats.map((beat, index) => (
          <li key={beat.label} className="glass-inset flex gap-3 p-3.5">
            <span className={cn("mt-1 size-2.5 shrink-0 rounded-full", BEAT_COLORS[index % BEAT_COLORS.length])} aria-hidden />
            <div className="min-w-0 flex-1">
              <p className="flex flex-wrap items-baseline justify-between gap-x-3 text-sm">
                <span className="font-medium">{beat.label}</span>
                <span className="font-mono text-xs text-subtle tabular-nums">
                  {beat.start_s}s – {beat.end_s}s
                </span>
              </p>
              <p className="mt-0.5 text-sm text-muted">{beat.description}</p>
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}
