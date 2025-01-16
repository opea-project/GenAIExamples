// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { browser } from "$app/environment";
import { chats$, chatList$ } from "$lib/components/shared/shared.store";
import { LOCAL_STORAGE_KEY } from "$lib/components/shared/shared.type";

export const load = async () => {
	if (browser) {
		const chatList = localStorage.getItem(LOCAL_STORAGE_KEY.CHAT_LIST);

		// Chat list
		if (chatList) {
			const parsedChatList = JSON.parse(chatList);
			chatList$.set(parsedChatList);

			// Chats
			if (parsedChatList.length > 0) {
				parsedChatList.forEach((listItem: any) => {
					const chatId = listItem.chatId;
					// chats$ messages should already be present in localStorage, else ¯\_(ツ)_/¯
					const chat = localStorage.getItem(chatId);

					if (chat) {
						chats$.update((chats) => {
							return {
								...chats,
								[chatId]: JSON.parse(chat),
							};
						});
					}
				});
			}
		}
	}
};
