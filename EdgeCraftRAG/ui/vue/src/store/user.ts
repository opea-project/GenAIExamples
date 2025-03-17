import { defineStore } from "pinia";

export const userAppStore = defineStore("user", {
  state: () => ({
    userGuide: false,
  }),
  persist: {
    key: "userInfo",
    storage: localStorage,
  },
  actions: {
    setUserGuideState(state: boolean) {
      this.userGuide = state;
    },
  },
});
