import Link from "next/link";

import { APP_NAME } from "@/components/layout/nav-items";

export function SiteFooter() {
  return (
    <footer className="border-t border-edge px-4 py-10 sm:px-6">
      <div className="mx-auto flex max-w-6xl flex-col gap-6 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="font-display text-4xl italic">{APP_NAME}</p>
          <p className="mt-2 text-sm text-subtle">A BS AI final year project at ITU Lahore.</p>
        </div>
        <nav aria-label="Footer" className="flex gap-6 text-sm text-muted">
          <a href="#dna" className="hover:text-ink">How it works</a>
          <a href="#pilot" className="hover:text-ink">Pilot</a>
          <Link href="/login" className="hover:text-ink">Sign in</Link>
        </nav>
      </div>
    </footer>
  );
}
