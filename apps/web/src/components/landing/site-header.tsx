import { ArrowRight, Sparkles } from "lucide-react";
import Link from "next/link";

import { APP_NAME } from "@/components/layout/nav-items";

const LINKS = [
  { href: "#how", label: "How it works" },
  { href: "#pilot", label: "Pilot" },
  { href: "#faq", label: "FAQ" },
];

export function SiteHeader() {
  return (
    <header className="absolute inset-x-0 top-0 z-50 px-4 sm:px-8">
      <nav aria-label="Main" className="mx-auto flex h-20 max-w-[1180px] items-center justify-between gap-4">
        <Link href="/" className="flex items-center gap-2 rounded-lg">
          <span className="grid size-7 place-items-center rounded-lg bg-ink text-white">
            <Sparkles aria-hidden className="size-3.5" />
          </span>
          <span className="font-display text-[17px] font-semibold tracking-[-0.03em]">{APP_NAME}</span>
        </Link>

        <ul className="hidden items-center gap-1 md:flex">
          {LINKS.map((link) => (
            <li key={link.href}>
              <a href={link.href} className="rounded-pill px-3.5 py-2 text-[14.5px] text-muted transition-colors hover:text-ink">
                {link.label}
              </a>
            </li>
          ))}
        </ul>

        <div className="flex items-center gap-2">
          <Link href="/login" className="hidden rounded-pill px-3 py-2 text-[14.5px] font-medium text-muted hover:text-ink sm:block">
            Sign in
          </Link>
          <Link
            href="/login"
            className="group bg-cta-dark flex h-10 items-center gap-3 rounded-pill pr-1.5 pl-[18px] text-[14.5px] font-semibold tracking-[-0.01em] text-white shadow-glass"
          >
            Join the pilot
            <span className="grid size-7 place-items-center rounded-full bg-white/15 transition-transform group-hover:translate-x-0.5">
              <ArrowRight aria-hidden className="size-3.5" />
            </span>
          </Link>
        </div>
      </nav>
    </header>
  );
}
