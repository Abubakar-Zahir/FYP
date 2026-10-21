import { ArrowRight, Lightbulb } from "lucide-react";

import { cn } from "@/lib/utils";

import { SectionHeading, Serif } from "./section-heading";

const COMMENTS = [
  { text: "Ye kahan hai exact location?", tone: "accent" },
  { text: "Karachi ka bhi review karo plz", tone: "accent" },
  { text: "Finally koi honest review deta hai ❤️", tone: "success" },
  { text: "150 nahi 200 ka hai ab", tone: "warning" },
  { text: "Address plz 🙏", tone: "accent" },
  { text: "Your reactions are the best 😂", tone: "success" },
  { text: "Islamabad aao kabhi!", tone: "accent" },
  { text: "Safai ka kya haal hai?", tone: "danger" },
  { text: "Is this near Mall Road?", tone: "accent" },
  { text: "Bohat acha content bhai", tone: "success" },
] as const;

const TONE_DOT = {
  accent: "bg-accent",
  success: "bg-success",
  warning: "bg-warning",
  danger: "bg-danger",
} as const;

const THEMES = [
  { theme: "Where is this place?", count: 412, share: 100, idea: "Locations recap: 10 spots in 30 seconds" },
  { theme: "Try other cities", count: 268, share: 65, idea: "Karachi vs Lahore samosa chaat face-off" },
  { theme: "Prices seem wrong", count: 97, share: 24, idea: "Prices then vs now at Anarkali" },
];

function CommentColumn({ hidden }: { hidden?: boolean }) {
  return (
    <ul aria-hidden={hidden} className="flex flex-col gap-2.5 pb-2.5">
      {COMMENTS.map((comment) => (
        <li key={comment.text} className="glass-inset flex items-center gap-2.5 rounded-2xl px-3.5 py-2.5 text-sm">
          <span className={cn("size-1.5 shrink-0 rounded-full", TONE_DOT[comment.tone])} />
          {comment.text}
        </li>
      ))}
    </ul>
  );
}

export function CommentsSection() {
  return (
    <section className="px-4 py-24 sm:px-6 sm:py-32">
      <div className="mx-auto max-w-6xl">
        <SectionHeading
          number="04"
          kicker="Comment intelligence"
          title={
            <>
              Your comments are a <Serif className="text-accent">content calendar.</Serif>
            </>
          }
          body="Built for how Pakistan actually comments: Roman Urdu, Urdu script and English, mixed in one line. We sort every comment, find the themes, and turn the loudest ones into your next videos."
        />

        <div className="mt-14 grid gap-4 lg:grid-cols-[0.9fr_auto_1.1fr] lg:items-center">
          <div className="reveal glass h-80 overflow-hidden p-4 [mask-image:linear-gradient(180deg,transparent,black_18%,black_82%,transparent)]">
            <div className="animate-[marquee-y_22s_linear_infinite] motion-reduce:animate-none">
              <CommentColumn />
              <CommentColumn hidden />
            </div>
          </div>

          <div aria-hidden className="hidden justify-center text-subtle lg:flex">
            <ArrowRight className="size-6" />
          </div>

          <div className="reveal glass p-5 sm:p-7">
            <p className="text-xs text-subtle">1,286 comments → 5 themes · last 30 days</p>
            <ol className="mt-5 space-y-5">
              {THEMES.map((theme) => (
                <li key={theme.theme}>
                  <div className="flex items-baseline justify-between gap-3">
                    <span className="font-medium">{theme.theme}</span>
                    <span className="text-sm text-muted tabular-nums">{theme.count}</span>
                  </div>
                  <div className="mt-2 h-1.5 overflow-hidden rounded-pill bg-surface-strong">
                    <div className="grow-on-view h-full rounded-pill bg-accent" style={{ width: `${theme.share}%` }} />
                  </div>
                  <p className="mt-2 flex items-center gap-1.5 text-xs text-muted">
                    <Lightbulb aria-hidden className="size-3.5 text-warning" />
                    {theme.idea}
                  </p>
                </li>
              ))}
            </ol>
          </div>
        </div>
      </div>
    </section>
  );
}
