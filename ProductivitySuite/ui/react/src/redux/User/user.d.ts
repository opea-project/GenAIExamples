// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

export interface User {
  name: string;
  isAuthenticated: boolean;
  role: "Admin" | "User";
}
