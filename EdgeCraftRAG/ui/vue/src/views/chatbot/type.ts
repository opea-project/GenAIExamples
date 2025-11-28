// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

export interface Benchmark {
  generator: string;
  postprocessor: string;
  retriever: string;
}
export interface IMessage {
  role: string;
  content: string;
  query?: string;
  errorMessage?: string;
  benchmark?: Benchmark | undefined;
}
export interface ThinkType {
  enable_thinking?: boolean;
  enable_rag_retrieval?: boolean;
}
export interface ConfigType {
  top_n: number;
  k: number;
  temperature: number;
  top_p: number;
  top_k: number;
  repetition_penalty: number;
  max_tokens: number;
  stream: boolean;
  chat_template_kwargs?: ThinkType;
}
