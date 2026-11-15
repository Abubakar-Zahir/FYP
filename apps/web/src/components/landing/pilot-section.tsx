import { ArrowRight, Check } from "lucide-react";
import Link from "next/link";

import { cn } from "@/lib/utils";

import { SectionHeading } from "./section-heading";

type Plan = {
  name: string;
  price: string;
  note: string;
  points: { text: string; soon?: boolean }[];
  cta: string;
  featured?: boolean;
};

const PLANS: Plan[] = [
  {
    name: "Creators",
    price: "Free",
    note: "for the 5-week pilot · 15 spots",
    points: [
      { text: "Format DNA from reels you upload" },
      { text: "Scripts and hooks in English, Urdu or Roman Urdu" },
      { text: "Auto-edit with word-level captions" },
      { text: "3 Trial Reel variants per video" },
      { text: "Comment themes and a weekly report" },
    ],
    cta: "Apply for the pilot",
    featured: true,
  },
  {
    name: "Brands",
    price: "Later",
    note: "after the pilot",
    points: [
      { text: "Turn your comment section into product feedback" },
      { text: "Scripts for your own reels, based on what works" },
      { text: "Competitor formats, broken down", soon: true },
      { text: "Creator matching", soon: true },
    ],
    cta: "Join the waitlist",
  },
];

const ASKS = ["1,000+ followers", "Public professional account", "A few reels a week"];

export function PilotSection() {
  return (
    <section id="pilot" className="scroll-mt-10 px-4 py-20 sm:px-6 sm:py-28">
      <SectionHeading
        kicker="The pilot"
        title="Free while we prove it works"
        body="We're testing Reelmind with real creators for 5 weeks and reporting the results honestly, including what didn't work."
      />

      <ul className="mx-auto mt-6 flex flex-wrap justify-center gap-2">
        {ASKS.map((ask) => (
          <li key={ask} className="rounded-pill border border-edge bg-surface px-3 py-1 text-[13px] text-muted">
            {ask}
          </li>
        ))}
      </ul>

      <div className="mx-auto mt-14 grid max-w-3xl gap-5 md:grid-cols-2">
        {PLANS.map((plan) => (
          <article
            key={plan.name}
            className={cn(
              "reveal glass flex flex-col rounded-3xl p-7",
              plan.featured && "border-accent/40 shadow-[0_20px_60px_-20px_rgb(255_0_135/0.45)]",
            )}
          >
            <p className="flex items-center justify-between text-[15px] font-semibold">
              {plan.name}
              {plan.featured && (
                <span className="bg-cta rounded-pill px-2.5 py-0.5 text-[11px] font-bold text-white">Open now</span>
              )}
            </p>
            <p className="mt-4 font-display text-5xl font-semibold tracking-[-0.045em]">{plan.price}</p>
            <p className="mt-1 text-[13px] text-subtle">{plan.note}</p>

            <ul className="mt-7 flex-1 space-y-3">
              {plan.points.map((point) => (
                <li key={point.text} className="flex gap-2.5 text-[14.5px]">
                  <Check aria-hidden className={cn("mt-0.5 size-4 shrink-0", plan.featured ? "text-accent" : "text-subtle")} />
                  <span className="text-muted">
                    {point.text}
                    {point.soon && (
                      <span className="ml-2 rounded-pill border border-edge-strong px-1.5 py-px align-middle text-[10px] tracking-wide text-subtle uppercase">
                        Soon
                      </span>
                    )}
                  </span>
                </li>
              ))}
            </ul>

            <Link
              href="/login"
              className={cn(
                "group mt-8 inline-flex h-12 items-center justify-center gap-2 rounded-xl font-bold tracking-[-0.01em] transition-transform hover:scale-[1.02]",
                plan.featured ? "bg-cta text-white shadow-glow" : "bg-cta-dark text-white",
              )}
            >
              {plan.cta}
              <ArrowRight aria-hidden className="size-4 transition-transform group-hover:translate-x-1" />
            </Link>
          </article>
        ))}
      </div>
    </section>
  );
}
