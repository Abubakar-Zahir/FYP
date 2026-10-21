import { Check } from "lucide-react";
import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

import { Serif } from "./section-heading";

type Audience = {
  kicker: string;
  title: ReactNode;
  points: { text: string; soon?: boolean }[];
  className: string;
};

const AUDIENCES: Audience[] = [
  {
    kicker: "For creators",
    title: (
      <>
        Post less <Serif>guesswork.</Serif>
      </>
    ),
    points: [
      { text: "See which formats work for your account, not someone else's" },
      { text: "Scripts and captions in English, Urdu or Roman Urdu" },
      { text: "Auto-edit with word-level captions and silence cuts" },
      { text: "Test 3 variants before your followers see any of them" },
    ],
    className: "from-accent/25 via-accent/5",
  },
  {
    kicker: "For brands",
    title: (
      <>
        Learn from your <Serif>competitors.</Serif>
      </>
    ),
    points: [
      { text: "Turn your comment section into product feedback" },
      { text: "Scripts for your own reels, grounded in what works" },
      { text: "See your competitors' top formats, broken down", soon: true },
      { text: "Ideas built on the formats winning your category", soon: true },
    ],
    className: "from-glow-2/25 via-glow-2/5",
  },
];

export function AudienceSection() {
  return (
    <section id="audience" className="scroll-mt-28 px-4 py-24 sm:px-6 sm:py-32">
      <div className="mx-auto grid max-w-6xl gap-4 md:grid-cols-2">
        {AUDIENCES.map((audience) => (
          <article key={audience.kicker} className={cn("reveal glass bg-gradient-to-br to-transparent p-7 sm:p-10", audience.className)}>
            <p className="font-mono text-xs tracking-widest text-subtle uppercase">{audience.kicker}</p>
            <h3 className="mt-4 text-[clamp(1.9rem,3.6vw,3rem)] leading-none font-semibold tracking-[-0.035em]">{audience.title}</h3>
            <ul className="mt-8 space-y-3.5">
              {audience.points.map((point) => (
                <li key={point.text} className="flex gap-3 text-sm sm:text-base">
                  <Check aria-hidden className="mt-0.5 size-4 shrink-0 text-accent" />
                  <span className="text-muted">
                    {point.text}
                    {point.soon && (
                      <span className="ml-2 rounded-pill border border-edge-strong px-2 py-0.5 align-middle text-[10px] tracking-wide text-subtle uppercase">
                        Soon
                      </span>
                    )}
                  </span>
                </li>
              ))}
            </ul>
          </article>
        ))}
      </div>
    </section>
  );
}
