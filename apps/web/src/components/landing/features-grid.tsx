import { BarChart3, Eye, KeyRound, Languages, Trash2, Zap } from "lucide-react";

import { SectionHeading } from "./section-heading";

const FEATURES = [
  { icon: KeyRound, title: "Official APIs only", text: "You connect through Instagram's own login. We never see or store your password." },
  { icon: Trash2, title: "Your data, your call", text: "Disconnect and delete everything, videos and comments included, in one click." },
  { icon: Eye, title: "Honest numbers", text: "Every score shows the reasons behind it, and the weekly report shows what didn't work too." },
  { icon: Languages, title: "Roman Urdu first", text: "Scripts, captions and comment analysis in the mix of languages your audience writes in." },
  { icon: Zap, title: "Trial Reels built in", text: "Variants go out to non-followers first, so a weak hook never costs you your audience." },
  { icon: BarChart3, title: "A weekly report", text: "What worked, what to post next, and which comment themes are growing." },
];

export function FeaturesGrid() {
  return (
    <section className="px-4 py-20 sm:px-6 sm:py-28">
      <SectionHeading title="Built to run your reels, end to end." />

      <ul className="mx-auto mt-14 grid max-w-[1180px] gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {FEATURES.map(({ icon: Icon, title, text }) => (
          <li key={title} className="reveal glass rounded-3xl p-7">
            <span className="grid size-11 place-items-center rounded-xl bg-accent-soft text-accent">
              <Icon aria-hidden className="size-5" />
            </span>
            <p className="mt-5 font-display text-lg font-semibold tracking-[-0.02em]">{title}</p>
            <p className="mt-1.5 text-[15px] leading-[1.5] text-muted">{text}</p>
          </li>
        ))}
      </ul>
    </section>
  );
}
