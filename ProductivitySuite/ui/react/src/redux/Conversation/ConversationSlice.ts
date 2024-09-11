// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { PayloadAction, createSlice } from "@reduxjs/toolkit";
import { RootState, store } from "../store";
import { fetchEventSource } from "@microsoft/fetch-event-source";
import { Message, MessageRole, ConversationReducer, ConversationRequest, Conversation } from "./Conversation";
import { getCurrentTimeStamp } from "../../common/util";
import { createAsyncThunkWrapper } from "../thunkUtil";
import client from "../../common/client";
import { notifications } from "@mantine/notifications";
import {
  CHAT_QNA_URL,
  DATA_PREP_URL,
  DATA_PREP_GET_URL,
  DATA_PREP_DELETE_URL,
  CHAT_HISTORY_CREATE,
  CHAT_HISTORY_GET,
  CHAT_HISTORY_DELETE,
} from "../../config";

const initialState: ConversationReducer = {
  conversations: [],
  selectedConversationId: "",
  selectedConversationHistory: [],
  onGoingResult: "",
  filesInDataSource: [],
  model: "Intel/neural-chat-7b-v3-3",
  systemPrompt: "You are helpful assistant",
  minToken: 100,
  maxToken: 1000,
  token: 100,
  minTemperature: 0,
  maxTemperature: 1,
  temperature: 0.4,
};

export const ConversationSlice = createSlice({
  name: "Conversation",
  initialState,
  reducers: {
    logout: (state) => {
      state.conversations = [];
      state.selectedConversationId = "";
      state.onGoingResult = "";
      state.selectedConversationHistory = [];
      state.filesInDataSource = [];
    },

    setOnGoingResult: (state, action: PayloadAction<string>) => {
      state.onGoingResult = action.payload;
    },
    addMessageToMessages: (state, action: PayloadAction<Message>) => {
      state.selectedConversationHistory.push(action.payload);
    },
    newConversation: (state) => {
      (state.selectedConversationId = ""), (state.onGoingResult = ""), (state.selectedConversationHistory = []);
    },
    setSelectedConversationId: (state, action: PayloadAction<string>) => {
      state.selectedConversationId = action.payload;
    },
    setTemperature: (state, action: PayloadAction<number>) => {
      state.temperature = action.payload;
    },
    setToken: (state, action: PayloadAction<number>) => {
      state.token = action.payload;
    },
    setSystemPrompt: (state, action: PayloadAction<string>) => {
      state.systemPrompt = action.payload;
    },
  },
  extraReducers(builder) {
    builder.addCase(uploadFile.fulfilled, () => {
      notifications.update({
        id: "upload-file",
        message: "File Uploaded Successfully",
        loading: false,
        autoClose: 3000,
      });
    });
    builder.addCase(uploadFile.rejected, () => {
      notifications.update({
        color: "red",
        id: "upload-file",
        message: "Failed to Upload file",
        loading: false,
      });
    });

    builder.addCase(submitDataSourceURL.fulfilled, () => {
      notifications.show({
        message: "Submitted Successfully",
      });
    });
    builder.addCase(submitDataSourceURL.rejected, () => {
      notifications.show({
        color: "red",
        message: "Submit Failed",
      });
    });

    builder.addCase(getAllConversations.fulfilled, (state, action) => {
      state.conversations = action.payload;
    });

    builder.addCase(getConversationHistory.fulfilled, (state, action) => {
      state.selectedConversationHistory = action.payload;
    });

    builder.addCase(saveConversationtoDatabase.fulfilled, (state, action) => {
      if (state.selectedConversationId == "") {
        state.selectedConversationId = action.payload;
        state.conversations.push({
          id: action.payload,
          first_query: state.selectedConversationHistory[1].content,
        });
      }
    });
    builder.addCase(getAllFilesInDataSource.fulfilled, (state, action) => {
      state.filesInDataSource = action.payload;
    });
    builder.addCase(deleteConversation.fulfilled, () => {
      notifications.show({
        message: "Conversation Deleted Successfully",
      });
    });
  },
});

export const submitDataSourceURL = createAsyncThunkWrapper(
  "conversation/submitDataSourceURL",
  async ({ link_list }: { link_list: string[] }, { dispatch }) => {
    const body = new FormData();
    body.append("link_list", JSON.stringify(link_list));
    const response = await client.post(DATA_PREP_URL, body);
    dispatch(getAllFilesInDataSource({ knowledgeBaseId: "default" }));
    return response.data;
  },
);

export const getAllFilesInDataSource = createAsyncThunkWrapper(
  "conversation/getAllFilesInDataSource",
  async ({ knowledgeBaseId }: { knowledgeBaseId: string }, {}) => {
    const body = {
      knowledge_base_id: knowledgeBaseId,
    };
    const response = await client.post(DATA_PREP_GET_URL, body);
    return response.data;
  },
);
export const uploadFile = createAsyncThunkWrapper(
  "conversation/uploadFile",
  async ({ file }: { file: File }, { dispatch }) => {
    const body = new FormData();
    body.append("files", file);

    notifications.show({
      id: "upload-file",
      message: "uploading File",
      loading: true,
    });
    const response = await client.post(DATA_PREP_URL, body);
    dispatch(getAllFilesInDataSource({ knowledgeBaseId: "default" }));
    return response.data;
  },
);

export const deleteInDataSource = createAsyncThunkWrapper(
  "conversation/deleteInDataSource",
  async ({ file }: { file: any }, { dispatch }) => {
    const response = await client.post(DATA_PREP_DELETE_URL, {
      file_path: file,
    });
    dispatch(getAllFilesInDataSource({ knowledgeBaseId: "default" }));
    return response.data;
  },
);

export const saveConversationtoDatabase = createAsyncThunkWrapper(
  "conversation/saveConversationtoDatabase",
  async ({ conversation }: { conversation: Conversation }, { getState }) => {
    // @ts-ignore
    const state: RootState = getState();
    const selectedConversationHistory = state.conversationReducer.selectedConversationHistory;
    const response = await client.post(CHAT_HISTORY_CREATE, {
      data: {
        user: state.userReducer.name,
        messages: selectedConversationHistory,
      },
      id: conversation.id == "" ? null : conversation.id,
      first_query: selectedConversationHistory[1].content,
    });
    return response.data;
  },
);

export const getAllConversations = createAsyncThunkWrapper(
  "conversation/getAllConversations",
  async ({ user }: { user: string }, {}) => {
    const response = await client.post(CHAT_HISTORY_GET, {
      user,
    });
    return response.data;
  },
);

export const getConversationHistory = createAsyncThunkWrapper(
  "conversation/getConversationHistory",
  async ({ user, conversationId }: { user: string; conversationId: string }, {}) => {
    const response = await client.post(CHAT_HISTORY_GET, {
      user,
      id: conversationId,
    });
    return response.data.messages;
  },
);

export const deleteConversation = createAsyncThunkWrapper(
  "conversation/delete",
  async ({ user, conversationId }: { user: string; conversationId: string }, { dispatch }) => {
    const response = await client.post(CHAT_HISTORY_DELETE, {
      user,
      id: conversationId,
    });

    dispatch(newConversation());
    dispatch(getAllConversations({ user }));
    return response.data;
  },
);

export const doConversation = (conversationRequest: ConversationRequest) => {
  const { conversationId, userPrompt, messages, model, token, temperature } = conversationRequest;
  store.dispatch(addMessageToMessages(messages[0]));
  store.dispatch(addMessageToMessages(userPrompt));
  const userPromptWithoutTime = {
    role: userPrompt.role,
    content: userPrompt.content,
  };
  const body = {
    messages: [...messages, userPromptWithoutTime],
    model,
    max_new_tokens: token,
    temperature: temperature,
  };

  //   let conversation: Conversation;
  let result = "";
  try {
    fetchEventSource(CHAT_QNA_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
      openWhenHidden: true,
      async onopen(response) {
        if (response.ok) {
          return;
        } else if (response.status >= 400 && response.status < 500 && response.status !== 429) {
          const e = await response.json();
          console.log(e);
          throw Error(e.error.message);
        } else {
          console.log("error", response);
        }
      },
      onmessage(msg) {
        if (msg?.data != "[DONE]") {
          try {
            const match = msg.data.match(/b'([^']*)'/);
            if (match && match[1] != "</s>") {
              const extractedText = match[1];
              result += extractedText;
              store.dispatch(setOnGoingResult(result));
            }
          } catch (e) {
            console.log("something wrong in msg", e);
            throw e;
          }
        }
      },
      onerror(err) {
        console.log("error", err);
        store.dispatch(setOnGoingResult(""));
        //notify here
        throw err;
        //handle error
      },
      onclose() {
        //handle close
        const m: Message = {
          role: MessageRole.Assistant,
          content: result,
          time: getCurrentTimeStamp().toString(),
        };
        store.dispatch(setOnGoingResult(""));

        store.dispatch(addMessageToMessages(m));

        store.dispatch(
          saveConversationtoDatabase({
            conversation: {
              id: conversationId,
            },
          }),
        );
      },
    });
  } catch (err) {
    console.log(err);
  }
};

export const {
  logout,
  setOnGoingResult,
  newConversation,
  addMessageToMessages,
  setSelectedConversationId,
  setTemperature,
  setToken,
  setSystemPrompt,
} = ConversationSlice.actions;
export const conversationSelector = (state: RootState) => state.conversationReducer;
export default ConversationSlice.reducer;
