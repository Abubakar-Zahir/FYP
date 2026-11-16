import type { Metadata } from "next";
import { Suspense } from "react";

import { InstagramCallback } from "@/components/onboarding/instagram-callback";
import { GlassCard } from "@/components/ui/card";
import { LoadingBlock } from "@/components/ui/states";

export const metadata: Metadata = { title: "Connecting Instagram · Reelmind" };

/** The Meta app's redirect URI (INSTAGRAM_REDIRECT_URI) points here. */
export default function InstagramCallbackPage() {
  // useSearchParams reads the request, so it waits behind Suspense (cacheComponents).
  return (
    <Suspense fallback={<GlassCard className="mx-auto max-w-xl"><LoadingBlock label="Checking with Instagram" /></GlassCard>}>
      <InstagramCallback />
    </Suspense>
  );
}
