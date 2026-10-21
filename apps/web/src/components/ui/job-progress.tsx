"use client";

import { CircleCheck, CircleAlert, LoaderCircle, RefreshCw } from "lucide-react";

import type { Job } from "@/lib/api/types";
import { cn } from "@/lib/utils";

import { Button } from "./button";

const STATUS_LABEL: Record<Job["status"], string> = {
  queued: "Queued",
  running: "Running",
  done: "Done",
  failed: "Failed",
};

type JobProgressProps = {
  label: string;
  job: Job | undefined;
  requestError?: Error | null;
  onRetry: () => void;
};

/** Shows queued, running, done or failed for a background job. Never blocks the page (frontend.md UI rule 4). */
export function JobProgress({ label, job, requestError, onRetry }: JobProgressProps) {
  const failed = job?.status === "failed" || Boolean(requestError);
  const status = failed ? "failed" : (job?.status ?? "queued");
  const percent = Math.round((job?.progress ?? 0) * 100);

  return (
    <div className="glass-inset p-4" aria-live="polite">
      <div className="flex items-center justify-between gap-3 text-sm">
        <span className="flex items-center gap-2 font-medium text-ink">
          {status === "done" && <CircleCheck aria-hidden className="size-4 text-success" />}
          {status === "failed" && <CircleAlert aria-hidden className="size-4 text-danger" />}
          {(status === "queued" || status === "running") && (
            <LoaderCircle aria-hidden className="size-4 animate-spin text-accent" />
          )}
          {label}
        </span>
        <span className="text-xs text-muted">
          {STATUS_LABEL[status]}
          {status === "running" && ` · ${percent}%`}
        </span>
      </div>
      <div
        role="progressbar"
        aria-label={label}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={percent}
        className="mt-3 h-1.5 overflow-hidden rounded-pill bg-surface-strong"
      >
        <div
          className={cn(
            "h-full rounded-pill transition-[width] duration-700",
            failed ? "bg-danger" : "bg-gradient-to-r from-accent-strong to-accent",
          )}
          style={{ width: `${failed ? 100 : percent}%` }}
        />
      </div>
      {failed && (
        <div className="mt-3 flex items-center justify-between gap-3">
          <p className="text-xs text-danger">{requestError?.message ?? job?.error ?? "The job failed."}</p>
          <Button variant="secondary" size="sm" onClick={onRetry}>
            <RefreshCw aria-hidden />
            Retry
          </Button>
        </div>
      )}
    </div>
  );
}
