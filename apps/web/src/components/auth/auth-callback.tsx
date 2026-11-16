"use client";

import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { getSupabase } from "@/lib/auth/supabase";
import { ButtonLink } from "@/components/ui/button";
import { GlassCard } from "@/components/ui/card";
import { EmptyState, LoadingBlock } from "@/components/ui/states";

const AFTER_SIGN_IN = "/onboarding";

/** Exchanges the code for a session. Returns what went wrong, or null when signed in. */
async function finishSignIn(): Promise<string | null> {
  const supabase = getSupabase();
  const params = new URLSearchParams(window.location.search);
  const code = params.get("code");
  if (!supabase || !code) {
    return params.get("error_description") ?? "This sign-in link is missing its code. Try signing in again.";
  }
  const { error } = await supabase.auth.exchangeCodeForSession(code);
  return error ? "This sign-in link expired or was already used. Try signing in again." : null;
}

/** Supabase sends the browser back here with `?code=` after Google sign-in or email confirmation. */
export function AuthCallback() {
  const router = useRouter();
  const [problem, setProblem] = useState<string | null>(null);
  const started = useRef(false);

  useEffect(() => {
    // Strict Mode runs effects twice, and a code can only be exchanged once.
    if (started.current) return;
    started.current = true;
    void finishSignIn().then((failure) => {
      if (failure) setProblem(failure);
      else router.replace(AFTER_SIGN_IN);
    });
  }, [router]);

  return (
    <GlassCard className="w-full max-w-md">
      {problem ? (
        <EmptyState
          title="Sign-in didn't finish"
          description={problem}
          action={<ButtonLink href="/login" variant="secondary">Back to sign in</ButtonLink>}
        />
      ) : (
        <LoadingBlock label="Signing you in" />
      )}
    </GlassCard>
  );
}
