// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import request from "../request";

export const getKnowledgeBaseList = () => {
  return request({
    url: "/v1/knowledge",
    method: "get",
  });
};

export const getKnowledgeBaseDetailByName = (kbName: String) => {
  return request({
    url: `/v1/knowledge/${kbName}`,
    method: "get",
  });
};

export const requestKnowledgeBaseCreate = (data: Object) => {
  return request({
    url: "/v1/knowledge",
    method: "post",
    data,
    showLoading: true,
    showSuccessMsg: true,
    successMsg: "request.knowledge.createSucc",
  });
};

export const requestKnowledgeBaseUpdate = (data: Object) => {
  return request({
    url: `/v1/knowledge/patch`,
    method: "patch",
    data,
    showLoading: true,
    showSuccessMsg: true,
    successMsg: "request.knowledge.updateSucc",
  });
};

export const requestKnowledgeBaseDelete = (kbName: String) => {
  return request({
    url: `/v1/knowledge/${kbName}`,
    method: "delete",
    showLoading: true,
    showSuccessMsg: true,
    successMsg: "request.knowledge.deleteSucc",
  });
};

export const requestKnowledgeBaseRelation = (kbName: String, data: Object) => {
  return request({
    url: `/v1/knowledge/${kbName}/files`,
    method: "post",
    data,
    showLoading: true,
    showSuccessMsg: true,
    successMsg: "request.knowledge.uploadSucc",
  });
};

export const requestFileDelete = (name: String, data: Object) => {
  return request({
    url: `/v1/knowledge/${name}/files`,
    method: "delete",
    data,
    showLoading: true,
    showSuccessMsg: true,
    successMsg: "request.knowledge.deleteFileSucc",
  });
};

export const getExperienceList = () => {
  return request({
    url: "/v1/experiences",
    method: "get",
  });
};

export const requestExperienceCreate = (data: EmptyArrayType) => {
  return request({
    url: "/v1/multiple_experiences/check",
    method: "post",
    data,
    showLoading: true,
  });
};
export const requestExperienceConfirm = (
  flag: Boolean,
  data: EmptyArrayType
) => {
  return request({
    url: `/v1/multiple_experiences/confirm?flag=${flag}`,
    method: "post",
    data,
    showLoading: true,
    showSuccessMsg: true,
    successMsg: "request.experience.createSucc",
  });
};
export const getExperienceDetailByName = (data: Object) => {
  return request({
    url: `/v1/experience`,
    method: "post",
    data,
  });
};

export const requestExperienceUpdate = (data: Object) => {
  return request({
    url: `/v1/experiences`,
    method: "patch",
    data,
    showLoading: true,
    showSuccessMsg: true,
    successMsg: "request.experience.updateSucc",
  });
};

export const requestExperienceDelete = (data: Object) => {
  return request({
    url: `/v1/experiences`,
    method: "delete",
    data,
    showLoading: true,
    showSuccessMsg: true,
    successMsg: "request.experience.deleteSucc",
  });
};

export const requestExperienceRelation = (data: Object) => {
  return request({
    url: "/v1/experiences/files",
    method: "post",
    data,
    showLoading: true,
    showSuccessMsg: true,
    successMsg: "experience.importSuccTip",
  });
};

export const uploadFileUrl = `${import.meta.env.VITE_API_URL}v1/data/file/`;
