<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";

import { findModule } from "@/permissions";

const route = useRoute();
const current = computed(() => findModule(route.meta.module as string));
</script>

<template>
  <section class="placeholder-panel unavailable">
    <h2>{{ current?.title || "功能" }}暂未开放</h2>
    <p>
      当前第一版先保证教务管理、统计分析、系统工具和普通 AI 问答跑通。
      {{ current?.title || "该功能" }}完整业务能力暂缓开发，后续补齐时会接入真实接口和权限校验。
    </p>
    <RouterLink to="/dashboard">返回总览</RouterLink>
  </section>
</template>
