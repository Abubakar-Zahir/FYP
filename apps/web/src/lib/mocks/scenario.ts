/*
 * Lets reviewers force every screen into its loading, empty or error state
 * (frontend.md, "Prototype done when" 4). Read by the MSW handlers, which run
 * in the page's main thread, so localStorage is available.
 */

export const MOCK_SCENARIOS = ["normal", "slow", "empty", "error"] as const;

export type MockScenario = (typeof MOCK_SCENARIOS)[number];

const STORAGE_KEY = "fyp.mock-scenario";

function isMockScenario(value: string | null): value is MockScenario {
  return MOCK_SCENARIOS.some((scenario) => scenario === value);
}

export function readMockScenario(): MockScenario {
  try {
    const stored = window.localStorage.getItem(STORAGE_KEY);
    return isMockScenario(stored) ? stored : "normal";
  } catch {
    return "normal";
  }
}

export function writeMockScenario(scenario: MockScenario): void {
  try {
    window.localStorage.setItem(STORAGE_KEY, scenario);
  } catch {
    // Storage can be blocked (private mode). The switch then lasts for this page view only.
  }
}
