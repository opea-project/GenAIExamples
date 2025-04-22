// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

export interface UseCase {
  use_case: string;
  display_name: string;
  access_level: string;
}

export interface Model {
  displayName: string;
  endpoint?: string;
  maxToken: number;
  minToken: number;
  model_name: string;
  types: string[];
}

export type ConversationRequest = {
  conversationId: string;
  userPrompt: Message;
  messages: Message[];
  model: string;
  temperature: number;
  token: number;
  files?: any[];
  time?: string;
  type: string;
};

export type CodeRequest = {
  conversationId: string;
  userPrompt: Message;
  messages: any[];
  model: string;
  type: string;
  token?: number;
  temperature?: number;
};

export type SummaryFaqRequest = {
  conversationId: string;
  userPrompt: Message;
  messages: Message[] | string;
  files?: any[];
  model: string;
  temperature: number;
  token: number;
  type: string;
};

export enum MessageRole {
  Assistant = "assistant",
  User = "user",
  System = "system",
}

export interface Message {
  message_id?: string;
  role: MessageRole;
  content: string;
  time?: string;
}

export interface ChatMessageProps {
  message: Message;
  pending?: boolean;
}

export interface Conversation {
  id: string;
  first_query?: string;
}

export type file = {
  name: string;
  id: string;
  type: string;
  parent: string;
};

export interface ConversationReducer {
  selectedConversationId: string;
  conversations: Conversation[];
  sharedConversations: Conversation[];
  selectedConversationHistory: Message[];
  onGoingResult: string;
  isPending: boolean;
  filesInDataSource: file[];
  dataSourceUrlStatus: string;

  useCase: string;
  useCases: UseCase[];
  model: string;
  models: Model[];
  type: string;
  types: any[];
  systemPrompt: string;
  minToken: number;
  maxToken: number;
  token: number;
  minTemperature: number;
  maxTemperature: number;
  temperature: number;
  sourceType: string;
  sourceLinks: string[];
  sourceFiles: any[];

  abortController: AbortController | null;

  uploadInProgress: boolean;
}
