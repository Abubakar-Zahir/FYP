import { Clock } from "lucide-react";
import type { ReactNode } from "react";

import { USE_MOCKS } from "@/lib/config";

import { GlassCard } from "./card";
import { EmptyState } from "./states";

/**
 * Screens whose API arrives in a later phase. The prototype shows them on mock data. Against
 * the real API they say when they arrive, instead of failing on an endpoint that doesn't exist.
 */
export function PlannedFeature({ phase, title, children }: { phase: string; title: string; children: ReactNode }) {
  if (USE_MOCKS) return children;
  return (
    <GlassCard>
      <EmptyState icon={Clock} title={`${title} arrives in ${phase}`} description="This screen runs on sample data in the prototype only." />
    </GlassCard>
  );
}
