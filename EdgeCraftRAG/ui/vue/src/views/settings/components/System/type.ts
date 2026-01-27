// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

export interface SystemType {
  cpuUsage: number;
  gpuUsage: number;
  diskUsage: number;
  memoryUsage: number;
  memoryUsed: string;
  memoryTotal: string;
  kernel: string;
  processor: string;
  os: string;
  currentTime: string;
}
