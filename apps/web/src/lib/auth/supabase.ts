import { createClient, type SupabaseClient } from "@supabase/supabase-js";

import { USE_MOCKS } from "@/lib/config";

/*
 * Supabase Auth in the browser. The API checks every token itself (apps/api/app/core/security.py),
 * so the browser only needs the session to send it. The anon key is public by design.
 */
const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL ?? "";
const SUPABASE_ANON_KEY = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? "";

let client: SupabaseClient | null = null;

export function isAuthConfigured(): boolean {
  return !USE_MOCKS && SUPABASE_URL !== "" && SUPABASE_ANON_KEY !== "";
}

/** One client per tab. Null in the prototype or when Supabase isn't configured. */
export function getSupabase(): SupabaseClient | null {
  if (!isAuthConfigured()) return null;
  client ??= createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
    auth: {
      // PKCE keeps the token out of the URL. The callback page exchanges the code itself.
      flowType: "pkce",
      detectSessionInUrl: false,
      persistSession: true,
      autoRefreshToken: true,
    },
  });
  return client;
}

export async function getAccessToken(): Promise<string | null> {
  const supabase = getSupabase();
  if (!supabase) return null;
  const { data } = await supabase.auth.getSession();
  return data.session?.access_token ?? null;
}

export function authCallbackUrl(): string {
  return `${window.location.origin}/auth/callback`;
}
