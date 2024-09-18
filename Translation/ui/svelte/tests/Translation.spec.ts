// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { test, expect, type Page } from "@playwright/test";

// Initialization before each test
test.beforeEach(async ({ page }) => {
  await page.goto("/");
});

// Constants definition
const TRANSLATE_ITEMS = ["hello"];

// Helper function: Enter message to chat
async function enterMessageToChat(page: Page, message: string) {
  await page.getByTestId("translate-input").click();
  await page.getByTestId("translate-input").fill(message);
  await page.waitForTimeout(10000);
  const outputText = await page.getByTestId("translate-output").inputValue();
  console.log("Actual text:", outputText);
  await expect(page.getByTestId("translate-output")).not.toHaveValue("");
}

// Test description: New Doc Summary
test.describe("New Translation", () => {
  // Test: Enter message to summary
  test("should enter message to translate", async ({ page }) => {
    await enterMessageToChat(page, TRANSLATE_ITEMS[0]);
  });
});
