import { expect, test } from "@playwright/test";

/** Editor flow: load -> step frame -> split (C) -> undo. */
test("editor scrub / cut / undo", async ({ page }) => {
  await page.goto("/projects/demo");
  await expect(page.getByRole("heading", { name: "Project demo" })).toBeVisible();
  const tc = page.locator(".tc");
  await expect(tc).toContainText("00:00:00");
  await expect(page.locator(".clip")).toHaveCount(1);

  await page.keyboard.press("ArrowRight");
  await expect(tc).toContainText("00:00:01");

  await page.keyboard.press("c");
  await expect(page.locator(".clip")).toHaveCount(2);

  await page.getByRole("button", { name: "Undo" }).click();
  await expect(page.locator(".clip")).toHaveCount(1);
});

/** Prompt path: invalid input surfaces a clean error (no silent swallow). */
test("prompt invalid input shows error", async ({ page }) => {
  await page.goto("/projects/demo");
  // needs the API reachable via the proxy route (localhost:8000 in dev/CI)
  await page.getByLabel(/edit prompt/i).fill("not json at all");
  await page.getByRole("button", { name: /apply prompt/i }).click();
  await expect(page.getByRole("status")).toContainText(/error/i);
});

/** UAT: upload real video -> transcribe -> prompt -> preview link. */
test("UAT prompt workflow", async ({ page }) => {
  test.setTimeout(240000);
  await page.goto("/uat");
  await page.locator('input[type="file"]').setInputFiles("/tmp/uat/sample.mp4");
  await expect(page.getByRole("status")).toContainText(/uploaded/i, { timeout: 60000 });
  await page.getByRole("button", { name: /transcribe/i }).click();
  await expect(page.getByRole("status")).toContainText(/transcribed \d+ words/i, { timeout: 180000 });
  await page.getByRole("button", { name: /apply prompt/i }).click();
  await expect(page.getByRole("status")).toContainText(/done/i, { timeout: 180000 });
  await expect(page.locator("video")).toHaveAttribute("src", /\/api\/proxy\/exports\/.+\/download/);
});
