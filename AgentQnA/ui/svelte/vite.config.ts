// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { sveltekit } from "@sveltejs/kit/vite";
import type { UserConfig } from "vite";

const config: UserConfig = {
	plugins: [sveltekit()],
	server: {
		proxy: {
			"/api": {
				target: "http://10.112.228.168:8000",
				changeOrigin: true,
				secure: true,
				rewrite: (path) => path.replace(/^\/api/, ""),
			},
		},
	},
};

export default config;
