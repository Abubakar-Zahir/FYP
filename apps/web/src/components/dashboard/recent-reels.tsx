"use client";

import { useQueryClient } from "@tanstack/react-query";
import { Dna, Film, LoaderCircle } from "lucide-react";
import { useEffect } from "react";

import { queryKeys, useAnalyseReel, useJob, useReels } from "@/lib/api/hooks";
import type { Reel } from "@/lib/api/types";
import { formatCompact, formatOutlier, formatSeconds, formatShortDate } from "@/lib/utils";
import { HOOK_TYPE_LABEL, outlierTone } from "@/lib/utils/labels";
import { Badge } from "@/components/ui/badge";
import { Button, ButtonLink } from "@/components/ui/button";
import { CardHeader, GlassCard } from "@/components/ui/card";
import { EmptyState, LoadingBlock, QueryState } from "@/components/ui/states";

/** A reel without a hook type has no DNA record yet. Analysing it runs the DNA job on the video. */
function HookCell({ reel }: { reel: Reel }) {
  const queryClient = useQueryClient();
  const analyse = useAnalyseReel();
  const job = useJob(analyse.data?.job_id ?? null);
  const status = job.data?.status;

  useEffect(() => {
    if (status === "done") void queryClient.invalidateQueries({ queryKey: queryKeys.reels });
  }, [status, queryClient]);

  if (reel.hook_type) return <>{HOOK_TYPE_LABEL[reel.hook_type]}</>;
  if (status === "failed" || analyse.isError) return <span className="text-danger">Failed</span>;
  if (analyse.data || analyse.isPending) {
    return (
      <span className="inline-flex items-center gap-1.5 text-subtle">
        <LoaderCircle aria-hidden className="size-3.5 animate-spin" />
        Analysing
      </span>
    );
  }
  return (
    <Button variant="ghost" size="sm" onClick={() => analyse.mutate(reel.id)}>
      <Dna aria-hidden />
      Analyse
    </Button>
  );
}

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
                      <p dir="auto" className="truncate font-medium">{reel.caption ?? reel.title}</p>
                      <p className="text-xs text-subtle">{formatShortDate(reel.posted_at)}</p>
                    </td>
                    <td className="px-2 py-3 text-muted"><HookCell reel={reel} /></td>
                    <td className="px-2 py-3 text-right tabular-nums">{formatCompact(reel.views)}</td>
                    <td className="px-2 py-3 text-right tabular-nums">{formatCompact(reel.saves)}</td>
                    <td className="px-2 py-3 text-right tabular-nums">{formatCompact(reel.shares)}</td>
                    <td className="px-2 py-3 text-right tabular-nums">{formatSeconds(reel.avg_watch_time_s)}</td>
                    <td className="px-2 py-3 text-right">
                      <Badge tone={outlierTone(reel.outlier_score)}>{formatOutlier(reel.outlier_score)}</Badge>
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
