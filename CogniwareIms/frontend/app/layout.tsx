// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "OPEA IMS - Cogniware Inventory Management",
  description:
    "AI-Powered Inventory Management System built with OPEA GenAI Components",
  keywords: "OPEA, AI, Inventory Management, GenAI, Intel, Enterprise AI",
  authors: [{ name: "Cogniware" }],
  icons: {
    icon: "/images/opea-stacked-logo-rwd.png",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </head>
      <body className="antialiased">{children}</body>
    </html>
  );
}
