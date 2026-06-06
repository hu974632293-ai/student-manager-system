<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";

import { findModule } from "@/permissions";

const route = useRoute();
const current = computed(() => findModule(route.meta.module as string));
</script>

<template>
  <section class="placeholder-panel unavailable">
    <h2>{{ current?.title || "功能" }}未启用</h2>
    <p>
      当前角色暂时没有可用的{{ current?.title || "该功能" }}操作入口。可返回总览页查看已启用模块，或联系管理员确认账号权限配置。
    </p>
    <RouterLink to="/dashboard">返回总览</RouterLink>
  </section>
</template>
