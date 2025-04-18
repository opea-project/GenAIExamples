// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { RootState } from "@redux/store";
import { User } from "./user";

const initialState: User = {
  name: "",
  isAuthenticated: false,
  role: "User",
};

export const userSlice = createSlice({
  name: "init user",
  initialState,
  reducers: {
    setUser: (state, action: PayloadAction<User>) => {
      state.name = action.payload.name;
      state.isAuthenticated = action.payload.isAuthenticated;
      state.role = action.payload.role;
    },
    removeUser: (state) => {
      state.name = "";
    },
  },
});
export const { setUser, removeUser } = userSlice.actions;
export const userSelector = (state: RootState) => state.userReducer;
export default userSlice.reducer;
