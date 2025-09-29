<template>
  <div class="not-found">
    <img :src="notFound" alt="" class="not-found-icon" />
    <p>{{ $t("error.notFoundTip") }}</p>
    <a-button type="primary" size="large" @click="handleGoHome">
      <template #icon>
        <HomeFilled />
      </template>
      {{ $t("error.back") }}
    </a-button>
  </div>
</template>

<script lang="ts" setup name="404">
import notFound from "@/assets/svgs/404-icon.svg";
import router from "@/router";
import { HomeFilled } from "@ant-design/icons-vue";
import { h } from "vue";

const handleGoHome = () => {
  router.push("/");
};
</script>

<style scoped lang="less">
.not-found {
  width: 100%;
  height: 100vh;
  padding-top: 30vh;
  display: flex;
  align-items: center;
  flex-direction: column;
  gap: 16px;
  background-image: url("@/assets/images/404-bg.png");
  background-size: cover;
  background-repeat: no-repeat;
  background-position: center;
  color: #595959;
  .not-found-icon {
    margin-bottom: 16px;
  }
}
</style>
