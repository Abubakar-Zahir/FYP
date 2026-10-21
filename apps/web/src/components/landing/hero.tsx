import { ArrowRight, ShieldCheck } from "lucide-react";
import Link from "next/link";

import { PhoneStack } from "./phone-stack";

const TRUST = ["Official Instagram API", "Your password is never stored", "Built at ITU Lahore"];

export function Hero() {
  return (
    <section className="relative px-4 pt-32 pb-16 sm:px-6 sm:pt-40 lg:pb-24">
      <div className="mx-auto grid max-w-6xl items-center gap-14 lg:grid-cols-[1.05fr_1fr] lg:gap-8">
        <div>
          <p className="inline-flex animate-[rise_0.8s_ease-out_both] items-center gap-2 rounded-pill border border-edge bg-surface px-3 py-1.5 text-xs text-muted backdrop-blur-md">
            <span className="relative flex size-2">
              <span className="absolute inline-flex size-full animate-ping rounded-full bg-success opacity-70" />
              <span className="relative inline-flex size-2 rounded-full bg-success" />
            </span>
            Pilot open · 15 creators · Pakistan
          </p>

          <h1 className="mt-6 animate-[rise_0.9s_ease-out_0.1s_both] text-[clamp(2.9rem,7.2vw,6.25rem)] leading-[0.92] font-semibold tracking-[-0.045em]">
            Know what
            <br />
            goes viral{" "}
            <span className="font-display font-normal tracking-[-0.02em] text-accent italic">before</span>
            <br />
            you post.
          </h1>

          <p className="mt-7 max-w-xl animate-[rise_0.9s_ease-out_0.25s_both] text-base leading-relaxed text-muted sm:text-lg">
            Reelmind reads <em className="text-ink not-italic">why</em> reels work, writes the script in your voice, in
            English, Urdu or Roman Urdu, and tests three versions as Trial Reels on strangers. Your followers only see
            the winner.
          </p>

          <div className="mt-9 flex animate-[rise_0.9s_ease-out_0.4s_both] flex-wrap items-center gap-3">
            <Link
              href="/login"
              className="group inline-flex h-13 items-center gap-2 rounded-pill bg-gradient-to-r from-accent to-accent-glow px-7 font-semibold text-on-accent shadow-[0_10px_40px_-10px_rgb(167_139_250/0.8)] transition-transform hover:scale-[1.03]"
            >
              Join the pilot
              <ArrowRight aria-hidden className="size-4 transition-transform group-hover:translate-x-1" />
            </Link>
            <a
              href="#dna"
              className="inline-flex h-13 items-center rounded-pill border border-edge-strong px-6 font-medium text-ink transition-colors hover:bg-surface-strong"
            >
              See how it works
            </a>
          </div>

          <ul className="mt-10 flex animate-[rise_0.9s_ease-out_0.55s_both] flex-wrap gap-x-5 gap-y-2 text-xs text-subtle">
            {TRUST.map((item) => (
              <li key={item} className="flex items-center gap-1.5">
                <ShieldCheck aria-hidden className="size-3.5 text-accent" />
                {item}
              </li>
            ))}
          </ul>
        </div>

        <div className="animate-[rise_1.1s_ease-out_0.3s_both]">
          <PhoneStack />
        </div>
      </div>
    </section>
  );
}
