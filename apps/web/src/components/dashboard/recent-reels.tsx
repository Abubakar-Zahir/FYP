"use client";

import { Film } from "lucide-react";

import { useReels } from "@/lib/api/hooks";
import { formatCompact, formatSeconds, formatShortDate } from "@/lib/utils";
import { HOOK_TYPE_LABEL, outlierTone } from "@/lib/utils/labels";
import { Badge } from "@/components/ui/badge";
import { ButtonLink } from "@/components/ui/button";
import { CardHeader, GlassCard } from "@/components/ui/card";
import { EmptyState, LoadingBlock, QueryState } from "@/components/ui/states";

export function RecentReels() {
  const reels = useReels();

  return (
    <GlassCard>
      <CardHeader title="Recent reels" description="Sorted by date. Outlier score compares each reel to your median." />
      <QueryState
        query={reels}
        loading={<LoadingBlock label="Loading reels" />}
        isEmpty={(page) => page.items.length === 0}
        empty={
          <EmptyState
            icon={Film}
            title="No reels imported"
            description="Connect your Instagram account and we will import your last 30 to 50 reels."
            action={<ButtonLink href="/onboarding" size="sm" variant="secondary">Connect Instagram</ButtonLink>}
          />
        }
      >
        {(page) => (
          <div className="-mx-2 overflow-x-auto">
            <table className="w-full min-w-[640px] text-left text-sm">
              <thead className="text-xs text-subtle">
                <tr>
                  <th scope="col" className="px-2 pb-3 font-medium">Reel</th>
                  <th scope="col" className="px-2 pb-3 font-medium">Hook</th>
                  <th scope="col" className="px-2 pb-3 text-right font-medium">Views</th>
                  <th scope="col" className="px-2 pb-3 text-right font-medium">Saves</th>
                  <th scope="col" className="px-2 pb-3 text-right font-medium">Shares</th>
                  <th scope="col" className="px-2 pb-3 text-right font-medium">Watch</th>
                  <th scope="col" className="px-2 pb-3 text-right font-medium">Outlier</th>
                </tr>
              </thead>
              <tbody>
                {page.items.map((reel) => (
                  <tr key={reel.id} className="border-t border-edge transition-colors hover:bg-surface">
                    <td className="max-w-72 px-2 py-3">
                      <p dir="auto" className="truncate font-medium">{reel.caption}</p>
                      <p className="text-xs text-subtle">{formatShortDate(reel.posted_at)}</p>
                    </td>
                    <td className="px-2 py-3 text-muted">{reel.hook_type ? HOOK_TYPE_LABEL[reel.hook_type] : "—"}</td>
                    <td className="px-2 py-3 text-right tabular-nums">{formatCompact(reel.views)}</td>
                    <td className="px-2 py-3 text-right tabular-nums">{formatCompact(reel.saves)}</td>
                    <td className="px-2 py-3 text-right tabular-nums">{formatCompact(reel.shares)}</td>
                    <td className="px-2 py-3 text-right tabular-nums">{formatSeconds(reel.avg_watch_time_s)}</td>
                    <td className="px-2 py-3 text-right">
                      <Badge tone={outlierTone(reel.outlier_score)}>{reel.outlier_score.toFixed(1)}×</Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </QueryState>
    </GlassCard>
  );
}
