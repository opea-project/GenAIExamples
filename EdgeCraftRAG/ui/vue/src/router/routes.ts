// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import Layout from "@/layout/Main.vue";

export const routeList = [
  {
    path: "/",
    name: "Main",
    component: Layout,
    redirect: "/rag",
    children: [
      {
        path: "/rag",
        name: "Rag",
        component: () => import("@/views/main/index.vue"),
        redirect: "/rag/chatbot",
        children: [
          {
            path: "/rag/pipeline",
            name: "Pipeline",
            component: () => import("@/views/pipeline/index.vue"),
            meta: { title: "Pipeline" },
          },
          {
            path: "/rag/chatbot",
            name: "Chatbot",
            component: () => import("@/views/chatbot/index.vue"),
            meta: { title: "Chatbot" },
          },
        ],
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
