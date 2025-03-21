// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import "axios";

// extend axios type
declare module "axios" {
  export interface AxiosResponse<T = any> {
    code: number;
    data: T;
    message: string;
    type?: string;
    showLoading?: boolean;
    showSuccessMsg?: boolean;
    successMsg?: string;
    [key: string]: T;
  }
  export interface AxiosRequestConfig<T = any> {
    [key: string]: T;
  }
}
