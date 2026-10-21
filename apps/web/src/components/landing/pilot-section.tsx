import { ArrowRight, Eye, KeyRound, Trash2 } from "lucide-react";
import Link from "next/link";

import { Serif } from "./section-heading";

const PRINCIPLES = [
  { icon: KeyRound, title: "Official APIs only", text: "We connect through Instagram's own login. We never see or store your password." },
  { icon: Trash2, title: "Your data, your call", text: "Disconnect and delete everything, videos and comments included, in one click." },
  { icon: Eye, title: "Honest numbers", text: "We report what didn't work too. Every score shows the reasons behind it." },
];

const PILOT_FACTS = [
  { value: "15", label: "creator spots" },
  { value: "5", label: "weeks" },
  { value: "Free", label: "during the pilot" },
];

export function PilotSection() {
  return (
    <section id="pilot" className="scroll-mt-28 px-4 pt-12 pb-24 sm:px-6 sm:pb-32">
      <div className="mx-auto max-w-6xl">
        <ul className="grid gap-4 md:grid-cols-3">
          {PRINCIPLES.map(({ icon: Icon, title, text }) => (
            <li key={title} className="reveal glass-inset p-6">
              <Icon aria-hidden className="size-5 text-accent" />
              <p className="mt-4 font-medium">{title}</p>
              <p className="mt-1.5 text-sm text-muted">{text}</p>
            </li>
          ))}
        </ul>

        <div className="reveal glass relative mt-24 overflow-hidden px-6 py-16 text-center sm:px-12 sm:py-24">
          <div aria-hidden className="absolute -top-1/2 left-1/2 size-[42rem] -translate-x-1/2 rounded-full bg-[radial-gradient(circle,rgb(167_139_250/0.35),transparent_65%)]" />
          <div className="relative">
            <p className="font-mono text-xs tracking-widest text-subtle uppercase">The pilot</p>
            <h2 className="mx-auto mt-5 max-w-4xl text-[clamp(2.6rem,7vw,5.75rem)] leading-[0.92] font-semibold tracking-[-0.045em]">
              Stop guessing.
              <br />
              <Serif className="text-gradient">Start knowing.</Serif>
            </h2>
            <p className="mx-auto mt-6 max-w-lg text-muted">
              We&apos;re looking for creators with 1,000+ followers and a public account who post a few reels a week.
            </p>

            <dl className="mx-auto mt-10 flex max-w-md justify-center divide-x divide-edge">
              {PILOT_FACTS.map((fact) => (
                <div key={fact.label} className="flex flex-1 flex-col-reverse px-4">
                  <dt className="mt-1 text-xs text-subtle">{fact.label}</dt>
                  <dd className="text-3xl font-semibold tracking-tight sm:text-4xl">{fact.value}</dd>
                </div>
              ))}
            </dl>

            <Link
              href="/login"
              className="group mt-11 inline-flex h-14 items-center gap-2 rounded-pill bg-ink px-8 text-base font-semibold text-canvas transition-transform hover:scale-[1.03]"
            >
              Apply for the pilot
              <ArrowRight aria-hidden className="size-4 transition-transform group-hover:translate-x-1" />
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
}
