<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";

import { modules } from "@/permissions";

const route = useRoute();
const current = computed(() => modules.find((item) => item.key === route.meta.module));
</script>

<template>
  <section class="ai-workbench">
    <aside class="workbench-side">
      <h3>{{ current?.title }}</h3>
      <p>{{ current?.subtitle }}</p>
    </aside>
    <main class="placeholder-panel">
      <h2>{{ current?.title }}工作台</h2>
      <p>前端路由、菜单权限和页面结构已就位，等待后端具体接口接入。</p>
    </main>
    <aside class="workbench-side">
      <h3>权限</h3>
      <p>页面入口由 Vue Router 守卫控制，接口仍由后端角色依赖兜底。</p>
    </aside>
  </section>
</template>
