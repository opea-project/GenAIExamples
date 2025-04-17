// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

export interface ErrorResponse {
  response?: {
    data?: {
      error?: {
        message?: string;
      };
    };
  };
  message: string;
}
