"use client";

import type { UseQueryResult } from "@tanstack/react-query";
import { CircleAlert, Inbox, LoaderCircle, RefreshCw, type LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

import { Button } from "./button";

export function Skeleton({ className }: { className?: string }) {
  return (
    <div
      aria-hidden
      className={cn(
        "relative overflow-hidden rounded-xl bg-surface-strong",
        "after:absolute after:inset-0 after:-translate-x-full after:animate-[shimmer_1.6s_infinite] after:bg-gradient-to-r after:from-transparent after:via-white/10 after:to-transparent",
        className,
      )}
    />
  );
}

export function LoadingBlock({ label, className }: { label: string; className?: string }) {
  return (
    <div role="status" aria-label={label} className={cn("space-y-3", className)}>
      <Skeleton className="h-5 w-1/3" />
      <Skeleton className="h-24 w-full" />
      <Skeleton className="h-4 w-2/3" />
    </div>
  );
}

export function LoadingScreen() {
  return (
    <div role="status" className="grid min-h-dvh place-items-center">
      <LoaderCircle aria-hidden className="size-8 animate-spin text-accent" />
      <span className="sr-only">Loading</span>
    </div>
  );
}

type EmptyStateProps = {
  title: string;
  description: string;
  icon?: LucideIcon;
  action?: ReactNode;
};

export function EmptyState({ title, description, icon: Icon = Inbox, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center gap-3 px-4 py-10 text-center">
      <div className="glass-inset grid size-12 place-items-center rounded-2xl text-accent">
        <Icon aria-hidden className="size-5" />
      </div>
      <div>
        <p className="font-medium text-ink">{title}</p>
        <p className="mx-auto mt-1 max-w-sm text-sm text-muted">{description}</p>
      </div>
      {action}
    </div>
  );
}

export function ErrorState({ error, onRetry }: { error: Error; onRetry?: () => void }) {
  return (
    <div role="alert" className="flex flex-col items-center gap-3 px-4 py-10 text-center">
      <div className="grid size-12 place-items-center rounded-2xl border border-danger/40 bg-danger-soft text-danger">
        <CircleAlert aria-hidden className="size-5" />
      </div>
      <div>
        <p className="font-medium text-ink">Something went wrong</p>
        <p className="mx-auto mt-1 max-w-sm text-sm text-muted">{error.message}</p>
      </div>
      {onRetry && (
        <Button variant="secondary" size="sm" onClick={onRetry}>
          <RefreshCw aria-hidden />
          Try again
        </Button>
      )}
    </div>
  );
}

type QueryStateProps<T> = {
  query: UseQueryResult<T>;
  loading: ReactNode;
  isEmpty?: (data: T) => boolean;
  empty?: ReactNode;
  children: (data: T) => ReactNode;
};

/** Renders exactly one of loading, error, empty or data, so no screen forgets a state (rules.md 4.8). */
export function QueryState<T>({ query, loading, isEmpty, empty, children }: QueryStateProps<T>) {
  if (query.isPending) return loading;
  if (query.isError) return <ErrorState error={query.error} onRetry={() => void query.refetch()} />;
  if (isEmpty?.(query.data)) return empty;
  return children(query.data);
}
