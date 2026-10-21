import { Brain, Crown } from "lucide-react";

import { cn } from "@/lib/utils";

import { SectionHeading, Serif } from "./section-heading";

const VARIANTS = [
  { label: "A", hook: "Sab se crispy chaat?", opener: "Crunch close-up", views: 11800, display: "11.8K" },
  { label: "B", hook: "Best Rs 150 in Lahore?", opener: "Price board first", views: 7300, display: "7.3K" },
  { label: "C", hook: "30 saal purana stall", opener: "Stall owner smiling", views: 15900, display: "15.9K", winner: true },
];

const TOP_VIEWS = Math.max(...VARIANTS.map((variant) => variant.views));

const STEPS = [
  { time: "0 h", text: "3 variants go out as Trial Reels, to non-followers only" },
  { time: "24 h", text: "First insights pulled: views, reach, saves, shares" },
  { time: "72 h", text: "Winner picked. Share it to your followers in one tap" },
];

export function TrialSection() {
  return (
    <section id="trial" className="relative scroll-mt-28 px-4 py-24 sm:px-6 sm:py-32">
      <div className="mx-auto max-w-6xl">
        <SectionHeading
          number="03"
          kicker="Trial Reels"
          title={
            <>
              Test on strangers. <Serif className="text-warning">Post the winner.</Serif>
            </>
          }
          body="Same footage, three different hook lines, openers and captions. Instagram shows them to people who don't follow you yet, and the numbers decide, not your gut."
        />

        <div className="mt-14 grid gap-4 lg:grid-cols-[1.4fr_1fr]">
          <div className="reveal glass p-5 sm:p-8">
            <div className="flex items-center justify-between text-xs text-subtle">
              <span>Views after 72 h</span>
              <span className="font-mono">non-followers only</span>
            </div>
            <ul className="mt-6 space-y-6">
              {VARIANTS.map((variant) => (
                <li key={variant.label}>
                  <div className="mb-2 flex items-end justify-between gap-3">
                    <div className="flex min-w-0 items-center gap-3">
                      <span
                        className={cn(
                          "grid size-9 shrink-0 place-items-center rounded-xl text-sm font-bold",
                          variant.winner ? "animate-[pulse-ring_2s_ease-out_infinite] bg-warning text-on-accent" : "bg-surface-strong",
                        )}
                      >
                        {variant.winner ? <Crown aria-label="Winner" className="size-4" /> : variant.label}
                      </span>
                      <span className="min-w-0">
                        <span className="block truncate font-medium">{variant.hook}</span>
                        <span className="block text-xs text-subtle">{variant.opener}</span>
                      </span>
                    </div>
                    <span className={cn("text-2xl font-semibold tracking-tight tabular-nums", variant.winner && "text-warning")}>
                      {variant.display}
                    </span>
                  </div>
                  <div className="h-3 overflow-hidden rounded-pill bg-surface-strong">
                    <div
                      className={cn(
                        "grow-on-view h-full rounded-pill",
                        variant.winner ? "bg-gradient-to-r from-warning/70 to-warning" : "bg-gradient-to-r from-accent-strong/60 to-accent/80",
                      )}
                      style={{ width: `${(variant.views / TOP_VIEWS) * 100}%` }}
                    />
                  </div>
                </li>
              ))}
            </ul>
          </div>

          <div className="reveal flex flex-col gap-4">
            <ol className="glass flex-1 space-y-5 p-5 sm:p-7">
              {STEPS.map((step) => (
                <li key={step.time} className="flex gap-4">
                  <span className="w-12 shrink-0 font-mono text-sm text-accent">{step.time}</span>
                  <span className="text-sm text-muted">{step.text}</span>
                </li>
              ))}
            </ol>
            <div className="glass flex gap-4 p-5 sm:p-6">
              <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-accent-soft text-accent">
                <Brain aria-hidden className="size-5" />
              </span>
              <p className="text-sm text-muted">
                <span className="font-medium text-ink">It learns you.</span> Every result updates a model of what works
                for your audience, so the next set of variants starts smarter.
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
