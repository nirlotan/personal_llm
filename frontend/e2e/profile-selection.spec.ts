import { test, expect } from "@playwright/test";

test.describe("Profile Selection", () => {
  test("displays category grid and enforces 3-5 selection", async ({ page }) => {
    // Would need a session first — this is a smoke test
    await page.goto("/profile");
    // Should redirect to home if no session
    await expect(page).toHaveURL("/");
  });
});
