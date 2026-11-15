import { ArrowRight } from "lucide-react";
import Link from "next/link";

import { APP_NAME } from "@/components/layout/nav-items";
import MurmurationWordmark from "@/components/ui/murmuration-wordmark";
import { inter } from "@/lib/fonts";

/*
 * Dark closing section: CTA, link columns, then a flock of starlings that forms the wordmark.
 * Column layout adapted from the 21st.dev "Footer with Suite" (scrollxui/footer-with-suite).
 */

const COLUMNS = [
  {
    title: "Product",
    links: [
      { label: "How it works", href: "#how" },
      { label: "Pilot", href: "#pilot" },
      { label: "FAQ", href: "#faq" },
    ],
  },
  {
    title: "Account",
    links: [
      { label: "Sign in", href: "/login" },
      { label: "Join the pilot", href: "/login" },
    ],
  },
  {
    title: "Project",
    links: [{ label: "BS AI final year project, ITU Lahore", href: "#" }],
  },
];

export function SiteFooter() {
  return (
    <footer className="relative overflow-hidden bg-night-2 text-on-dark">
      <div
        aria-hidden
        className="absolute top-0 left-1/2 h-[26rem] w-[70rem] -translate-x-1/2 -translate-y-1/2 bg-[radial-gradient(closest-side,rgb(255_0_135/0.55),rgb(255_122_46/0.2)_50%,transparent)] blur-2xl"
      />

      <div className="relative mx-auto max-w-[1180px] px-4 pt-24 sm:px-6">
        <div className="text-center">
          <h2 className="text-[clamp(2.125rem,5vw,4rem)] leading-[1.02] font-semibold tracking-[-0.045em]">
            Stop guessing. Start knowing.
          </h2>
          <Link
            href="/login"
            className="group bg-cta mt-8 inline-flex h-14 items-center gap-3 rounded-[18px] pr-3.5 pl-[30px] text-[19px] font-bold text-white shadow-glow transition-transform hover:scale-[1.02]"
          >
            Join the pilot, free
            <ArrowRight aria-hidden className="size-5 transition-transform group-hover:translate-x-1" />
          </Link>
        </div>

        <div className="mt-24 grid gap-10 border-t border-white/10 pt-12 sm:grid-cols-[1.4fr_repeat(3,1fr)]">
          <p className="max-w-xs text-sm leading-relaxed text-on-dark-soft">
            {APP_NAME} reads why reels work, writes scripts in your voice and tests them as Trial Reels.
          </p>
          {COLUMNS.map((column) => (
            <nav key={column.title} aria-label={column.title}>
              <p className="text-[11px] font-semibold tracking-[0.14em] text-white/40 uppercase">{column.title}</p>
              <ul className="mt-4 space-y-2.5">
                {column.links.map((link) => (
                  <li key={link.label}>
                    <Link href={link.href} className="text-sm text-on-dark-soft transition-colors hover:text-white">
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </nav>
          ))}
        </div>
      </div>

      {/* Starlings that gather into the wordmark. From 21st.dev, @kedhareswer/murmuration-wordmark */}
      <MurmurationWordmark
        word={APP_NAME}
        birds={3200}
        preset="night"
        palette={{ skyTop: "#121214", skyLow: "#1a0a1e", sun: "#ff0087", ink: "#f5f5f7" }}
        reeds={false}
        fontFamily={inter.style.fontFamily}
        height="clamp(300px, 40vw, 540px)"
        className="mt-10"
      />

      <div className="relative border-t border-white/10 px-4 py-4 text-center text-xs text-white/40 sm:px-6">
        Official Instagram APIs only · Your password is never stored
      </div>
    </footer>
  );
}
