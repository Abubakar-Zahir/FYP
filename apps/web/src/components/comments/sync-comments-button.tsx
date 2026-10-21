"use client";

import { useQueryClient } from "@tanstack/react-query";
import { CircleAlert, CircleCheck, LoaderCircle, RefreshCw } from "lucide-react";
import { useEffect } from "react";

import { queryKeys, useJob, useSyncComments } from "@/lib/api/hooks";
import { Button } from "@/components/ui/button";

export function SyncCommentsButton() {
  const queryClient = useQueryClient();
  const sync = useSyncComments();
  const job = useJob<{ synced: number }>(sync.data?.job_id ?? null);
  const status = job.data?.status;
  const running = sync.isPending || status === "queued" || status === "running";
  const failed = sync.isError || job.isError || status === "failed";

  useEffect(() => {
    if (status !== "done") return;
    void queryClient.invalidateQueries({ queryKey: queryKeys.commentThemes });
    void queryClient.invalidateQueries({ queryKey: queryKeys.commentSummary });
  }, [status, queryClient]);

  return (
    <div className="flex items-center gap-3" aria-live="polite">
      {status === "done" && (
        <span className="flex items-center gap-1 text-xs text-success">
          <CircleCheck aria-hidden className="size-3.5" />
          {job.data?.result?.synced} new comments
        </span>
      )}
      {failed && (
        <span className="flex items-center gap-1 text-xs text-danger">
          <CircleAlert aria-hidden className="size-3.5" />
          Sync failed
        </span>
      )}
      <Button variant="secondary" onClick={() => sync.mutate()} disabled={running}>
        {running ? <LoaderCircle aria-hidden className="animate-spin" /> : <RefreshCw aria-hidden />}
        {running ? `Syncing… ${Math.round((job.data?.progress ?? 0) * 100)}%` : "Sync comments"}
      </Button>
    </div>
  );
}
