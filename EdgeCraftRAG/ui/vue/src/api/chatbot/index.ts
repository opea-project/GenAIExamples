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

export const getBenchmark = () => {
  return request({
    url: `/v1/settings/pipeline/benchmark`,
    method: "get",
  });
};

export const getHistorySessionList = () => {
  return request({
    url: "/v1/sessions",
    method: "get",
  });
};

export const getSessionDetailById = (SessionId: String) => {
  return request({
    url: `v1/session/${SessionId}`,
    method: "get",
  });
};

export const requestSessionDelete = (SessionId: String) => {
  return request({
    url: `/v1/session/${SessionId}`,
    method: "delete",
    showLoading: true,
    showSuccessMsg: true,
    successMsg: "request.knowledge.deleteSucc",
  });
};
