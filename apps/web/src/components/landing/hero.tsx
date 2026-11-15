import { ArrowRight, GraduationCap, ShieldCheck } from "lucide-react";
import Link from "next/link";

import { PhoneStack } from "./phone-stack";

const BADGES = [
  { icon: ShieldCheck, kicker: "Built on", label: "Official Instagram API" },
  { icon: GraduationCap, kicker: "Final year project", label: "ITU Lahore" },
];

export function Hero() {
  return (
    <section className="relative overflow-hidden px-4 pt-36 pb-10 sm:px-6 sm:pt-44">
      {/* Pink and peach glow behind the headline */}
      <div
        aria-hidden
        className="absolute -top-40 left-1/2 h-[40rem] w-[80rem] max-w-[200vw] -translate-x-1/2 bg-[radial-gradient(closest-side,rgb(255_142_224/0.55),rgb(255_196_160/0.4)_45%,transparent_75%)] blur-2xl"
      />

      <div className="relative mx-auto max-w-[1180px] text-center">
        <h1 className="mx-auto max-w-4xl animate-[rise_0.8s_ease-out_both] text-[clamp(2.6rem,6.6vw,5.375rem)] leading-[0.97] font-semibold tracking-[-0.045em] text-balance">
          Know what goes viral before you post
        </h1>

        <p className="mx-auto mt-6 max-w-xl animate-[rise_0.9s_ease-out_0.1s_both] text-[17px] leading-[1.5] text-muted">
          Reelmind reads why reels work, writes the script in your voice in English, Urdu or Roman Urdu, and tests three
          versions as Trial Reels. Your followers only see the winner.
        </p>

        <div className="mt-9 animate-[rise_0.9s_ease-out_0.2s_both]">
          <Link
            href="/login"
            className="group bg-cta inline-flex h-14 items-center gap-3 rounded-[18px] pr-3.5 pl-[30px] text-[19px] font-bold tracking-[-0.01em] text-white shadow-glow transition-transform hover:scale-[1.02]"
          >
            Join the pilot, free
            <ArrowRight aria-hidden className="size-5 transition-transform group-hover:translate-x-1" />
          </Link>
        </div>

        <ul className="mt-7 flex animate-[rise_0.9s_ease-out_0.3s_both] flex-wrap justify-center gap-3">
          {BADGES.map(({ icon: Icon, kicker, label }) => (
            <li
              key={label}
              className="flex items-center gap-2.5 rounded-xl border border-warning/35 bg-white/80 px-3 py-1.5 text-left shadow-[0_1px_2px_rgb(0_0_0/0.06)]"
            >
              <Icon aria-hidden className="size-5 text-warning" />
              <span>
                <span className="block text-[9.5px] font-extrabold tracking-[0.08em] text-warning/80 uppercase">{kicker}</span>
                <span className="block text-[13.5px] font-semibold text-warning">{label}</span>
              </span>
            </li>
          ))}
        </ul>

        <div className="mt-14 animate-[rise_1.1s_ease-out_0.35s_both]">
          <PhoneStack />
        </div>
      </div>
    </section>
  );
}
