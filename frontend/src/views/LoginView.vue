<script setup lang="ts">
import { Avatar, Lock, Management, Reading, School, User, UserFilled } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import { reactive, ref } from "vue";
import { useRouter } from "vue-router";

import { notifyError } from "@/api/http";
import { useAuthStore } from "@/stores/auth";
import campusEntranceBg from "@/assets/login-bg-campus-entrance.png";

const router = useRouter();
const auth = useAuthStore();
const loading = ref(false);

const form = reactive({
  username: "",
  password: "",
});

const roleOptions = [
  { label: "管理员", icon: Management, tone: "primary" },
  { label: "教师", icon: UserFilled, tone: "blue" },
  { label: "学生", icon: School, tone: "green" },
  { label: "顾问", icon: Avatar, tone: "orange" },
];

async function submit() {
  if (!form.username || !form.password) {
    ElMessage.warning("请输入账号和密码");
    return;
  }
  loading.value = true;
  try {
    await auth.login(form.username, form.password);
    ElMessage.success("登录成功");
    router.push("/dashboard");
  } catch (error) {
    notifyError(error);
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <main class="login-page" :style="{ backgroundImage: `url(${campusEntranceBg})` }">
    <section class="login-shell" aria-label="学生管理系统登录">
      <div class="login-glass-card">
        <div class="brand-orbit">
          <el-icon><Reading /></el-icon>
        </div>

        <div class="login-heading">
          <h1>学生管理系统</h1>
          <div class="login-subtitle">
            <span></span>
            <p>登录工作台</p>
            <span></span>
          </div>
        </div>

        <el-form class="login-form" @keyup.enter="submit">
          <el-form-item>
            <el-input v-model="form.username" size="large" autocomplete="username" placeholder="账号" :prefix-icon="User" />
          </el-form-item>
          <el-form-item>
            <el-input
              v-model="form.password"
              size="large"
              type="password"
              show-password
              autocomplete="current-password"
              placeholder="密码"
              :prefix-icon="Lock"
            />
          </el-form-item>
          <el-button class="full-button login-submit" type="primary" size="large" :loading="loading" @click="submit">
            进入系统
          </el-button>
        </el-form>

        <div class="role-divider">
          <span></span>
          <p>选择身份登录</p>
          <span></span>
        </div>

        <div class="login-role-strip" aria-label="支持的登录角色">
          <button
            v-for="item in roleOptions"
            :key="item.label"
            class="role-choice"
            :class="`role-choice-${item.tone}`"
            type="button"
          >
            <el-icon><component :is="item.icon" /></el-icon>
            <span>{{ item.label }}</span>
          </button>
        </div>
      </div>
    </section>
  </main>
</template>
