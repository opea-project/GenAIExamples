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

// export const DATA_PREP_GET_URL = "http://10.223.24.231:6007/v1/dataprep/get_file";

// export const DATA_PREP_URL = "http://10.223.24.231:6007/v1/dataprep";
// export const DATA_PREP_DELETE_URL = "http://10.223.24.231:6007/v1/dataprep/delete_file";

// export const CHAT_HISTORY_CREATE = "http://10.223.24.231:6012/v1/chathistory/create";
// export const CHAT_HISTORY_GET = "http://10.223.24.231:6012/v1/chathistory/get";
// export const CHAT_HISTORY_DELETE = "http://10.223.24.231:6012/v1/chathistory/delete";

// export const CHAT_QNA_URL = "http://10.223.24.231:8888/v1/chatqna";
// export const CODE_GEN_URL = "http://10.223.24.231:7778/v1/codegen";
// export const DOC_SUM_URL = "http://10.223.24.231:8890/v1/docsum";
// export const FAQ_GEN_URL = "http://10.223.24.231:8889/v1/faqgen";
// export const PROMPT_MANAGER_GET = "http://10.223.24.231:6015/v1/prompt/get";
// export const PROMPT_MANAGER_CREATE = "http://10.223.24.231:6015/v1/prompt/create";
