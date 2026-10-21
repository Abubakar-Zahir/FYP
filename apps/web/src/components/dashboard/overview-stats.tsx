"use client";

import { Bookmark, Clock, Eye, Share2, TrendingDown, TrendingUp, Users, type LucideIcon } from "lucide-react";

import { useAnalyticsOverview } from "@/lib/api/hooks";
import type { AnalyticsOverview } from "@/lib/api/types";
import { cn, formatCompact, formatPercent, formatSeconds } from "@/lib/utils";
import { GlassCard } from "@/components/ui/card";
import { ErrorState, QueryState, Skeleton } from "@/components/ui/states";

type MetricKey = keyof AnalyticsOverview["totals"];

const METRICS: { key: MetricKey; label: string; icon: LucideIcon; format: (value: number) => string }[] = [
  { key: "views", label: "Views", icon: Eye, format: formatCompact },
  { key: "reach", label: "Reach", icon: Users, format: formatCompact },
  { key: "saves", label: "Saves", icon: Bookmark, format: formatCompact },
  { key: "shares", label: "Shares", icon: Share2, format: formatCompact },
  { key: "avg_watch_time_s", label: "Avg watch time", icon: Clock, format: formatSeconds },
];

function StatTile({ label, value, change, icon: Icon }: { label: string; value: string; change: number; icon: LucideIcon }) {
  const up = change >= 0;
  const TrendIcon = up ? TrendingUp : TrendingDown;
  return (
    <GlassCard className="p-4 sm:p-5">
      <div className="flex items-center justify-between text-sm text-muted">
        {label}
        <Icon aria-hidden className="size-4 text-subtle" />
      </div>
      <p className="mt-2 text-2xl font-semibold tracking-tight tabular-nums sm:text-3xl">{value}</p>
      <p className={cn("mt-1 flex items-center gap-1 text-xs", up ? "text-success" : "text-danger")}>
        <TrendIcon aria-hidden className="size-3.5" />
        {formatPercent(change)} <span className="hidden text-subtle sm:inline">vs previous 30 days</span>
      </p>
    </GlassCard>
  );
}

const STATS_GRID = "grid grid-cols-2 gap-4 md:grid-cols-3 xl:grid-cols-5";

export function OverviewStats() {
  const overview = useAnalyticsOverview();

  if (overview.isError) {
    return (
      <GlassCard>
        <ErrorState error={overview.error} onRetry={() => void overview.refetch()} />
      </GlassCard>
    );
  }

  return (
    <QueryState
      query={overview}
      loading={
        <div className={STATS_GRID} role="status" aria-label="Loading stats">
          {METRICS.map((metric) => (
            <Skeleton key={metric.key} className="h-32 rounded-glass" />
          ))}
        </div>
      }
    >
      {(data) => (
        <div className={STATS_GRID}>
          {METRICS.map(({ key, label, icon, format }) => (
            <StatTile key={key} label={label} icon={icon} value={format(data.totals[key])} change={data.change[key]} />
          ))}
        </div>
      )}
    </QueryState>
  );
}
