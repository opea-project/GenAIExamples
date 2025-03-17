import { defineStore } from "pinia";

export const pipelineAppStore = defineStore("pipeline", {
  state: () => ({
    activatedPipeline: "",
  }),
  persist: {
    key: "pipelineInfo",
    storage: localStorage,
  },
  actions: {
    setPipelineActivate(name: string) {
      this.activatedPipeline = name;
    },
  },
});
