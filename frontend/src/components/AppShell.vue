<script setup lang="ts">
import * as Icons from "@element-plus/icons-vue";
import { User } from "@element-plus/icons-vue";
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";

import { roleLabels, roleModules } from "@/permissions";
import { useAuthStore } from "@/stores/auth";

const auth = useAuthStore();
const router = useRouter();
const route = useRoute();

const menus = computed(() => roleModules(auth.role, auth.modules));
const activePath = computed(() => route.path);
const current = computed(() => menus.value.find((item) => item.route === route.path) || menus.value[0]);

function icon(name: string) {
  return (Icons as Record<string, unknown>)[name];
}

function logout() {
  auth.logout();
  router.push("/login");
}
</script>

<template>
  <el-container class="shell">
    <el-aside class="sidebar" width="248px">
      <div class="brand">
        <div class="brand-mark">沃</div>
        <div>
          <h1>学生管理系统</h1>
          <p>角色权限工作台</p>
        </div>
      </div>
      <el-scrollbar>
        <el-menu :default-active="activePath" router class="menu">
          <el-menu-item v-for="item in menus" :key="item.key" :index="item.route">
            <el-icon><component :is="icon(item.icon)" /></el-icon>
            <span>{{ item.title }}</span>
          </el-menu-item>
        </el-menu>
      </el-scrollbar>
    </el-aside>

    <el-container>
      <el-header class="topbar">
        <div class="title-block">
          <h2>{{ current?.title || "工作台" }}</h2>
          <p>{{ current?.subtitle || "学生管理系统" }}</p>
        </div>
        <div class="topbar-actions">
          <el-tag effect="dark" type="success">{{ auth.role ? roleLabels[auth.role] : "用户" }}</el-tag>
          <el-dropdown>
            <button class="user-button" type="button">
              <el-icon><User /></el-icon>
              <span>{{ auth.user?.real_name || auth.user?.username }}</span>
            </button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      <el-main class="content">
        <RouterView />
      </el-main>
    </el-container>
  </el-container>
</template>
