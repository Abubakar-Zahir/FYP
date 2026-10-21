"use client";

import { ChartLine } from "lucide-react";
import dynamic from "next/dynamic";

import { useAnalyticsOverview } from "@/lib/api/hooks";
import { CardHeader, GlassCard } from "@/components/ui/card";
import { EmptyState, QueryState, Skeleton } from "@/components/ui/states";

// Recharts is heavy. Load it only when the chart renders (frontend.md, performance 2).
const ViewsChart = dynamic(() => import("./views-chart").then((module) => module.ViewsChart), {
  ssr: false,
  loading: () => <Skeleton className="h-64 w-full" />,
});

export function ViewsTrend({ className }: { className?: string }) {
  const overview = useAnalyticsOverview();

  return (
    <GlassCard className={className}>
      <CardHeader title="Daily views" description="Across all your reels" />
      <QueryState
        query={overview}
        loading={<Skeleton className="h-64 w-full" />}
        isEmpty={(data) => data.trend.length === 0}
        empty={
          <EmptyState
            icon={ChartLine}
            title="No views yet"
            description="Connect Instagram and import your reels to see daily views."
          />
        }
      >
        {(data) => <ViewsChart points={data.trend} />}
      </QueryState>
    </GlassCard>
  );
}
