// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { test, expect, type Page } from "@playwright/test";

test.beforeEach(async ({ page }) => {
	await page.goto("/");
});

const CHAT_ITEMS = ["What is the total revenue of Nike in 2023?"];
const UPLOAD_LINK = ["https://www.ces.tech/"];
const FILE_PATH = "./test_file.txt";

// Helper function to check notification text
async function checkNotificationText(page, expectedText) {
	const notificationText = await page.textContent(".notification");
	expect(notificationText).toContain(expectedText);
}

// Helper function to enter message to chat
async function enterMessageToChat(page, message) {
	const newChat = page.getByTestId("chat-input");
	await newChat.fill(message);
	await newChat.press("Enter");
	await expect(page.getByTestId("msg-time")).toBeVisible();
}

// Helper function to upload a file
async function uploadFile(page, filePath) {
	const fileUpload = page.getByTestId("file-upload");
	await fileUpload.setInputFiles(filePath);
	await checkNotificationText(page, "Uploaded successfully");
}

// Helper function to paste link
async function pasteLink(page, link) {
	const pasteLink = page.getByTestId("paste-link");
	await pasteLink.fill(link);
	const pasteClick = page.getByTestId("paste-click");
	await pasteClick.click();
	await checkNotificationText(page, "Uploaded successfully");
}

test.describe("New Chat", () => {
	// chat
	test("should enter message to chat", async ({ page }) => {
		await enterMessageToChat(page, CHAT_ITEMS[0]);
	});

	// clear chat
	test("should clear chat", async ({ page }) => {
		const clearChat = page.getByTestId("clear-chat");
		await clearChat.click();
	});
});

test.describe("Upload file and create new Chat", () => {
	// upload file
	test("should upload a file", async ({ page }) => {
		await uploadFile(page, FILE_PATH);
	});

	// paste link
	test("should paste link", async ({ page }) => {
		await pasteLink(page, UPLOAD_LINK[0]);
	});

	// chat with uploaded file and link
	test("should test uploaded chat", async ({ page }) => {
		await enterMessageToChat(page, CHAT_ITEMS[0]);
	});
});
