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
    successMsg: "Pipeline created successfully !",
  });
};

export const requestPipelineUpdate = (name: String, data: Object) => {
  return request({
    url: `/v1/settings/pipelines/${name}`,
    method: "patch",
    data,
    showLoading: true,
    showSuccessMsg: true,
    successMsg: "Pipeline update successfully !",
  });
};

export const requestPipelineDelete = (name: String) => {
  return request({
    url: `/v1/settings/pipelines/${name}`,
    method: "delete",
    showLoading: true,
    showSuccessMsg: true,
    successMsg: "Pipeline deleted successfully !",
  });
};

export const requestPipelineSwitchState = (name: String, data: Object) => {
  return request({
    url: `/v1/settings/pipelines/${name}`,
    method: "patch",
    data,
    showLoading: true,
    showSuccessMsg: true,
    successMsg: "Pipeline state switch successful !",
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
