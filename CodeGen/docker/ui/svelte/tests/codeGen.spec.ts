// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { test, expect, type Page } from "@playwright/test";

// Initialization before each test
test.beforeEach(async ({ page }) => {
	await page.goto("/");
});

// Constants definition
const CHAT_ITEMS = [
	"Implement a high-level API for a TODO list application. The API takes as input an operation request and updates the TODO list in place. If the request is invalid, raise an exception.",
];

// Helper function: Enter message to chat
async function enterMessageToChat(page: Page, message: string) {
	await page.getByTestId("code-input").click();
	await page.getByTestId("code-input").fill(message);
	await page.getByTestId("code-input").press("Enter");
	await page.waitForTimeout(10000);
	await expect(page.getByTestId("code-output")).toContainText("copy");
}

// Test description: New Code Gen
test.describe("New Code Gen", () => {
	// Test: Enter message to summary
	test("should enter message to generate code gen", async ({ page }) => {
		await enterMessageToChat(page, CHAT_ITEMS[0]);
	});
});
