// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import Layout from "@/layout/Main.vue";

export const routeList = [
  {
    path: "/",
    name: "Main",
    component: Layout,
    redirect: "/chatbot",
    children: [
      {
        path: "/settings",
        name: "Settings",
        component: () => import("@/views/settings/index.vue"),
        meta: { title: "Settings" },
      },
      {
        path: "/chatbot",
        name: "Chatbot",
        component: () => import("@/views/chatbot/index.vue"),
        meta: { title: "Chatbot" },
      },
    ],
  },
];

export const notFoundAndNoPower = [
  {
    path: "/:path(.*)*",
    name: "notFound",
    component: () => import("@/views/error/404.vue"),
    meta: {
      title: "404",
    },
  },
];
