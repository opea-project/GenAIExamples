<template>
  <div class="header-wrap">
    <img :height="36" :src="headerLog" />
    <div class="setting-wrap">
      <a-dropdown>
        <div @click.prevent>
          <div class="lang-icon">
            <SvgIcon
              class="iconfont"
              :name="
                currentLanguage === 'en_US' ? 'icon-lang-en' : 'icon-lang-zh'
              "
              :size="22"
            />
          </div>
        </div>
        <template #overlay>
          <a-menu @click="handleLanguageChange">
            <a-menu-item key="zh_CN" :disabled="currentLanguage === 'zh_CN'"
              >简体中文</a-menu-item
            >
            <a-menu-item key="en_US" :disabled="currentLanguage === 'en_US'"
              >English</a-menu-item
            >
          </a-menu>
        </template>
      </a-dropdown>
      <div class="theme-switch" @click="handleThemeChange">
        <div class="icon-wrap" :class="{ 'slider-on': isDark }">
          <img v-if="!isDark" :src="LightIcon" alt="Sun" class="icon" />
          <img v-else :src="DarkIcon" alt="Moon" class="icon" />
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup name="Header">
import DarkIcon from "@/assets/svgs/dark-icon.svg";
import headerLog from "@/assets/svgs/header-log.svg";
import LightIcon from "@/assets/svgs/light-icon.svg";
import SvgIcon from "@/components/SvgIcon.vue";
import { themeAppStore } from "@/store/theme";
import { useI18n } from "vue-i18n";

const { locale } = useI18n();
const themeStore = themeAppStore();
const emit = defineEmits(["change-theme"]);
const isDark = ref<boolean>(false);

const currentLanguage = computed(() => locale.value);
const handleLanguageChange = ({ key }: { key: string }) => {
  locale.value = key;
  themeStore.toggleLanguage(key);
};
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
@keyframes logoAnimation {
  0% {
    transform: scale(0);
  }
  80% {
    transform: scale(1.2);
  }
  100% {
    transform: scale(1);
  }
}
.header-wrap {
  max-width: 1440px;
  height: 64px;
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
.setting-wrap {
  .flex-end;
  gap: 12px;
  .lang-icon {
    cursor: pointer;
    position: relative;
    top: 3px;
    color: var(--font-tip-color);
    height: 24px;
    line-height: 24px;
    &:hover i {
      display: inline-block;
      animation: logoAnimation 0.3s ease-in-out;
    }
  }
}
</style>
