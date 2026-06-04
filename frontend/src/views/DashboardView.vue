<script setup lang="ts">
import { computed } from "vue";

import { roleLabels, roleModules } from "@/permissions";
import { useAuthStore } from "@/stores/auth";

const auth = useAuthStore();
const modules = computed(() => roleModules(auth.role, auth.modules));
const identity = computed(() => {
  if (!auth.user) return "未绑定";
  if (auth.user.role === "teacher") return auth.user.teacher_id ? `教师ID ${auth.user.teacher_id}` : "未绑定教师身份";
  if (auth.user.role === "student") return auth.user.student_id ? `学生编号 ${auth.user.student_id}` : "未绑定学生身份";
  if (auth.user.role === "consultant") return auth.user.teacher_id ? `顾问ID ${auth.user.teacher_id}` : "未绑定顾问身份";
  return "全量数据权限";
});
</script>

<template>
  <section class="dashboard">
    <div class="hero-card">
      <div>
        <p class="eyebrow">ACCESS CONTROL</p>
        <h1>{{ auth.user?.real_name || auth.user?.username }}</h1>
        <span>{{ auth.role ? roleLabels[auth.role] : "用户" }} · {{ identity }}</span>
      </div>
      <img src="/assets/dashboard-hero.png" alt="数据看板" />
    </div>

    <div class="metric-grid">
      <article class="metric-card">
        <span>可访问模块</span>
        <strong>{{ modules.length }}</strong>
      </article>
      <article class="metric-card">
        <span>权限点</span>
        <strong>{{ auth.permissions.length }}</strong>
      </article>
      <article class="metric-card">
        <span>数据范围</span>
        <strong>{{ auth.role === "admin" ? "全量" : "受限" }}</strong>
      </article>
    </div>

    <div class="module-grid">
      <RouterLink v-for="item in modules" :key="item.key" class="module-card" :to="item.route">
        <strong>{{ item.title }}</strong>
        <span>{{ item.subtitle }}</span>
      </RouterLink>
    </div>
  </section>
</template>
