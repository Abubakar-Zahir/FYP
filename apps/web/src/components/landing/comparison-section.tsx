import { Check, Minus } from "lucide-react";

import { APP_NAME } from "@/components/layout/nav-items";
import { cn } from "@/lib/utils";

import { SectionHeading } from "./section-heading";

type Cell = "yes" | "partly" | "no";

const COLUMNS = [APP_NAME, "AI chatbots", "Caption editors", "Schedulers"];

const ROWS: { feature: string; cells: Cell[] }[] = [
  { feature: "Breaks down why a reel worked", cells: ["yes", "no", "no", "no"] },
  { feature: "Scripts in your voice, in Roman Urdu", cells: ["yes", "partly", "no", "no"] },
  { feature: "Captions, silence cuts and B-roll", cells: ["yes", "no", "yes", "no"] },
  { feature: "Posts Trial Reel variants", cells: ["yes", "no", "no", "yes"] },
  { feature: "Picks the winner and learns from it", cells: ["yes", "no", "no", "no"] },
  { feature: "Comment themes in Roman Urdu", cells: ["yes", "partly", "no", "no"] },
];

function CellMark({ cell, highlight }: { cell: Cell; highlight: boolean }) {
  if (cell === "yes") {
    return (
      <span className={cn("grid size-6 place-items-center rounded-full", highlight ? "bg-cta text-white" : "bg-white/15 text-on-dark")}>
        <Check aria-label="Yes" className="size-3.5" />
      </span>
    );
  }
  if (cell === "partly") return <span className="text-xs text-on-dark-soft">Partly</span>;
  return <Minus aria-label="No" className="size-4 text-white/25" />;
}

export function ComparisonSection() {
  return (
    <section className="relative overflow-hidden bg-night px-4 py-24 sm:px-6 sm:py-32">
      <div aria-hidden className="absolute inset-0 bg-[radial-gradient(rgb(255_255_255/0.07)_0.9px,transparent_1.3px)] [background-size:18px_18px]" />
      <div
        aria-hidden
        className="absolute -top-40 left-1/2 h-[30rem] w-[60rem] -translate-x-1/2 bg-[radial-gradient(closest-side,rgb(255_79_174/0.4),rgb(228_87_196/0.15)_45%,transparent)] blur-2xl"
      />

      <div className="relative mx-auto max-w-[1180px]">
        <SectionHeading tone="dark" kicker={APP_NAME} title="Versus everything else." />

        <div className="reveal mx-auto mt-14 max-w-4xl overflow-x-auto rounded-3xl border border-white/10 bg-white/[0.04] backdrop-blur-sm">
          <table className="w-full min-w-[40rem] text-left text-sm">
            <thead>
              <tr className="border-b border-white/10">
                <th scope="col" className="p-5 font-medium text-on-dark-soft">
                  <span className="sr-only">Feature</span>
                </th>
                {COLUMNS.map((column, index) => (
                  <th
                    key={column}
                    scope="col"
                    className={cn("p-5 text-center font-semibold", index === 0 ? "text-accent-glow" : "text-on-dark-soft")}
                  >
                    {column}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {ROWS.map((row) => (
                <tr key={row.feature} className="border-b border-white/5 last:border-0">
                  <th scope="row" className="p-5 font-normal text-on-dark">
                    {row.feature}
                  </th>
                  {row.cells.map((cell, index) => (
                    <td key={index} className={cn("p-5", index === 0 && "bg-white/[0.04]")}>
                      <span className="flex justify-center">
                        <CellMark cell={cell} highlight={index === 0} />
                      </span>
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}
