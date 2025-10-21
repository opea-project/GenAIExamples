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
	console.log("Starting to enter message:", message);

	await page.getByTestId("code-input").click();
	await page.getByTestId("code-input").fill(message);
	console.log("Message filled, pressing Enter...");

	await page.getByTestId("code-input").press("Enter");
	console.log("Enter pressed, waiting for response...");

	// Wait longer for the backend to respond and UI to update
	await page.waitForTimeout(30000);

	console.log("Checking for code-output element...");

	// First check if the output container exists
	const outputContainer = page.getByTestId("code-output");
	const isVisible = await outputContainer.isVisible({ timeout: 5000 });
	console.log("code-output container visible:", isVisible);

	if (!isVisible) {
		console.log("code-output container not found, taking screenshot...");
		await page.screenshot({ path: "no-output-container.png" });
		throw new Error("code-output container not found");
	}

	// Then check for the copy button within the container
	const copyButton = outputContainer.getByText("copy", { exact: false });
	const copyButtonVisible = await copyButton.isVisible({ timeout: 10000 });
	console.log("Copy button visible:", copyButtonVisible);

	if (!copyButtonVisible) {
		console.log("Copy button not found, taking screenshot...");
		await page.screenshot({ path: "no-copy-button.png" });
		// Get the content of the output container for debugging
		const outputContent = await outputContainer.textContent();
		console.log("Output container content:", outputContent);
		throw new Error("Copy button not found in code-output container");
	}

	console.log("Test completed successfully");
}

// Test description: New Code Gen
test.describe("New Code Gen", () => {
	// Test: Enter message to summary
	test("should enter message to generate code gen", async ({ page }) => {
		await enterMessageToChat(page, CHAT_ITEMS[0]);
	});
});
