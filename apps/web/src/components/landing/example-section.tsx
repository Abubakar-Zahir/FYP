import { ArrowRight, Crown, Eye } from "lucide-react";
import Link from "next/link";

import { Soft } from "./section-heading";

const STATS = [
  { value: "3", label: "versions tested" },
  { value: "72 h", label: "to a winner" },
  { value: "+35%", label: "views vs the next best" },
];

/** One worked example of the loop. Clearly marked as example output, not a real creator. */
export function ExampleSection() {
  return (
    <section className="px-4 py-20 sm:px-6 sm:py-28">
      <div className="reveal mx-auto grid max-w-[1180px] items-center gap-12 lg:grid-cols-[1.2fr_1fr]">
        <div>
          <p className="text-[9.5px] font-extrabold tracking-[0.1em] text-subtle uppercase">Example output</p>
          <h2 className="mt-3 text-[clamp(2.125rem,5vw,4rem)] leading-[1.02] font-semibold tracking-[-0.045em]">
            One idea, three hooks.
            <br />
            <Soft>The story won.</Soft>
          </h2>
          <p className="mt-5 max-w-md text-[17px] leading-[1.5] text-muted">
            A street food reel went out as three Trial Reels. “30 saal purana stall” beat the price hook and the question
            hook, so that version went to followers, and story hooks get more weight next time.
          </p>
          <dl className="mt-8 flex max-w-md divide-x divide-edge">
            {STATS.map((stat) => (
              <div key={stat.label} className="flex flex-1 flex-col-reverse px-4 first:pl-0">
                <dt className="mt-1 text-xs text-subtle">{stat.label}</dt>
                <dd className="font-display text-3xl font-semibold tracking-[-0.04em]">{stat.value}</dd>
              </div>
            ))}
          </dl>
          <Link
            href="/login"
            className="bg-cta mt-9 inline-flex h-12 items-center gap-2 rounded-xl px-7 font-bold text-white shadow-glow transition-transform hover:scale-[1.02]"
          >
            Run this on your reels
            <ArrowRight aria-hidden className="size-4" />
          </Link>
        </div>

        <div className="relative mx-auto w-64 sm:w-72">
          <div aria-hidden className="absolute -inset-10 -z-10 rounded-full bg-[radial-gradient(closest-side,rgb(255_0_135/0.3),transparent)] blur-2xl" />
          <div className="aspect-[9/19] rounded-[2.4rem] bg-ink p-2 shadow-lifted">
            <div className="relative size-full overflow-hidden rounded-[2rem] bg-[radial-gradient(circle_at_50%_62%,#fb923c_0,transparent_36%),radial-gradient(circle_at_28%_28%,#db2777_0,transparent_42%),linear-gradient(180deg,#2a0f1f,#0b0610)] text-white">
              <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-transparent to-black/30" />
              <span className="bg-cta absolute top-5 left-4 flex items-center gap-1 rounded-pill px-2.5 py-1 text-[11px] font-bold">
                <Crown aria-hidden className="size-3" />
                Winner · variant C
              </span>
              <p className="absolute inset-x-4 top-[45%] text-center text-xl leading-tight font-black uppercase [text-shadow:0_2px_0_rgb(0_0_0/0.8)]">
                30 saal purana stall
              </p>
              <p className="absolute bottom-6 left-4 flex items-center gap-1.5 text-sm font-semibold">
                <Eye aria-hidden className="size-4" />
                15.9K
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
