// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { createAsyncThunkWrapper } from "@redux/thunkUtil";
import { RootState } from "@redux/store";
import { PROMPT_MANAGER_CREATE, PROMPT_MANAGER_GET, PROMPT_MANAGER_DELETE } from "@root/config";
import { NotificationSeverity, notify } from "@components/Notification/Notification";
import axios from "axios";

type promptReducer = {
  prompts: Prompt[];
};

export type Prompt = {
  id: string;
  prompt_text: string;
  user: string;
  type: string;
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
    builder.addCase(getPrompts.fulfilled, (state, action: PayloadAction<any>) => {
      state.prompts = action.payload;
    });
    builder.addCase(addPrompt.fulfilled, () => {
      notify("Prompt added Successfully", NotificationSeverity.SUCCESS);
    });
    builder.addCase(deletePrompt.fulfilled, () => {
      notify("Prompt deleted Successfully", NotificationSeverity.SUCCESS);
    });
  },
});

export const { clearPrompts } = PromptSlice.actions;
export const promptSelector = (state: RootState) => state.promptReducer;
export default PromptSlice.reducer;

export const getPrompts = createAsyncThunkWrapper("prompts/getPrompts", async (_: void, { getState }) => {
  // @ts-ignore
  const state: RootState = getState();
  const response = await axios.post(PROMPT_MANAGER_GET, {
    user: state.userReducer.name,
  });
  return response.data;
});

export const addPrompt = createAsyncThunkWrapper(
  "prompts/addPrompt",
  async ({ promptText }: { promptText: string }, { dispatch, getState }) => {
    // @ts-ignore
    const state: RootState = getState();
    const response = await axios.post(PROMPT_MANAGER_CREATE, {
      prompt_text: promptText,
      user: state.userReducer.name,
      //TODO: Would be nice to support type to set prompts for each
      // type: state.conversationReducer.type // TODO: this might be crashing chatqna endpoint?
    });

    dispatch(getPrompts());

    return response.data;
  },
);

//TODO delete prompt doesn't actually work, but responds 200
export const deletePrompt = createAsyncThunkWrapper(
  "prompts/deletePrompt",
  async ({ promptId, promptText }: { promptId: string; promptText: string }, { dispatch, getState }) => {
    // @ts-ignore
    const state: RootState = getState();
    const user = state.userReducer.name;

    const response = await axios.post(PROMPT_MANAGER_DELETE, {
      user: user,
      prompt_id: promptId,
      prompt_text: promptText,
    });

    dispatch(getPrompts());

    return response.data;
  },
);
