import { cn } from "@/lib/utils";

import { SectionHeading, Serif } from "./section-heading";

const HOOKS = [
  { text: "Gol gappay — kya ye hype ke qabil hain?", score: 84, why: "+ question hook, your best format" },
  { text: "Maine 3 jagah try kiye. Result shocking tha", score: 77, why: "+ story with stakes" },
  { text: "Liberty ka sab se underrated thela", score: 71, why: "+ local place name" },
];

const LANGUAGES = ["English", "Roman Urdu", "Mix"];

function scoreTone(score: number): string {
  if (score >= 80) return "text-success border-success/40 bg-success-soft";
  return "text-accent border-accent/40 bg-accent-soft";
}

export function ScriptSection() {
  return (
    <section className="px-4 py-24 sm:px-6 sm:py-32">
      <div className="mx-auto grid max-w-6xl items-center gap-14 lg:grid-cols-2">
        <SectionHeading
          number="02"
          kicker="Scripts"
          title={
            <>
              Sounds like you. <Serif className="text-accent">Not like a bot.</Serif>
            </>
          }
          body="Pick a template, type a rough idea. You get five hooks, three angles and a full beat-by-beat script, written from your own captions, in the language your audience actually speaks."
        />

        <div className="reveal glass p-5 sm:p-7">
          <div className="flex items-center justify-between gap-3">
            <p className="text-sm text-muted">
              Topic: <span className="text-ink">gol gappay at Liberty</span>
            </p>
            <div className="flex rounded-pill border border-edge bg-surface p-0.5 text-xs">
              {LANGUAGES.map((language) => (
                <span
                  key={language}
                  className={cn("rounded-pill px-2.5 py-1", language === "Roman Urdu" ? "bg-ink font-medium text-canvas" : "text-muted")}
                >
                  {language}
                </span>
              ))}
            </div>
          </div>

          <ol className="mt-5 space-y-2.5">
            {HOOKS.map((hook, index) => (
              <li
                key={hook.text}
                className={cn("glass-inset flex items-center gap-4 p-4", index === 0 && "border-accent/50 bg-accent-soft")}
              >
                <span className={cn("grid size-11 shrink-0 place-items-center rounded-xl border text-sm font-bold tabular-nums", scoreTone(hook.score))}>
                  {hook.score}
                </span>
                <span className="min-w-0">
                  <span className="block font-medium">{hook.text}</span>
                  <span className="mt-0.5 block text-xs text-subtle">{hook.why}</span>
                </span>
              </li>
            ))}
          </ol>
          <p className="mt-4 text-xs text-subtle">Every score shows the reasons behind it. No black boxes.</p>
        </div>
      </div>
    </section>
  );
}
