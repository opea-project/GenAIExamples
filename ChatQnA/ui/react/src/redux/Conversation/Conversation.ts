// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

export type ConversationRequest = {
  conversationId: string;
  userPrompt: Message;
  messages: Partial<Message>[];
  model: string;
};
export enum MessageRole {
  Assistant = "assistant",
  User = "user",
  System = "system",
}

export interface Message {
  role: MessageRole;
  content: string;
  time: number;
}

export interface Conversation {
  conversationId: string;
  title?: string;
  Messages: Message[];
}

type file = {
  name: string;
};

export interface ConversationReducer {
  selectedConversationId: string;
  conversations: Conversation[];
  onGoingResult: string;
  filesInDataSource: file[];
}
