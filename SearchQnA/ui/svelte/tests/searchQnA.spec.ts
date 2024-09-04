// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { test, expect, type Page } from "@playwright/test";

// Initialization before each test
test.beforeEach(async ({ page }) => {
	await page.goto("/");
});

// Constants definition
const CHAT_ITEMS = ["What is the total revenue of Nike in 2023?"];

// Helper function: Enter message to chat
async function enterMessageToChat(page: Page, message: string) {
	await page.getByTestId("chat-input").click();
	await page.getByTestId("chat-input").fill(message);
	await page.getByTestId("chat-input").press("Enter");
	await page.waitForTimeout(10000);
	await expect(page.getByTestId("display-answer")).toBeVisible();
}

// Test description: New Chat
test.describe("New Chat", () => {
	// Test: Enter message to chat
	test("should enter message to chat", async ({ page }) => {
		await enterMessageToChat(page, CHAT_ITEMS[0]);
	});
});
