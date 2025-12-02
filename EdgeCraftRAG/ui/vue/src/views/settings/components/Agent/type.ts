// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

export interface ModelType {
  model_id: string | undefined;
  model_path: string;
  model_url?: string;
  device: string;
  weight?: string;
}
