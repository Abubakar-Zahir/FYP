import { ArrowUpRight, Sparkles } from "lucide-react";
import Link from "next/link";

import { APP_NAME } from "@/components/layout/nav-items";

const LINKS = [
  { href: "#dna", label: "How it works" },
  { href: "#trial", label: "Trial Reels" },
  { href: "#audience", label: "Creators & brands" },
  { href: "#pilot", label: "Pilot" },
];

export function SiteHeader() {
  return (
    <header className="fixed inset-x-0 top-0 z-50 px-3 pt-3 sm:px-6 sm:pt-5">
      <nav
        aria-label="Main"
        className="glass mx-auto flex max-w-6xl items-center justify-between gap-4 rounded-pill bg-canvas/65 py-2 pr-2 pl-4 sm:pl-5"
      >
        <Link href="/" className="flex items-center gap-2 rounded-pill">
          <span className="grid size-7 place-items-center rounded-lg bg-gradient-to-br from-accent to-glow-2">
            <Sparkles aria-hidden className="size-3.5" />
          </span>
          <span className="font-semibold tracking-tight">{APP_NAME}</span>
        </Link>
        <ul className="hidden items-center gap-1 md:flex">
          {LINKS.map((link) => (
            <li key={link.href}>
              <a href={link.href} className="rounded-pill px-3.5 py-2 text-sm text-muted transition-colors hover:text-ink">
                {link.label}
              </a>
            </li>
          ))}
        </ul>
        <div className="flex items-center gap-1">
          <Link href="/login" className="hidden rounded-pill px-3.5 py-2 text-sm text-muted transition-colors hover:text-ink sm:block">
            Sign in
          </Link>
          <Link
            href="/login"
            className="group flex items-center gap-1.5 rounded-pill bg-ink px-4 py-2 text-sm font-medium text-canvas transition-transform hover:scale-[1.03]"
          >
            Join the pilot
            <ArrowUpRight aria-hidden className="size-4 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
          </Link>
        </div>
      </nav>
    </header>
  );
}
