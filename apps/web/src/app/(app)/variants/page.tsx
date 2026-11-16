import type { Metadata } from "next";
import { Suspense } from "react";

import { VariantExperiment } from "@/components/variants/variant-experiment";
import { GlassCard } from "@/components/ui/card";
import { PageHeader } from "@/components/ui/page-header";
import { LoadingBlock } from "@/components/ui/states";

export const metadata: Metadata = { title: "Variants · Reelmind" };

export default function VariantsPage() {
  return (
    <>
      <PageHeader
        eyebrow="Trial Reels"
        title="Variants"
        description="Publish 3 to 5 versions to non-followers first. We pull insights at 24 h and 72 h and pick the winner."
      />
      <Suspense fallback={<GlassCard><LoadingBlock label="Loading variants" /></GlassCard>}>
        <VariantExperiment />
      </Suspense>
    </>
  );
}
