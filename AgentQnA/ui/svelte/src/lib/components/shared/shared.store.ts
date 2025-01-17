// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { derived, writable } from "svelte/store";

import type { Chat, ChatListItem } from "./shared.type";

/**
 * Banners
 */
export const banners$ = writable([] as any);

export const hasBanners$ = derived(banners$, (banners) => {
	return banners.length > 0;
});

/**
 * localStorage
 */
export const chatList$ = writable([] as ChatListItem[]);
export const chats$ = writable({} as Record<string, Chat>);
export const knowledge_base_id = writable("" as string);
export const storageFiles = writable([]);
export const admin$ = writable("" as string);

export const parentPath = writable("" as string);
export const parentIdx = writable(-1 as number);

export const hintStart = writable(false as boolean);
export const hintEnd = writable({ status: false, hintContent: "" });
export const netError = writable(false as boolean);

export const needRecreate = writable(false as boolean);
export const displayHintRecreate = writable(false as boolean);
