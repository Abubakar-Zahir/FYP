import { expect, test } from "@playwright/test";

// "Prototype done when" checks from docs/frontend.md: every screen fits 375 px and 1280 px,
// and has empty and error states.

const SCREENS = ["/", "/login", "/onboarding", "/dashboard", "/dna", "/dna/dna_01", "/studio", "/editor", "/variants", "/comments", "/reports"];
const WIDTHS = [375, 1280];
const SCENARIO_KEY = "fyp.mock-scenario";
const WALK_ALL_SCREENS_TIMEOUT_MS = 120_000;

for (const width of WIDTHS) {
  test(`no screen scrolls sideways at ${width} px`, async ({ page }) => {
    test.setTimeout(WALK_ALL_SCREENS_TIMEOUT_MS);
    await page.setViewportSize({ width, height: 800 });
    for (const path of SCREENS) {
      // Retried because MSW can reload a page if its worker is not yet in control, which
      // interrupts the check. Waits for network idle so wide content has loaded before measuring.
      await expect(async () => {
        await page.goto(path);
        await page.waitForLoadState("networkidle");
        const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
        expect(overflow, `${path} overflows by ${overflow}px`).toBeLessThanOrEqual(0);
      }).toPass({ timeout: 30_000 });
    }
  });
}

test("the error scenario shows a retry instead of breaking the page", async ({ page }) => {
  await page.addInitScript((key) => window.localStorage.setItem(key, "error"), SCENARIO_KEY);
  await page.goto("/dna");

  await expect(page.getByText("Something went wrong")).toBeVisible({ timeout: 15_000 });
  await expect(page.getByRole("button", { name: "Try again" })).toBeVisible();
});

test("the empty scenario explains what to do next", async ({ page }) => {
  await page.addInitScript((key) => window.localStorage.setItem(key, "empty"), SCENARIO_KEY);
  await page.goto("/dna");

  await expect(page.getByText("No reels analysed yet")).toBeVisible();
});

test("the landing page leads to sign in", async ({ page }) => {
  await page.goto("/");

  await page.getByRole("link", { name: "Apply for the pilot" }).click();

  await expect(page).toHaveURL(/\/login$/);
});
