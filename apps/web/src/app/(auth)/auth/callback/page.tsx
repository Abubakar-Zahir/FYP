import type { Metadata } from "next";

import { AuthCallback } from "@/components/auth/auth-callback";

export const metadata: Metadata = { title: "Signing in · Reelmind" };

export default function AuthCallbackPage() {
  return (
    <main className="grid min-h-dvh place-items-center p-4">
      <AuthCallback />
    </main>
  );
}
