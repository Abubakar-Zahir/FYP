import { expect, test } from "@playwright/test";

// The four flows from docs/frontend.md, against the MSW mocks.

test("onboarding saves the profile and reaches the dashboard", async ({ page }) => {
  await page.goto("/login");
  await page.getByRole("button", { name: "Continue with Google" }).click();
  await expect(page.getByRole("heading", { name: "Tell us about your content" })).toBeVisible();

  await page.getByLabel("Niche").fill("Lahore street food");
  await page.getByLabel("Tone").selectOption("Honest reviewer");
  await page.getByLabel("Goals for the next 2 months").fill("Grow to 20K followers");
  await page.getByRole("button", { name: "Connect with Instagram" }).click();

  // Instagram's callback page, then back to the form with the answers kept.
  await expect(page.getByText("@ayesha.eats.lahore", { exact: true }).first()).toBeVisible();
  await page.getByRole("link", { name: "Back to setup" }).click();
  await expect(page.getByLabel("Niche")).toHaveValue("Lahore street food");
  await expect(page.getByText("@ayesha.eats.lahore", { exact: true }).first()).toBeVisible();
  await page.getByRole("button", { name: "Save and go to dashboard" }).click();

  await expect(page.getByRole("heading", { name: "Dashboard", exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Recent reels" })).toBeVisible();
});

test("onboarding blocks an empty form", async ({ page }) => {
  await page.goto("/onboarding");

  await page.getByRole("button", { name: "Save and go to dashboard" }).click();

  await expect(page.getByText("Tell us your niche")).toBeVisible();
  await expect(page).toHaveURL(/\/onboarding$/);
});

test("script generation returns 5 scored hooks with reasons", async ({ page }) => {
  await page.goto("/studio");

  await page.getByLabel("Topic or rough idea").fill("gol gappay at Liberty");
  await page.getByRole("button", { name: "Generate script" }).click();

  await expect(page.getByRole("heading", { name: "5 hooks, scored" })).toBeVisible({ timeout: 20_000 });
  await expect(page.getByRole("list", { name: "Top factors" })).toHaveCount(5);
  await expect(page.getByRole("heading", { name: "Full script" })).toBeVisible();
});

test("publishing variants picks a winner with insights", async ({ page }) => {
  await page.goto("/variants");
  await expect(page.getByText("No insights yet")).toBeVisible();

  await page.getByRole("button", { name: "Publish as Trial Reels" }).click();

  await expect(page.getByRole("button", { name: "Share winner to followers" })).toBeVisible({ timeout: 20_000 });
  await expect(page.getByText("Winner", { exact: true })).toBeVisible();
  await expect(page.getByRole("table")).toContainText("15.9K");
});

test("comments page shows ranked themes in Roman Urdu", async ({ page }) => {
  await page.goto("/comments");

  await expect(page.getByRole("heading", { name: "Where is this place?" })).toBeVisible();
  await expect(page.getByText("Ye kahan hai exact location?")).toBeVisible();
  await expect(page.getByText("comments classified")).toBeVisible();
});

test("uploading a reference reel analyses it into the library", async ({ page }) => {
  await page.goto("/dna");
  await expect(page.getByRole("heading", { name: "DNA library" })).toBeVisible();

  await page.locator('input[type="file"]').setInputFiles({
    name: "gulberg-cafes.mp4",
    mimeType: "video/mp4",
    buffer: Buffer.from("not a real video, the mock only needs bytes"),
  });

  await expect(page.getByText("Analysing the reel's DNA")).toBeVisible();
  await expect(page.getByRole("link", { name: "gulberg-cafes" })).toBeVisible({ timeout: 20_000 });
});

test("a file that is not a video is refused before uploading", async ({ page }) => {
  await page.goto("/dna");

  await page.locator('input[type="file"]').setInputFiles({ name: "notes.txt", mimeType: "text/plain", buffer: Buffer.from("x") });

  await expect(page.getByText("Upload an MP4 or MOV video.")).toBeVisible();
});
