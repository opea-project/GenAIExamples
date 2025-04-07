// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { NextLoading } from "@/utils/loading";
import serviceManager from "@/utils/serviceManager";
import axios, { AxiosInstance } from "axios";
import qs from "qs";

const antNotification = serviceManager.getService("antNotification");

const service: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  timeout: 50000,
  headers: { "Content-Type": "application/json" },
});

// request interceptor
service.interceptors.request.use(
  (config) => {
    if (config.type === "formData") {
      config.data = qs.stringify(config.data);
    } else if (config.type === "files") {
      config.headers!["Content-Type"] = "multipart/form-data";
    }

    if (config.showLoading) NextLoading.start();
    return config;
  },
  (error) => {
    return Promise.reject(error);
  },
);

// response interceptor
service.interceptors.response.use(
  (response) => {
    const { config } = response;
    if (NextLoading) NextLoading.done();
    const res = response.data;
    if (config.showSuccessMsg) {
      if (antNotification) antNotification("success", "Success", config.successMsg);
    }
    return Promise.resolve(res);
  },
  (error) => {
    if (NextLoading) NextLoading.done();
    let errorMessage = "";
    const { detail = "" } = error.response?.data || {};
    if (error.message.indexOf("timeout") != -1) {
      errorMessage = "Timeout";
    } else if (detail) {
      errorMessage = detail;
    } else {
      errorMessage = error.message;
    }
    if (antNotification) antNotification("error", "Error", errorMessage);

    return Promise.reject(error);
  },
);

export default service;
