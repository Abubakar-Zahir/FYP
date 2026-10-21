import type { Metadata } from "next";
import { Suspense } from "react";

import { ScriptStudio } from "@/components/studio/script-studio";
import { GlassCard } from "@/components/ui/card";
import { PageHeader } from "@/components/ui/page-header";
import { LoadingBlock } from "@/components/ui/states";

export const metadata: Metadata = { title: "Script studio · Reelmind" };

export default function StudioPage() {
  return (
    <>
      <PageHeader
        eyebrow="Ideation"
        title="Script studio"
        description="Pick a format, give a topic, get 5 scored hooks, 3 angles and a full script in your voice."
      />
      {/* useSearchParams (?template=) needs a Suspense boundary under cacheComponents */}
      <Suspense fallback={<GlassCard><LoadingBlock label="Loading studio" /></GlassCard>}>
        <ScriptStudio />
      </Suspense>
    </>
  );
}
