//  Copyright (C) 2024 Intel Corporation
//  SPDX-License-Identifier: Apache-2.0

import { sveltekit } from "@sveltejs/kit/vite";
import type { UserConfig } from "vite";

const config: UserConfig = {
	plugins: [sveltekit()],
	server: {
		allowedHosts: true,
	},
};

export default config;
