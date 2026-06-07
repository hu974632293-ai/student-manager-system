<script setup lang="ts">
import * as Icons from "@element-plus/icons-vue";
import { Menu, User } from "@element-plus/icons-vue";
import { computed, ref } from "vue";
import { useRoute, useRouter } from "vue-router";

import { findModule, groupLabels, roleLabels, roleModules } from "@/permissions";
import { useAuthStore } from "@/stores/auth";
import type { MenuModule } from "@/types";

const auth = useAuthStore();
const router = useRouter();
const route = useRoute();
const mobileMenuVisible = ref(false);

const menus = computed(() => roleModules(auth.role, auth.modules));
const activePath = computed(() => route.path);
const current = computed(() => findModule(route.meta.module as string) || menus.value[0]);
const roleName = computed(() => (auth.role ? roleLabels[auth.role] : "用户"));
const topMenus = computed(() => menus.value.filter((item) => !item.group));
const groupedMenus = computed(() => {
  const groups: Record<string, MenuModule[]> = {};
  menus.value
    .filter((item) => item.group)
    .forEach((item) => {
      const group = item.group || "tools";
      groups[group] = groups[group] || [];
      groups[group].push(item);
    });
  return groups;
});

function icon(name: string) {
  return (Icons as Record<string, unknown>)[name];
}

function logout() {
  auth.logout();
  router.push("/login");
}

function closeMobileMenu() {
  mobileMenuVisible.value = false;
}
</script>

<template>
  <el-container class="shell">
    <el-aside class="sidebar" width="252px">
      <div class="brand">
        <div class="brand-mark">管</div>
        <div>
          <h1>学生管理系统</h1>
          <p>教务与工具工作台</p>
        </div>
      </div>
      <el-scrollbar>
        <el-menu :default-active="activePath" router class="menu">
          <el-menu-item v-for="item in topMenus" :key="item.key" :index="item.route">
            <el-icon><component :is="icon(item.icon)" /></el-icon>
            <span>{{ item.title }}</span>
          </el-menu-item>

          <el-sub-menu v-for="(items, group) in groupedMenus" :key="group" :index="String(group)">
            <template #title>
              <el-icon><component :is="icon(group === 'business' ? 'School' : 'Tools')" /></el-icon>
              <span>{{ groupLabels[group as keyof typeof groupLabels] }}</span>
            </template>
            <el-menu-item v-for="item in items" :key="item.key" :index="item.route">
              <el-icon><component :is="icon(item.icon)" /></el-icon>
              <span>{{ item.title }}</span>
            </el-menu-item>
          </el-sub-menu>
        </el-menu>
      </el-scrollbar>
    </el-aside>

    <el-container>
      <el-header class="topbar">
        <div class="title-block">
          <button class="mobile-menu-button" type="button" aria-label="打开菜单" @click="mobileMenuVisible = true">
            <el-icon><Menu /></el-icon>
          </button>
          <h2>{{ current?.title || "工作台" }}</h2>
          <p>{{ current?.subtitle || "学生管理系统" }}</p>
        </div>
        <div class="topbar-actions">
          <el-dropdown>
            <button class="user-button" type="button">
              <el-icon><User /></el-icon>
              <span>{{ roleName }} · {{ auth.user?.real_name || auth.user?.username }}</span>
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

    <el-drawer v-model="mobileMenuVisible" title="系统菜单" direction="ltr" size="286px" class="mobile-menu-drawer">
      <el-menu :default-active="activePath" router class="mobile-menu" @select="closeMobileMenu">
        <el-menu-item v-for="item in topMenus" :key="item.key" :index="item.route">
          <el-icon><component :is="icon(item.icon)" /></el-icon>
          <span>{{ item.title }}</span>
        </el-menu-item>

        <el-sub-menu v-for="(items, group) in groupedMenus" :key="group" :index="String(group)">
          <template #title>
            <el-icon><component :is="icon(group === 'business' ? 'School' : 'Tools')" /></el-icon>
            <span>{{ groupLabels[group as keyof typeof groupLabels] }}</span>
          </template>
          <el-menu-item v-for="item in items" :key="item.key" :index="item.route">
            <el-icon><component :is="icon(item.icon)" /></el-icon>
            <span>{{ item.title }}</span>
          </el-menu-item>
        </el-sub-menu>
      </el-menu>
    </el-drawer>
  </el-container>
</template>
