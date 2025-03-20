<template>
  <div class="header-wrap">
    <img :height="36" :src="headerLog" />
    <div class="header-title">
      <h1>{{ $t("headerTitle") }}</h1>
    </div>
    <div class="theme-switch" @click="handleThemeChange">
      <div class="icon-wrap" :class="{ 'slider-on': isDark }">
        <img v-if="!isDark" :src="LightIcon" alt="Sun" class="icon" />
        <img v-else :src="DarkIcon" alt="Moon" class="icon" />
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup name="Header">
import DarkIcon from "@/assets/svgs/dark-icon.svg";
import headerLog from "@/assets/svgs/header-log.svg";
import LightIcon from "@/assets/svgs/light-icon.svg";
import { themeAppStore } from "@/store/theme";

const themeStore = themeAppStore();
const emit = defineEmits(["change-theme"]);
const isDark = ref<boolean>(false);

const handleThemeChange = () => {
  isDark.value = !isDark.value;
  const theme = isDark.value ? "dark" : "light";
  const body = document.documentElement as HTMLElement;
  body.setAttribute("data-theme", theme);
  themeStore.toggleTheme(theme);
};
onMounted(() => {
  isDark.value = themeStore.theme === "dark";
});
</script>

<style scoped lang="less">
.header-wrap {
  max-width: 1440px;
  min-width: 960px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: var(--font-main-color);
  .header-title {
    font-family: var(--header-font-family);
  }
}
.theme-switch {
  position: relative;
  width: 50px;
  height: 24px;
  background-color: var(--color-switch-theme);
  border-radius: 15px;
  cursor: pointer;
  overflow: hidden;
}

.icon-wrap {
  position: absolute;
  top: 0;
  left: 0;
  width: 30px;
  height: 24px;
  border-radius: 50%;
  transition: transform 0.3s ease;
}

.slider-on {
  transform: translateX(20px);
}

.icon {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 20px;
  height: 20px;
  transition: opacity 0.3s ease;
}
</style>
