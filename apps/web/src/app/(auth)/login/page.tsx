import type { Metadata } from "next";

import { LoginPanel } from "@/components/auth/login-panel";

export const metadata: Metadata = { title: "Sign in · Reelmind" };

export default function LoginPage() {
  return (
    <main className="grid min-h-dvh place-items-center p-4">
      <LoginPanel />
    </main>
  );
}
