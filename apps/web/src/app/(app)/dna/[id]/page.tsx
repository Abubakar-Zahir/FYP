import type { Metadata } from "next";
import { Suspense } from "react";

import { DnaDetail } from "@/components/dna/dna-detail";
import { GlassCard } from "@/components/ui/card";
import { LoadingBlock } from "@/components/ui/states";

export const metadata: Metadata = { title: "DNA record · Reelmind" };

export default function DnaDetailPage() {
  return (
    // useParams suspends for ids not known at build time (cacheComponents)
    <Suspense fallback={<GlassCard><LoadingBlock label="Loading DNA record" /></GlassCard>}>
      <DnaDetail />
    </Suspense>
  );
}
