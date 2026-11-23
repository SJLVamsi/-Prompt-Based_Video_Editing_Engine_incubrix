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
