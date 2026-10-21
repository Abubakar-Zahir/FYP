"use client";

import { MessagesSquare } from "lucide-react";

import { useCommentSummary } from "@/lib/api/hooks";
import { formatCompact } from "@/lib/utils";
import { COMMENT_LABEL } from "@/lib/utils/labels";
import { CardHeader, GlassCard } from "@/components/ui/card";
import { EmptyState, LoadingBlock, QueryState } from "@/components/ui/states";

const BAR_COLOR = {
  accent: "bg-accent",
  success: "bg-success/80",
  warning: "bg-warning/80",
  danger: "bg-danger/80",
  neutral: "bg-subtle",
} as const;

export function CommentSummaryCard() {
  const summary = useCommentSummary();

  return (
    <GlassCard>
      <CardHeader title="Comment types" description="Last 30 days" />
      <QueryState
        query={summary}
        loading={<LoadingBlock label="Loading comment summary" />}
        isEmpty={(data) => data.total === 0}
        empty={<EmptyState icon={MessagesSquare} title="No comments yet" description="Sync comments to see what your audience is saying." />}
      >
        {(data) => (
          <>
            <p className="text-3xl font-semibold tabular-nums">{formatCompact(data.total)}</p>
            <p className="text-sm text-muted">comments classified</p>
            <ul className="mt-5 space-y-3">
              {data.by_label.map((item) => {
                const meta = COMMENT_LABEL[item.label];
                const share = item.count / data.total;
                return (
                  <li key={item.label}>
                    <div className="mb-1 flex justify-between text-sm">
                      <span>{meta.label}</span>
                      <span className="text-muted tabular-nums">
                        {item.count} <span className="text-subtle">· {Math.round(share * 100)}%</span>
                      </span>
                    </div>
                    <div className="h-1.5 overflow-hidden rounded-pill bg-surface-strong">
                      <div className={`h-full rounded-pill ${BAR_COLOR[meta.tone]}`} style={{ width: `${share * 100}%` }} />
                    </div>
                  </li>
                );
              })}
            </ul>
          </>
        )}
      </QueryState>
    </GlassCard>
  );
}
