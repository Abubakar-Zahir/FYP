"use client";

import { FileChartColumn, Lightbulb, MessagesSquare, PenLine, TrendingDown, TrendingUp, type LucideIcon } from "lucide-react";

import { useWeeklyReport } from "@/lib/api/hooks";
import type { WeeklyReport } from "@/lib/api/types";
import { cn, formatShortDate } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { ButtonLink } from "@/components/ui/button";
import { CardHeader, GlassCard } from "@/components/ui/card";
import { EmptyState, LoadingBlock, QueryState } from "@/components/ui/states";

function OutcomeList({ title, items, icon: Icon, tone }: {
  title: string;
  items: WeeklyReport["wins"];
  icon: LucideIcon;
  tone: "success" | "danger";
}) {
  return (
    <GlassCard>
      <CardHeader title={title} />
      <ul className="space-y-3">
        {items.map((item) => (
          <li key={item.title} className="glass-inset flex gap-3 p-4">
            <span className={cn("grid size-8 shrink-0 place-items-center rounded-lg", tone === "success" ? "bg-success-soft text-success" : "bg-danger-soft text-danger")}>
              <Icon aria-hidden className="size-4" />
            </span>
            <div>
              <p className="font-medium">{item.title}</p>
              <p className="mt-0.5 text-sm text-muted">{item.detail}</p>
            </div>
          </li>
        ))}
      </ul>
    </GlassCard>
  );
}

function ReportBody({ report }: { report: WeeklyReport }) {
  return (
    <div className="space-y-4">
      <GlassCard className="bg-gradient-to-br from-accent/15 to-transparent">
        <p className="text-xs font-medium tracking-wider text-accent uppercase">Week of {formatShortDate(report.week_start)}</p>
        <p className="mt-2 text-xl font-semibold sm:text-2xl">{report.headline}</p>
        <div className="mt-4 flex flex-wrap gap-2">
          <MessagesSquare aria-hidden className="size-4 text-subtle" />
          {report.themes.map((theme) => (
            <Badge key={theme}>{theme}</Badge>
          ))}
        </div>
      </GlassCard>

      <div className="grid gap-4 lg:grid-cols-2">
        <OutcomeList title="Wins" items={report.wins} icon={TrendingUp} tone="success" />
        <OutcomeList title="Losses" items={report.losses} icon={TrendingDown} tone="danger" />
      </div>

      <GlassCard>
        <CardHeader title="5 ideas for next week" description="Ranked by expected impact for your account" />
        <ol className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {report.ideas.map((idea, index) => (
            <li key={idea.title} className="glass-inset flex flex-col gap-3 p-4">
              <div className="flex items-start gap-3">
                <span className="grid size-7 shrink-0 place-items-center rounded-lg bg-accent-soft text-xs font-bold text-accent">{index + 1}</span>
                <div>
                  <p className="font-medium">{idea.title}</p>
                  <p className="mt-1 flex items-center gap-1.5 text-xs text-subtle">
                    <Lightbulb aria-hidden className="size-3.5 text-warning" />
                    {idea.why}
                  </p>
                </div>
              </div>
              <ButtonLink href="/studio" variant="secondary" size="sm" className="mt-auto self-start">
                <PenLine aria-hidden />
                Script it
              </ButtonLink>
            </li>
          ))}
        </ol>
      </GlassCard>
    </div>
  );
}

export function WeeklyReportView() {
  const report = useWeeklyReport();

  return (
    <QueryState
      query={report}
      loading={<GlassCard><LoadingBlock label="Loading weekly report" /></GlassCard>}
      isEmpty={(data) => data.wins.length === 0 && data.losses.length === 0 && data.ideas.length === 0}
      empty={
        <GlassCard>
          <EmptyState icon={FileChartColumn} title="Your first report arrives Monday" description="We need one full week of posts and insights to write it." />
        </GlassCard>
      }
    >
      {(data) => <ReportBody report={data} />}
    </QueryState>
  );
}
