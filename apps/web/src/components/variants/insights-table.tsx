import { Trophy } from "lucide-react";

import type { Experiment, VariantInsight } from "@/lib/api/types";
import { cn, formatCompact } from "@/lib/utils";

const WINDOWS: VariantInsight["window"][] = ["24h", "72h"];

export function InsightsTable({ experiment }: { experiment: Experiment }) {
  return (
    <div className="-mx-2 overflow-x-auto">
      <table className="w-full min-w-[560px] text-left text-sm">
        <thead className="text-xs text-subtle">
          <tr>
            <th scope="col" className="px-2 pb-3 font-medium">Variant</th>
            <th scope="col" className="px-2 pb-3 font-medium">Window</th>
            <th scope="col" className="px-2 pb-3 text-right font-medium">Views</th>
            <th scope="col" className="px-2 pb-3 text-right font-medium">Reach</th>
            <th scope="col" className="px-2 pb-3 text-right font-medium">Saves</th>
            <th scope="col" className="px-2 pb-3 text-right font-medium">Shares</th>
          </tr>
        </thead>
        <tbody>
          {experiment.variants.flatMap((variant) =>
            WINDOWS.map((window) => {
              const insight = variant.insights.find((item) => item.window === window);
              const winner = variant.id === experiment.winner_variant_id;
              return (
                <tr key={`${variant.id}-${window}`} className={cn("border-t border-edge", winner && "bg-warning-soft/60")}>
                  {window === "24h" && (
                    <th scope="row" rowSpan={WINDOWS.length} className="px-2 py-2.5 align-top font-medium">
                      <span className="flex items-center gap-1.5">
                        {variant.label}
                        {winner && <Trophy aria-label="Winner" className="size-3.5 text-warning" />}
                      </span>
                    </th>
                  )}
                  <td className="px-2 py-2.5 text-muted">{window}</td>
                  <td className="px-2 py-2.5 text-right tabular-nums">{insight ? formatCompact(insight.views) : "—"}</td>
                  <td className="px-2 py-2.5 text-right tabular-nums">{insight ? formatCompact(insight.reach) : "—"}</td>
                  <td className="px-2 py-2.5 text-right tabular-nums">{insight ? formatCompact(insight.saves) : "—"}</td>
                  <td className="px-2 py-2.5 text-right tabular-nums">{insight ? formatCompact(insight.shares) : "—"}</td>
                </tr>
              );
            }),
          )}
        </tbody>
      </table>
    </div>
  );
}
