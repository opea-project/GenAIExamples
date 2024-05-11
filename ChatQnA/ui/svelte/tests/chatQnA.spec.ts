// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { test, expect, type Page } from "@playwright/test";

test.beforeEach(async ({ page }) => {
	await page.goto("/");
});

const CHAT_ITEMS = ["What is the total revenue of Nike in 2023?"];

test.describe("New Chat", () => {
	test("should enter message to chat", async ({ page }) => {
		const newChat = page.getByPlaceholder("Enter prompt here");
		console.log("newChat", newChat);

		await newChat.fill(CHAT_ITEMS[0]);
		await newChat.press("Enter");

		// Wait for the result to appear on the page
		//  await page.waitForSelector('#msg-time', { timeout: 60000 });

		//  // Make sure the result is displayed as expected
		//  const msgContent = await page.$eval('#msg-time', (element) => element.textContent);
		//  expect(msgContent).toBeTruthy();
	});
});
