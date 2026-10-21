import { cn } from "@/lib/utils";

import { SectionHeading, Serif } from "./section-heading";

const BEATS = [
  { label: "Hook", time: "0–3s", note: "Question + crunch close-up", grow: 3, color: "bg-accent" },
  { label: "Context", time: "3–8s", note: "Stall name, 30 years old", grow: 5, color: "bg-glow-2" },
  { label: "Proof", time: "8–20s", note: "Three bites, 4.2 cuts / 10s", grow: 12, color: "bg-glow-3" },
  { label: "Payoff", time: "20–25s", note: "Price reveal: Rs 150", grow: 5, color: "bg-warning" },
  { label: "CTA", time: "25–28s", note: "“Save for your next trip”", grow: 3, color: "bg-success" },
];

const TRAITS = [
  { label: "Hook type", value: "Question" },
  { label: "Pacing", value: "4.2 cuts / 10s" },
  { label: "Length", value: "28 seconds" },
  { label: "Performance", value: "3.4× median" },
];

export function DnaSection() {
  return (
    <section id="dna" className="scroll-mt-28 px-4 py-24 sm:px-6 sm:py-32">
      <div className="mx-auto max-w-6xl">
        <SectionHeading
          number="01"
          kicker="Format DNA"
          title={
            <>
              Every viral reel has a <Serif className="text-accent">structure.</Serif> We read it.
            </>
          }
          body="Upload a reel that blew up, yours or one you admire. We pull the transcript, every cut, the on-screen text and the call to action, and turn it into a template you can reuse."
        />

        <div className="reveal glass mt-14 overflow-hidden p-5 sm:p-8">
          <div className="flex flex-wrap items-baseline justify-between gap-2">
            <p className="font-medium">
              “Anarkali ki sab se crispy samosa chaat?”
            </p>
            <p className="font-mono text-xs text-subtle">dna_01 · schema v1.0</p>
          </div>

          <div className="relative mt-7 overflow-hidden rounded-2xl">
            <div className="flex h-16 gap-1.5 sm:h-20">
              {BEATS.map((beat) => (
                <div
                  key={beat.label}
                  className={cn("relative flex min-w-0 items-end bg-gradient-to-b from-white/25 to-transparent p-2.5 sm:p-3", beat.color)}
                  style={{ flexGrow: beat.grow }}
                >
                  <span className="truncate text-xs font-bold text-on-accent sm:text-sm">{beat.label}</span>
                </div>
              ))}
            </div>
            {/* Scan line: the extractor "reading" the reel */}
            <div className="pointer-events-none absolute inset-y-0 left-0 w-1/4 animate-[scan_4.5s_ease-in-out_infinite] bg-gradient-to-r from-transparent via-white/45 to-transparent mix-blend-overlay motion-reduce:hidden" />
          </div>

          <ol className="mt-6 grid gap-3 sm:grid-cols-5">
            {BEATS.map((beat) => (
              <li key={beat.label} className="glass-inset p-3.5">
                <p className="flex items-center gap-2 text-xs text-subtle">
                  <span className={cn("size-2 rounded-full", beat.color)} />
                  <span className="font-mono">{beat.time}</span>
                </p>
                <p className="mt-1.5 text-sm font-medium">{beat.label}</p>
                <p className="mt-0.5 text-xs text-muted">{beat.note}</p>
              </li>
            ))}
          </ol>

          <dl className="mt-6 grid grid-cols-2 gap-px overflow-hidden rounded-2xl border border-edge bg-edge sm:grid-cols-4">
            {TRAITS.map((trait) => (
              <div key={trait.label} className="bg-canvas/70 p-4">
                <dt className="text-xs text-subtle">{trait.label}</dt>
                <dd className="mt-1 text-lg font-semibold tracking-tight">{trait.value}</dd>
              </div>
            ))}
          </dl>
        </div>
      </div>
    </section>
  );
}
