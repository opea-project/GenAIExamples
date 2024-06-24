// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { RootState } from "../store";
import { User } from "./user";

const initialState: User = {
  name: localStorage.getItem("user"),
};

export const userSlice = createSlice({
  name: "user",
  initialState,
  reducers: {
    setUser: (state, action: PayloadAction<string>) => {
      state.name = action.payload;
    },
    removeUser: (state) => {
      state.name = null;
    },
  },
});
export const { setUser, removeUser } = userSlice.actions;
export const userSelector = (state: RootState) => state.userReducer;
export default userSlice.reducer;
