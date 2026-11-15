import { Captions, Crown, Film, Lightbulb, Scissors } from "lucide-react";
import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

import { SectionHeading, Soft } from "./section-heading";

/* ---------- Step visuals. All numbers are example output ---------- */

const BEATS = [
  { label: "Hook", time: "0–3s", grow: 3, color: "bg-accent" },
  { label: "Context", time: "3–8s", grow: 5, color: "bg-glow-1" },
  { label: "Proof", time: "8–20s", grow: 12, color: "bg-glow-2" },
  { label: "Payoff", time: "20–25s", grow: 5, color: "bg-warning" },
  { label: "CTA", time: "25–28s", grow: 3, color: "bg-ink" },
];

function DnaVisual() {
  return (
    <>
      <p className="text-sm font-medium">“Anarkali ki sab se crispy samosa chaat?”</p>
      <div className="mt-5 flex h-14 gap-1 overflow-hidden rounded-xl">
        {BEATS.map((beat) => (
          <div key={beat.label} className={cn("flex min-w-0 items-end p-2 text-white", beat.color)} style={{ flexGrow: beat.grow }}>
            <span className="truncate text-xs font-bold">{beat.label}</span>
          </div>
        ))}
      </div>
      <dl className="mt-5 grid grid-cols-3 gap-2">
        {[
          ["Hook type", "Question"],
          ["Pacing", "4.2 cuts / 10s"],
          ["Length", "28 s"],
        ].map(([label, value]) => (
          <div key={label} className="glass-inset p-3">
            <dt className="text-[11px] text-subtle">{label}</dt>
            <dd className="mt-0.5 text-sm font-semibold">{value}</dd>
          </div>
        ))}
      </dl>
    </>
  );
}

const HOOKS = [
  { text: "Gol gappay: kya ye hype ke qabil hain?", score: 84, why: "Question hook, your best format" },
  { text: "Maine 3 jagah try kiye. Result shocking tha", score: 77, why: "Story with stakes" },
  { text: "Liberty ka sab se underrated thela", score: 71, why: "Local place name" },
];

function ScriptVisual() {
  return (
    <ol className="space-y-2">
      {HOOKS.map((hook, index) => (
        <li key={hook.text} className={cn("glass-inset flex items-center gap-3 p-3", index === 0 && "border-accent/40 bg-accent-soft")}>
          <span
            className={cn(
              "grid size-10 shrink-0 place-items-center rounded-lg text-sm font-bold tabular-nums",
              index === 0 ? "bg-cta text-white" : "bg-surface text-ink",
            )}
          >
            {hook.score}
          </span>
          <span className="min-w-0">
            <span className="block text-sm font-medium">{hook.text}</span>
            <span className="block text-xs text-subtle">{hook.why}</span>
          </span>
        </li>
      ))}
    </ol>
  );
}

function EditVisual() {
  return (
    <div className="flex items-center gap-5">
      <div className="relative aspect-[9/16] w-32 shrink-0 overflow-hidden rounded-2xl bg-[radial-gradient(circle_at_50%_60%,#fb923c_0,transparent_45%),linear-gradient(180deg,#2a0f1f,#0b0610)] text-white">
        <p className="absolute inset-x-2 bottom-8 text-center text-[13px] leading-tight font-black uppercase">
          Ye <span className="text-[#ffd400]">crunch</span> sunao
        </p>
      </div>
      <ul className="space-y-2.5 text-sm">
        {[
          { icon: Captions, text: "Word-level captions" },
          { icon: Scissors, text: "Silences cut" },
          { icon: Film, text: "B-roll matched to the script" },
        ].map(({ icon: Icon, text }) => (
          <li key={text} className="flex items-center gap-2.5">
            <span className="grid size-8 place-items-center rounded-lg bg-accent-soft text-accent">
              <Icon aria-hidden className="size-4" />
            </span>
            {text}
          </li>
        ))}
      </ul>
    </div>
  );
}

const VARIANTS = [
  { label: "A", hook: "Sab se crispy chaat?", views: 11.8 },
  { label: "B", hook: "Best Rs 150 in Lahore?", views: 7.3 },
  { label: "C", hook: "30 saal purana stall", views: 15.9, winner: true },
];

function TrialVisual() {
  return (
    <>
      <p className="flex justify-between text-xs text-subtle">
        <span>Views after 72 h</span>
        <span>non-followers only</span>
      </p>
      <ul className="mt-4 space-y-4">
        {VARIANTS.map((variant) => (
          <li key={variant.label}>
            <div className="mb-1.5 flex items-center justify-between gap-3 text-sm">
              <span className="flex min-w-0 items-center gap-2">
                <span
                  className={cn(
                    "grid size-6 shrink-0 place-items-center rounded-md text-[11px] font-bold",
                    variant.winner ? "bg-cta text-white" : "bg-surface-strong",
                  )}
                >
                  {variant.winner ? <Crown aria-label="Winner" className="size-3.5" /> : variant.label}
                </span>
                <span className="truncate font-medium">{variant.hook}</span>
              </span>
              <span className={cn("font-semibold tabular-nums", variant.winner && "text-accent")}>{variant.views}K</span>
            </div>
            <div className="h-2.5 overflow-hidden rounded-pill bg-surface-strong">
              <div
                className={cn("grow-on-view h-full rounded-pill", variant.winner ? "bg-cta" : "bg-ink/25")}
                style={{ width: `${(variant.views / 15.9) * 100}%` }}
              />
            </div>
          </li>
        ))}
      </ul>
    </>
  );
}

const THEMES = [
  { theme: "Where is this place?", count: 412, share: 100, idea: "10 spots in 30 seconds" },
  { theme: "Try other cities", count: 268, share: 65, idea: "Karachi vs Lahore chaat face-off" },
  { theme: "Prices seem wrong", count: 97, share: 24, idea: "Prices then vs now" },
];

function CommentsVisual() {
  return (
    <>
      <p className="text-xs text-subtle">1,286 comments → 5 themes · last 30 days</p>
      <ol className="mt-4 space-y-4">
        {THEMES.map((theme) => (
          <li key={theme.theme}>
            <div className="flex justify-between gap-3 text-sm">
              <span className="font-medium">{theme.theme}</span>
              <span className="text-muted tabular-nums">{theme.count}</span>
            </div>
            <div className="mt-1.5 h-1.5 overflow-hidden rounded-pill bg-surface-strong">
              <div className="grow-on-view h-full rounded-pill bg-accent" style={{ width: `${theme.share}%` }} />
            </div>
            <p className="mt-1.5 flex items-center gap-1.5 text-xs text-muted">
              <Lightbulb aria-hidden className="size-3.5 text-warning" />
              Next video: {theme.idea}
            </p>
          </li>
        ))}
      </ol>
    </>
  );
}

const LOOPS = [
  { week: "Week 1", question: 34, story: 33, list: 33 },
  { week: "Week 3", question: 52, story: 31, list: 17 },
  { week: "Week 5", question: 64, story: 28, list: 8 },
];

function LearnVisual() {
  return (
    <>
      <p className="text-xs text-subtle">Which hook style gets picked for your next variants</p>
      <ul className="mt-4 space-y-3">
        {LOOPS.map((loop) => (
          <li key={loop.week} className="flex items-center gap-3">
            <span className="w-14 shrink-0 text-xs text-muted">{loop.week}</span>
            <div className="flex h-6 flex-1 overflow-hidden rounded-md text-[10px] font-semibold text-white">
              <span className="bg-cta grid place-items-center" style={{ width: `${loop.question}%` }}>
                Question
              </span>
              <span className="grid place-items-center bg-ink/70" style={{ width: `${loop.story}%` }}>
                Story
              </span>
              <span className="grid place-items-center bg-ink/30" style={{ width: `${loop.list}%` }} />
            </div>
          </li>
        ))}
      </ul>
    </>
  );
}

/* ---------- Steps ---------- */

type Step = { title: ReactNode; body: string; visual: ReactNode };

const STEPS: Step[] = [
  {
    title: (
      <>
        Reads the reel.
        <br />
        <Soft>Finds the structure.</Soft>
      </>
    ),
    body: "Upload a reel that blew up, yours or one you admire. Reelmind pulls the transcript, every cut, the hook and the call to action, and saves it as a format you can reuse.",
    visual: <DnaVisual />,
  },
  {
    title: (
      <>
        Writes the script
        <br />
        <Soft>in your voice.</Soft>
      </>
    ),
    body: "Type a rough idea. You get five hooks, three angles and a full script, learned from your own captions, in English, Urdu or Roman Urdu. Every hook gets a score with the reasons behind it.",
    visual: <ScriptVisual />,
  },
  {
    title: (
      <>
        Edits the footage.
        <br />
        <Soft>You just record.</Soft>
      </>
    ),
    body: "Upload your raw clip. Captions land word by word, silences get cut, and B-roll fills the gaps. Preview it in the browser before anything goes live.",
    visual: <EditVisual />,
  },
  {
    title: (
      <>
        Tests three versions
        <br />
        <Soft>on strangers.</Soft>
      </>
    ),
    body: "Same footage, three hooks, openers and captions. They go out as Instagram Trial Reels to people who don't follow you yet. After 72 hours the numbers pick the winner.",
    visual: <TrialVisual />,
  },
  {
    title: (
      <>
        Reads your comments.
        <br />
        <Soft>Finds the next video.</Soft>
      </>
    ),
    body: "Roman Urdu, Urdu script and English, mixed in one line. Every comment gets sorted into questions, requests, praise and complaints, and the loudest themes become ideas.",
    visual: <CommentsVisual />,
  },
  {
    title: (
      <>
        Every loop makes
        <br />
        <Soft>the next one better.</Soft>
      </>
    ),
    body: "Each result updates a model of what works for your audience, not someone else's. The next set of variants leans toward the hook styles that keep winning for you.",
    visual: <LearnVisual />,
  },
];

export function HowItWorks() {
  return (
    <section id="how" className="scroll-mt-10 px-4 py-20 sm:px-6 sm:py-28">
      <SectionHeading title="How it works" />

      <ol className="mx-auto mt-16 max-w-[1180px] space-y-20 sm:mt-24 sm:space-y-32">
        {STEPS.map((step, index) => (
          <li key={index} className="reveal grid items-center gap-8 lg:grid-cols-2 lg:gap-16">
            <div className={cn(index % 2 === 1 && "lg:order-2")}>
              <p className="text-[13px] font-semibold text-accent tabular-nums">0{index + 1}</p>
              <h3 className="mt-3 text-[clamp(1.875rem,3.6vw,2.875rem)] leading-[1.05] font-medium tracking-[-0.03em]">
                {step.title}
              </h3>
              <p className="mt-5 max-w-md text-[17px] leading-[1.5] text-muted">{step.body}</p>
            </div>
            <div className="relative">
              <div
                aria-hidden
                className="absolute inset-6 -z-10 rounded-[2rem] bg-[radial-gradient(closest-side,rgb(255_142_224/0.35),rgb(255_196_160/0.25)_50%,transparent)] blur-2xl"
              />
              <div className="glass rounded-3xl p-5 sm:p-7">{step.visual}</div>
            </div>
          </li>
        ))}
      </ol>
    </section>
  );
}
