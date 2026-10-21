"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useId, useSyncExternalStore } from "react";

import {
  MOCK_SCENARIOS,
  readMockScenario,
  subscribeMockScenario,
  writeMockScenario,
  type MockScenario,
} from "@/lib/mocks/scenario";
import { cn } from "@/lib/utils";

const USE_MOCKS = process.env.NEXT_PUBLIC_USE_MOCKS !== "false";

/** Prototype-only control for reviewing each screen's loading, empty and error states. */
export function MockScenarioSwitcher() {
  const queryClient = useQueryClient();
  // The server renders "normal"; the browser then reads the saved choice without a hydration mismatch.
  const scenario = useSyncExternalStore(subscribeMockScenario, readMockScenario, () => "normal" as const);
  // The switcher renders in both the sidebar and the mobile drawer, so each radio group needs its own name.
  const groupName = useId();

  if (!USE_MOCKS) return null;

  function choose(next: MockScenario) {
    writeMockScenario(next);
    void queryClient.resetQueries();
  }

  return (
    <fieldset className="glass-inset p-3">
      <legend className="sr-only">Mock data scenario</legend>
      <p aria-hidden className="mb-2 text-[11px] font-medium tracking-wider text-subtle uppercase">
        Mock data
      </p>
      <div className="grid grid-cols-4 gap-1">
        {MOCK_SCENARIOS.map((option) => (
          <label
            key={option}
            className={cn(
              "cursor-pointer rounded-lg py-1 text-center text-[11px] capitalize transition-colors",
              "has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-accent",
              scenario === option ? "bg-accent-soft text-ink" : "text-muted hover:text-ink",
            )}
          >
            <input
              type="radio"
              name={groupName}
              value={option}
              checked={scenario === option}
              onChange={() => choose(option)}
              className="sr-only"
            />
            {option}
          </label>
        ))}
      </div>
    </fieldset>
  );
}
