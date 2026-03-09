import { test, expect } from "@playwright/test";

test.describe("Chat Flow", () => {
  test("redirects to home without session", async ({ page }) => {
    await page.goto("/chat");
    await expect(page).toHaveURL("/");
  });
});
