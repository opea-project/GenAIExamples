// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import request from "../request";

export const getAgentList = () => {
  return request({
    url: "/v1/settings/agents",
    method: "get",
  });
};

export const getAgentDetailByName = (name: String) => {
  return request({
    url: `/v1/settings/agents/${name}`,
    method: "get",
  });
};
export const requestAgentCreate = (data: Object) => {
  return request({
    url: "/v1/settings/agents",
    method: "post",
    data,
    showLoading: true,
    showSuccessMsg: true,
    successMsg: "request.agent.createSucc",
  });
};
export const requestAgentUpdate = (name: String, data: Object) => {
  return request({
    url: `/v1/settings/agents/${name}`,
    method: "patch",
    data,
    showLoading: true,
    showSuccessMsg: true,
    successMsg: "request.agent.updateSucc",
  });
};

export const requestAgentDelete = (name: String) => {
  return request({
    url: `/v1/settings/agents/${name}`,
    method: "delete",
    showLoading: true,
    showSuccessMsg: true,
    successMsg: "request.agent.deleteSucc",
  });
};

export const getAgentConfigs = (type: String) => {
  return request({
    url: `/v1/settings/agents/configs/${type}`,
    method: "get",
  });
};
