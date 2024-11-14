// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { test, expect, type Page } from "@playwright/test";

// Initialization before each test
test.beforeEach(async ({ page }) => {
  await page.goto("/");
});

// Constants definition
const CHAT_ITEMS = ["What is the total revenue of Nike in 2023?"];
const placeholderText = "Upload or paste content on the left.";

// Helper function: Enter message to chat
async function enterMessageToChat(page: Page, message: string) {
  await page.getByTestId("sum-input").click();
  await page.getByTestId("sum-input").fill(message);
  await page.waitForTimeout(10000);
  await page.getByTestId("sum-click").click();
  await page.waitForTimeout(10000);
  await expect(page.getByTestId("display-answer")).not.toBeEmpty();
}

// Test description: New Doc Summary
test.describe("New Doc Summary", () => {
  // Test: Enter message to summary
  test("should enter message to summary", async ({ page }) => {
    await enterMessageToChat(page, CHAT_ITEMS[0]);
  });
});
