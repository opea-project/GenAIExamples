// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

const config = {
  companyName: "My Company",
  logo: "/logo512.png",
  tagline: "What can I help with?",
  disclaimer:
    "<p>Generative AI provides significant benefits for enhancing the productivity of quality engineers, production support teams, software developers, and DevOps professionals. With a secure and scalable toolbox, it offers a flexible architecture capable of connecting to various data sources and models, enabling it to address a wide range of Generative AI use cases.</p><p>This platform saves your user ID to retain chat history, which you can choose to delete from the app at any time.</p>",
  // defaultSummaryPrompt: `You are a professional summarizer good at summarizing documents. Provide a detailed summary of all documents while adhering to these guidelines:
  // 1. Do not repeat similar information in the summary and use a formal tone
  // 2. Format the summary in bullet form for easy understanding.`,
  defaultChatPrompt: `You are a helpful assistant`,
};

export default config;

export const CHAT_QNA_URL = import.meta.env.VITE_BACKEND_SERVICE_ENDPOINT_CHATQNA;
export const CODE_GEN_URL = import.meta.env.VITE_BACKEND_SERVICE_ENDPOINT_CODEGEN;
export const DOC_SUM_URL = import.meta.env.VITE_BACKEND_SERVICE_ENDPOINT_DOCSUM;
export const FAQ_GEN_URL = import.meta.env.VITE_BACKEND_SERVICE_ENDPOINT_FAQGEN;
export const KEYCLOAK_SERVICE_URL = import.meta.env.VITE_KEYCLOAK_SERVICE_ENDPOINT;

export const DATA_PREP_URL = import.meta.env.VITE_DATAPREP_SERVICE_ENDPOINT;
export const DATA_PREP_GET_URL = import.meta.env.VITE_DATAPREP_GET_FILE_ENDPOINT;
export const DATA_PREP_DELETE_URL = import.meta.env.VITE_DATAPREP_DELETE_FILE_ENDPOINT;

export const CHAT_HISTORY_CREATE = import.meta.env.VITE_CHAT_HISTORY_CREATE_ENDPOINT;
export const CHAT_HISTORY_GET = import.meta.env.VITE_CHAT_HISTORY_GET_ENDPOINT;
export const CHAT_HISTORY_DELETE = import.meta.env.VITE_CHAT_HISTORY_DELETE_ENDPOINT;

export const PROMPT_MANAGER_GET = import.meta.env.VITE_PROMPT_SERVICE_GET_ENDPOINT;
export const PROMPT_MANAGER_CREATE = import.meta.env.VITE_PROMPT_SERVICE_CREATE_ENDPOINT;
export const PROMPT_MANAGER_DELETE = import.meta.env.VITE_PROMPT_SERVICE_DELETE_ENDPOINT;
