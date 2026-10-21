"use client";

import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import type { TrendPoint } from "@/lib/api/types";
import { formatCompact, formatShortDate } from "@/lib/utils";

const AXIS_TICK = { fill: "var(--color-subtle)", fontSize: 12 };

const TOOLTIP_STYLE = {
  background: "rgb(20 16 38 / 0.85)",
  border: "1px solid var(--color-edge-strong)",
  borderRadius: 12,
  backdropFilter: "blur(12px)",
  color: "var(--color-ink)",
};

export function ViewsChart({ points }: { points: TrendPoint[] }) {
  return (
    <div className="h-64 w-full" role="img" aria-label={`Daily views over the last ${points.length} days`}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={points} margin={{ top: 8, right: 8, left: -12, bottom: 0 }}>
          <defs>
            <linearGradient id="views-fill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="var(--color-accent)" stopOpacity={0.45} />
              <stop offset="100%" stopColor="var(--color-accent)" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke="var(--color-edge)" strokeDasharray="3 6" vertical={false} />
          <XAxis
            dataKey="date"
            tickFormatter={formatShortDate}
            tick={AXIS_TICK}
            axisLine={false}
            tickLine={false}
            minTickGap={32}
          />
          <YAxis tickFormatter={formatCompact} tick={AXIS_TICK} axisLine={false} tickLine={false} width={48} />
          <Tooltip
            contentStyle={TOOLTIP_STYLE}
            labelStyle={{ color: "var(--color-muted)" }}
            itemStyle={{ color: "var(--color-ink)" }}
            labelFormatter={(label) => formatShortDate(String(label))}
            formatter={(value) => [formatCompact(Number(value)), "Views"]}
            cursor={{ stroke: "var(--color-edge-strong)" }}
          />
          <Area
            type="monotone"
            dataKey="views"
            stroke="var(--color-accent)"
            strokeWidth={2}
            fill="url(#views-fill)"
            activeDot={{ r: 4, fill: "var(--color-accent)", stroke: "var(--color-ink)" }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
