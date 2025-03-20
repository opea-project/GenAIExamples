// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import request from "../request";

export const getFilleList = () => {
  return request({
    url: "/v1/data/files",
    method: "get",
  });
};

export const requestChatbotConfig = (data: Object) => {
  return request({
    url: "/v1/settings/pipelines",
    method: "post",
    data,
    showLoading: true,
    showSuccessMsg: true,
    successMsg: "Configuration update successful !",
  });
};

export const requestFileDelete = (name: String) => {
  return request({
    url: `/v1/data/files/${name}`,
    method: "delete",
    showLoading: true,
    showSuccessMsg: true,
    successMsg: "File deleted successfully !",
  });
};

export const getBenchmark = (name: String) => {
  return request({
    url: `/v1/settings/pipelines/${name}/benchmark`,
    method: "get",
  });
};

export const requestParsingFiles = (data: Object) => {
  return request({
    url: `/v1/data`,
    method: "post",
    data,
    showLoading: true,
    showSuccessMsg: true,
    successMsg: "Document uploaded and parsed successfully !",
  });
};

export const uploadFileUrl = `${import.meta.env.VITE_API_URL}v1/data/file`;
