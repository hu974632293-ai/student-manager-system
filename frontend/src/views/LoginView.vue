<script setup lang="ts">
import { ElMessage } from "element-plus";
import { reactive, ref } from "vue";
import { useRouter } from "vue-router";

import { notifyError } from "@/api/http";
import { useAuthStore } from "@/stores/auth";
import heroImage from "../../assets/dashboard-hero.png";

const router = useRouter();
const auth = useAuthStore();
const loading = ref(false);
const form = reactive({
  username: "",
  password: "",
});

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
  <main class="login-page">
    <section class="login-visual">
      <img :src="heroImage" alt="学生管理系统数据看板" />
      <div class="visual-copy">
        <p>角色权限工作台</p>
        <h1>学生管理系统</h1>
        <span>按角色进入对应工作台，数据访问范围由系统自动控制。</span>
      </div>
    </section>
    <section class="login-panel">
      <div class="login-heading">
        <div class="brand-mark">管</div>
        <div>
          <h2>登录工作台</h2>
          <p>管理员、教师、学生、顾问使用同一入口</p>
        </div>
      </div>
      <el-form label-position="top" @keyup.enter="submit">
        <el-form-item label="账号">
          <el-input v-model="form.username" size="large" autocomplete="username" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="form.password" size="large" type="password" show-password autocomplete="current-password" />
        </el-form-item>
        <el-button class="full-button" type="primary" size="large" :loading="loading" @click="submit">
          进入系统
        </el-button>
      </el-form>
      <div class="login-demo">
        <span>admin / admin123</span>
        <span>teacher / teacher123</span>
        <span>student / student123</span>
        <span>consultant / consultant123</span>
      </div>
    </section>
  </main>
</template>
