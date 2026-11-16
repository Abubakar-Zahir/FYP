"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";

import { getSupabase } from "@/lib/auth/supabase";
import { USE_MOCKS } from "@/lib/config";
import { GlassCard } from "@/components/ui/card";
import { EmptyState, LoadingBlock } from "@/components/ui/states";

type GuardState = "checking" | "signed-in" | "not-configured";

/**
 * Keeps signed-out visitors off app pages. This is for the experience only: the API
 * checks the token on every request, which is what actually protects the data.
 */
export function AuthGuard({ children }: { children: ReactNode }) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [state, setState] = useState<GuardState>(() => {
    if (USE_MOCKS) return "signed-in";
    return getSupabase() ? "checking" : "not-configured";
  });

  useEffect(() => {
    const supabase = getSupabase();
    if (!supabase) return;
    // window.location, not usePathname: that suspends on dynamic routes under cacheComponents.
    const toLogin = () => router.replace(`/login?next=${encodeURIComponent(window.location.pathname)}`);

    void supabase.auth.getSession().then(({ data }) => {
      if (data.session) setState("signed-in");
      else toLogin();
    });
    const { data } = supabase.auth.onAuthStateChange((event) => {
      if (event === "SIGNED_OUT") {
        // Nothing from the last account may show for the next one.
        queryClient.clear();
        toLogin();
      }
    });
    return () => data.subscription.unsubscribe();
  }, [queryClient, router]);

  if (state === "signed-in") return children;
  if (state === "not-configured") {
    return (
      <GlassCard className="mx-auto mt-16 max-w-lg">
        <EmptyState
          title="Sign-in is not configured"
          description="Set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY, or NEXT_PUBLIC_USE_MOCKS=true for the prototype."
        />
      </GlassCard>
    );
  }
  return (
    <GlassCard className="mx-auto mt-16 max-w-lg">
      <LoadingBlock label="Checking your session" />
    </GlassCard>
  );
}
