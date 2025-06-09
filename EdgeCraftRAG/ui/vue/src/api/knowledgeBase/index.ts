// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import request from "../request";

export const getKnowledgeBaseList = () => {
  return request({
    url: "/v1/knowledge",
    method: "get",
    showLoading: true,
  });
};

export const getKnowledgeBaseDetialById = (kbId: String) => {
  return request({
    url: `/v1/knowledge/${kbId}`,
    method: "get",
    showLoading: true,
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

export const requestKnowledgeBaseDelete = (kbId: String) => {
  return request({
    url: `/v1/knowledge/${kbId}`,
    method: "delete",
    showLoading: true,
    showSuccessMsg: true,
    successMsg: "request.knowledge.deleteSucc",
  });
};

export const requestKnowledgeBaseRelation = (kbId: String, data: Object) => {
  return request({
    url: `/v1/knowledge/${kbId}/files`,
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

export const uploadFileUrl = `${import.meta.env.VITE_API_URL}v1/data/file/`;
