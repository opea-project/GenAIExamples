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
    successMsg: "request.chatbot.updateSucc",
  });
};

export const getBenchmark = (name: String) => {
  return request({
    url: `/v1/settings/pipelines/${name}/benchmark`,
    method: "get",
  });
};
