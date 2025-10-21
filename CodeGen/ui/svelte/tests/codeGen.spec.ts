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
	
	// Take screenshot before starting
	await page.screenshot({ path: "test-start.png" });
	
	await page.getByTestId("code-input").click();
	await page.getByTestId("code-input").fill(message);
	console.log("Message filled, pressing Enter...");

	await page.getByTestId("code-input").press("Enter");
	console.log("Enter pressed, waiting for response...");
	
	// Wait for network response to complete
	console.log("Waiting for network response...");
	await page.waitForResponse(response =>
		response.url().includes('/v1/codegen') &&
		response.status() !== 0,
		{ timeout: 60000 }
	);
	console.log("Network response received");
	
	// Wait for UI to update
	console.log("Waiting for UI to update...");
	await page.waitForTimeout(15000);
	
	console.log("Checking for code-output element...");

	// First check if the output container exists
	const outputContainer = page.getByTestId("code-output");
	const isVisible = await outputContainer.isVisible({ timeout: 10000 });
	console.log("code-output container visible:", isVisible);

	if (!isVisible) {
		console.log("code-output container not found, taking screenshot...");
		await page.screenshot({ path: "no-output-container.png" });
		
		// Check if there are any error messages
		const errorMessages = await page.locator('.error, .alert, [role="alert"]').allTextContents();
		if (errorMessages.length > 0) {
			console.log("Error messages found:", errorMessages);
		}
		
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
		
		// Check if there are any loading indicators
		const loadingIndicators = await page.locator('.loading, .spinner, [role="progressbar"]').allTextContents();
		if (loadingIndicators.length > 0) {
			console.log("Loading indicators found:", loadingIndicators);
		}
		
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
