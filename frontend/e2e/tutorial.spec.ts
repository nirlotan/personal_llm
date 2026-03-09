import { test, expect } from "@playwright/test";

test.describe("Tutorial / Consent Page", () => {
  test("shows experiment description and Start button", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("heading", { name: /personal chat experiment/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /start/i })).toBeVisible();
  });

  test("Start button navigates to profile page", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("button", { name: /start/i }).click();
    await expect(page).toHaveURL(/\/profile/);
  });
});
