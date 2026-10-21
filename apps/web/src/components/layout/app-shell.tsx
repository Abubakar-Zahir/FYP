"use client";

import { Menu, Settings2, Sparkles, X } from "lucide-react";
import Link from "next/link";
import { Suspense, useEffect, useState, type ReactNode } from "react";

import { useMe } from "@/lib/api/hooks";
import { cn } from "@/lib/utils";

import { MockScenarioSwitcher } from "./mock-scenario-switcher";
import { APP_NAME } from "./nav-items";
import { NavLinks, NavLinksFallback } from "./nav-links";

function Logo() {
  return (
    <Link href="/dashboard" className="flex items-center gap-2.5 rounded-xl">
      <span className="grid size-9 place-items-center rounded-xl bg-gradient-to-br from-accent to-glow-2 shadow-glow">
        <Sparkles aria-hidden className="size-4 text-ink" />
      </span>
      <span className="text-lg font-semibold tracking-tight">{APP_NAME}</span>
    </Link>
  );
}

function AccountCard() {
  const me = useMe();
  const name = me.data?.name ?? "Creator";
  const handle = me.data?.instagram ? `@${me.data.instagram.username}` : "Instagram not connected";

  return (
    <Link
      href="/onboarding"
      className="flex items-center gap-3 rounded-xl p-2 transition-colors hover:bg-surface-strong"
    >
      <span className="grid size-9 shrink-0 place-items-center rounded-full border border-edge-strong bg-surface-strong text-sm font-semibold">
        {name.charAt(0)}
      </span>
      <span className="min-w-0 flex-1">
        <span className="block truncate text-sm font-medium">{name}</span>
        <span className="block truncate text-xs text-subtle">{handle}</span>
      </span>
      <Settings2 aria-label="Profile and Instagram settings" className="size-4 text-subtle" />
    </Link>
  );
}

function SidebarContent({ onNavigate }: { onNavigate?: () => void }) {
  return (
    <div className="flex h-full flex-col gap-6">
      <Logo />
      <nav aria-label="Main" className="flex-1 overflow-y-auto">
        {/* usePathname suspends under dynamic routes like /dna/[id] (cacheComponents) */}
        <Suspense fallback={<NavLinksFallback />}>
          <NavLinks onNavigate={onNavigate} />
        </Suspense>
      </nav>
      <div className="space-y-3">
        <MockScenarioSwitcher />
        <AccountCard />
      </div>
    </div>
  );
}

function MobileDrawer({ open, onClose }: { open: boolean; onClose: () => void }) {
  useEffect(() => {
    if (!open) return;
    function closeOnEscape(event: KeyboardEvent) {
      if (event.key === "Escape") onClose();
    }
    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, [open, onClose]);

  return (
    <div className={cn("fixed inset-0 z-50 lg:hidden", !open && "pointer-events-none")} aria-hidden={!open}>
      <div
        className={cn("absolute inset-0 bg-canvas/60 backdrop-blur-sm transition-opacity", open ? "opacity-100" : "opacity-0")}
        onClick={onClose}
      />
      <aside
        role="dialog"
        aria-modal="true"
        aria-label="Navigation"
        inert={!open}
        className={cn(
          "glass absolute inset-y-3 left-3 w-72 rounded-glass p-5 transition-transform duration-300",
          open ? "translate-x-0" : "-translate-x-[110%]",
        )}
      >
        <button
          type="button"
          onClick={onClose}
          className="absolute top-5 right-4 rounded-lg p-1.5 text-muted hover:bg-surface-strong hover:text-ink"
        >
          <X aria-hidden className="size-5" />
          <span className="sr-only">Close menu</span>
        </button>
        <SidebarContent onNavigate={onClose} />
      </aside>
    </div>
  );
}

export function AppShell({ children }: { children: ReactNode }) {
  const [drawerOpen, setDrawerOpen] = useState(false);

  return (
    <div className="mx-auto flex min-h-dvh max-w-[1600px] gap-6 p-3 sm:p-4 lg:p-6">
      <aside className="glass sticky top-6 hidden h-[calc(100dvh-3rem)] w-64 shrink-0 p-5 lg:block">
        <SidebarContent />
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="glass sticky top-3 z-40 mb-4 flex items-center justify-between px-4 py-3 lg:hidden">
          <Logo />
          <button
            type="button"
            onClick={() => setDrawerOpen(true)}
            aria-expanded={drawerOpen}
            className="rounded-lg p-2 text-muted hover:bg-surface-strong hover:text-ink"
          >
            <Menu aria-hidden className="size-5" />
            <span className="sr-only">Open menu</span>
          </button>
        </header>
        <MobileDrawer open={drawerOpen} onClose={() => setDrawerOpen(false)} />
        <main className="min-w-0 flex-1 pb-10 lg:pt-2">{children}</main>
      </div>
    </div>
  );
}
