// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

console.log(import.meta.env.VITE_KEYCLOAK_SERVICE_ENDPOINT);
export const CHAT_QNA_URL = import.meta.env.VITE_BACKEND_SERVICE_ENDPOINT_CHATQNA;
export const CODE_GEN_URL = import.meta.env.VITE_BACKEND_SERVICE_ENDPOINT_CODEGEN;
export const DOC_SUM_URL = import.meta.env.VITE_BACKEND_SERVICE_ENDPOINT_DOCSUM;
export const FAQ_GEN_URL = import.meta.env.VITE_BACKEND_SERVICE_ENDPOINT_FAQGEN;
export const KEYCLOACK_SERVICE_URL = import.meta.env.VITE_KEYCLOAK_SERVICE_ENDPOINT;

export const DATA_PREP_URL = import.meta.env.VITE_DATAPREP_SERVICE_ENDPOINT;
export const DATA_PREP_GET_URL = import.meta.env.VITE_DATAPREP_GET_FILE_ENDPOINT;
export const DATA_PREP_DELETE_URL = import.meta.env.VITE_DATAPREP_DELETE_FILE_ENDPOINT;

export const CHAT_HISTORY_CREATE = import.meta.env.VITE_CHAT_HISTORY_CREATE_ENDPOINT;
export const CHAT_HISTORY_GET = import.meta.env.VITE_CHAT_HISTORY_GET_ENDPOINT;
export const CHAT_HISTORY_DELETE = import.meta.env.VITE_CHAT_HISTORY_DELETE_ENDPOINT;
export const PROMPT_MANAGER_GET = import.meta.env.VITE_PROMPT_SERVICE_GET_ENDPOINT;
export const PROMPT_MANAGER_CREATE = import.meta.env.VITE_PROMPT_SERVICE_CREATE_ENDPOINT;
