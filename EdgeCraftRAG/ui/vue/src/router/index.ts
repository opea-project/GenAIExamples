// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { createRouter, createWebHashHistory } from "vue-router";
import { routeList, notFoundAndNoPower } from "./routes";

const router = createRouter({
  history: createWebHashHistory(),
  routes: [...notFoundAndNoPower, ...routeList],
});

export default router;
