// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import request from "../request";

export const getSystemStatus = () => {
  return request({
    url: "/v1/system/info",
    method: "get",
  });
};

export const getPipelineList = () => {
  return request({
    url: "/v1/settings/pipelines",
    method: "get",
  });
};

export const getPipelineDetailByName = (name: String) => {
  return request({
    url: `/v1/settings/pipelines/${name}/json`,
    method: "get",
  });
};

export const requestPipelineCreate = (data: Object) => {
  return request({
    url: "/v1/settings/pipelines",
    method: "post",
    data,
    showLoading: true,
    showSuccessMsg: true,
    successMsg: "request.pipeline.createSucc",
  });
};

export const requestPipelineUpdate = (name: String, data: Object) => {
  return request({
    url: `/v1/settings/pipelines/${name}`,
    method: "patch",
    data,
    showLoading: true,
    showSuccessMsg: true,
    successMsg: "request.pipeline.updateSucc",
  });
};

export const requestPipelineDelete = (name: String) => {
  return request({
    url: `/v1/settings/pipelines/${name}`,
    method: "delete",
    showLoading: true,
    showSuccessMsg: true,
    successMsg: "request.pipeline.deleteSucc",
  });
};

export const requestPipelineSwitchState = (name: String, data: Object) => {
  return request({
    url: `/v1/settings/pipelines/${name}`,
    method: "patch",
    data,
    showLoading: true,
    showSuccessMsg: true,
    successMsg: "request.pipeline.switchSucc",
  });
};

export const getRunDevice = () => {
  return request({
    url: "/v1/system/device",
    method: "get",
  });
};

export const getModelList = (type: string, params?: Object) => {
  return request({
    url: `/v1/settings/avail-models/${type}`,
    method: "get",
    params,
  });
};

export const getModelWeight = (model_id: string) => {
  return request({
    url: `/v1/settings/weight/${model_id}`,
    method: "get",
  });
};

export const requestUrlVerify = (data: Object) => {
  return request({
    url: "/v1/check/milvus",
    method: "post",
    data,
    showLoading: true,
  });
};

export const requestUrlVllm = (data: Object) => {
  return request({
    url: "/v1/check/vllm",
    method: "post",
    data,
    showLoading: true,
  });
};

export const importUrl = `${import.meta.env.VITE_API_URL}v1/settings/pipelines/import`;
