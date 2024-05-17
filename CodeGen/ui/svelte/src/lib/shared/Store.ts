// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { writable } from "svelte/store";

export let kb_id = writable("");

export let loading = writable(false);
