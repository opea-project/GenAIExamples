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
    showLoading: true,
  });
};

export const getPipelineDetialByName = (name: String) => {
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

export const getModelList = (type: string) => {
  return request({
    url: `/v1/settings/avail-models/${type}`,
    method: "get",
  });
};

export const getModelWeight = (model_id: string) => {
  return request({
    url: `/v1/settings/weight/${model_id}`,
    method: "get",
  });
};

export const importUrl = `${import.meta.env.VITE_API_URL}v1/settings/pipelines/import`;
