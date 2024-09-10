// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { createAsyncThunkWrapper } from "../thunkUtil";
import client from "../../common/client";
import { RootState } from "../store";
import { notifications } from "@mantine/notifications";
import { PROMPT_MANAGER_CREATE, PROMPT_MANAGER_GET } from "../../config";

type promptReducer = {
  prompts: Prompt[];
};

type Prompt = {
  id: string;
  prompt_text: string;
  user: string;
};

const initialState: promptReducer = {
  prompts: [],
};

export const PromptSlice = createSlice({
  name: "Prompts",
  initialState,
  reducers: {
    clearPrompts: (state) => {
      state.prompts = [];
    },
  },
  extraReducers(builder) {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    builder.addCase(getPrompts.fulfilled, (state, action: PayloadAction<any>) => {
      state.prompts = action.payload;
    });
    builder.addCase(addPrompt.fulfilled, () => {
      notifications.show({
        message: "Prompt added SuccessFully",
      });
    });
  },
});

export const { clearPrompts } = PromptSlice.actions;
export const promptSelector = (state: RootState) => state.promptReducer;
export default PromptSlice.reducer;

export const getPrompts = createAsyncThunkWrapper(
  "prompts/getPrompts",
  async ({ promptText }: { promptText: string | null }, { getState }) => {
    // @ts-ignore
    const state: RootState = getState();
    const response = await client.post(PROMPT_MANAGER_GET, {
      promptText: promptText,
      user: state.userReducer.name,
    });
    return response.data;
  },
);

export const addPrompt = createAsyncThunkWrapper(
  "prompts/addPrompt",
  async ({ promptText }: { promptText: string }, { getState }) => {
    // @ts-ignore
    const state: RootState = getState();
    const response = await client.post(PROMPT_MANAGER_CREATE, {
      prompt_text: promptText,
      user: state.userReducer.name,
    });
    return response.data;
  },
);
