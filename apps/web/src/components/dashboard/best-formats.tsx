"use client";

import { Dna } from "lucide-react";

import { useAnalyticsOverview } from "@/lib/api/hooks";
import { HOOK_TYPE_LABEL } from "@/lib/utils/labels";
import { CardHeader, GlassCard } from "@/components/ui/card";
import { EmptyState, LoadingBlock, QueryState } from "@/components/ui/states";

export function BestFormats() {
  const overview = useAnalyticsOverview();

  return (
    <GlassCard>
      <CardHeader title="Best formats for you" description="Median outlier score by hook type. 1.0× is a typical reel." />
      <QueryState
        query={overview}
        loading={<LoadingBlock label="Loading formats" />}
        isEmpty={(data) => data.best_formats.length === 0}
        empty={<EmptyState icon={Dna} title="Not enough reels yet" description="We need about 10 analysed reels to compare formats." />}
      >
        {(data) => {
          const top = Math.max(...data.best_formats.map((format) => format.median_outlier));
          return (
            <ol className="space-y-3.5">
              {data.best_formats.map((format) => (
                <li key={format.hook_type}>
                  <div className="mb-1.5 flex items-baseline justify-between text-sm">
                    <span className="font-medium">{HOOK_TYPE_LABEL[format.hook_type]}</span>
                    <span className="text-muted tabular-nums">
                      {format.median_outlier.toFixed(1)}× <span className="text-subtle">· {format.reels} reels</span>
                    </span>
                  </div>
                  <div className="h-2 overflow-hidden rounded-pill bg-surface-strong">
                    <div
                      className="h-full rounded-pill bg-gradient-to-r from-accent-strong to-accent"
                      style={{ width: `${(format.median_outlier / top) * 100}%` }}
                    />
                  </div>
                </li>
              ))}
            </ol>
          );
        }}
      </QueryState>
    </GlassCard>
  );
}
