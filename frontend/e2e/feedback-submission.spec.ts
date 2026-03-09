import { test, expect } from "@playwright/test";

test.describe("Feedback Submission", () => {
  test("redirects to home without session", async ({ page }) => {
    await page.goto("/feedback");
    await expect(page).toHaveURL("/");
  });
});
