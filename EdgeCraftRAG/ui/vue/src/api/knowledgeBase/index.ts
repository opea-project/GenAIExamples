// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import request from "../request";

export const getKnowledgeBaseList = () => {
  return request({
    url: "/v1/knowledge",
    method: "get",
  });
};

export const getKnowledgeBaseDetialByName = (kbName: String) => {
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

export const requestFileDelete = (kbName: String, data: Object) => {
  return request({
    url: `/v1/knowledge/${kbName}/files`,
    method: "delete",
    data,
    showLoading: true,
    showSuccessMsg: true,
    successMsg: "request.knowledge.deleteFileSucc",
  });
};

export const uploadFileUrl = `${import.meta.env.VITE_API_URL}v1/data/file/`;
