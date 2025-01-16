// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { writable } from "svelte/store";

let open = writable(false);

export { open };

export const displayedGoals = writable<string[]>([]);
export const currentMsgs = writable<{ [key: string]: string[] }>({});
