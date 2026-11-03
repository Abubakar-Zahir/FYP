import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { ScoredHook } from "@/lib/api/types";

import { HookScoreCard } from "./hook-score-card";

const HOOK: ScoredHook = {
  text: "Kya ye hype ke qabil hai?",
  score: 84,
  top_factors: [
    { label: "Question hook", impact: 0.31 },
    { label: "Price cue", impact: 0.18 },
    { label: "Too long", impact: -0.06 },
  ],
};

describe("HookScoreCard", () => {
  it("shows the score next to the hook", () => {
    render(<HookScoreCard hook={HOOK} rank={1} />);

    expect(screen.getByText("84")).toBeInTheDocument();
    expect(screen.getByText(HOOK.text)).toBeInTheDocument();
  });

  it("always explains the score with its top 3 factors (NFR-10)", () => {
    render(<HookScoreCard hook={HOOK} rank={1} />);

    const factors = within(screen.getByRole("list", { name: "Top factors" })).getAllByRole("listitem");

    expect(factors).toHaveLength(3);
  });

  it("marks positive and negative factors", () => {
    render(<HookScoreCard hook={HOOK} rank={1} />);

    const factors = within(screen.getByRole("list", { name: "Top factors" })).getAllByRole("listitem");

    expect(factors[0]).toHaveTextContent("+ Question hook");
    expect(factors[2]).toHaveTextContent("− Too long");
  });

  it("lets Urdu text set its own direction", () => {
    render(<HookScoreCard hook={{ ...HOOK, text: "یہ کہاں ہے" }} rank={2} />);

    expect(screen.getByText("یہ کہاں ہے").closest("p")).toHaveAttribute("dir", "auto");
  });
});
