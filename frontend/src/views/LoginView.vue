<script setup lang="ts">
import { Lock, User } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import { computed, onBeforeUnmount, onMounted, reactive, ref } from "vue";
import { useRouter } from "vue-router";

import { notifyError } from "@/api/http";
import { useAuthStore } from "@/stores/auth";
import campusCorridorBg from "@/assets/login-bg-campus-corridor.png";
import campusCourtyardBg from "@/assets/login-bg-campus-courtyard.png";
import campusEntranceBg from "@/assets/login-bg-campus-entrance.png";
import studentServiceBg from "@/assets/login-bg-student-service.png";

const router = useRouter();
const auth = useAuthStore();
const loading = ref(false);
const currentBackgroundIndex = ref(0);
let carouselTimer: number | undefined;

const loginBackgrounds = [
  {
    title: "校园入口",
    subtitle: "统一身份入口",
    image: campusEntranceBg,
  },
  {
    title: "教学楼走廊",
    subtitle: "教学数据协同",
    image: campusCorridorBg,
  },
  {
    title: "学生事务大厅",
    subtitle: "业务办理闭环",
    image: studentServiceBg,
  },
  {
    title: "校园庭院",
    subtitle: "成长轨迹管理",
    image: campusCourtyardBg,
  },
];

const currentBackground = computed(() => loginBackgrounds[currentBackgroundIndex.value]);
const form = reactive({
  username: "",
  password: "",
});

function setBackground(index: number) {
  currentBackgroundIndex.value = index;
}

function showNextBackground() {
  currentBackgroundIndex.value = (currentBackgroundIndex.value + 1) % loginBackgrounds.length;
}

onMounted(() => {
  loginBackgrounds.forEach((item) => {
    const image = new Image();
    image.src = item.image;
  });
  carouselTimer = window.setInterval(showNextBackground, 7000);
});

onBeforeUnmount(() => {
  if (carouselTimer !== undefined) {
    window.clearInterval(carouselTimer);
  }
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
    <div class="login-bg-stage" aria-hidden="true">
      <div
        v-for="(item, index) in loginBackgrounds"
        :key="item.title"
        class="login-bg-layer"
        :class="{ active: index === currentBackgroundIndex }"
        :style="{ backgroundImage: `url(${item.image})` }"
      />
    </div>

    <section class="login-shell">
      <div class="login-glass-card">
        <div class="login-heading">
          <div class="brand-mark">管</div>
          <div>
            <p class="eyebrow">学生管理系统</p>
            <h1>登录工作台</h1>
            <span>管理员、教师、学生、顾问使用同一入口，系统按角色控制数据范围。</span>
          </div>
        </div>

        <el-form class="login-form" label-position="top" @keyup.enter="submit">
          <el-form-item label="账号">
            <el-input v-model="form.username" size="large" autocomplete="username" :prefix-icon="User" />
          </el-form-item>
          <el-form-item label="密码">
            <el-input
              v-model="form.password"
              size="large"
              type="password"
              show-password
              autocomplete="current-password"
              :prefix-icon="Lock"
            />
          </el-form-item>
          <el-button class="full-button login-submit" type="primary" size="large" :loading="loading" @click="submit">
            进入系统
          </el-button>
        </el-form>

        <div class="login-role-strip" aria-label="支持的登录角色">
          <span>管理员</span>
          <span>教师</span>
          <span>学生</span>
          <span>顾问</span>
        </div>

        <div class="login-demo">
          <span>admin / admin123</span>
          <span>teacher / teacher123</span>
          <span>student / student123</span>
          <span>consultant / consultant123</span>
        </div>
      </div>

      <div class="login-carousel" aria-label="登录背景切换">
        <button
          v-for="(item, index) in loginBackgrounds"
          :key="item.title"
          class="carousel-dot"
          :class="{ active: index === currentBackgroundIndex }"
          type="button"
          :aria-label="`切换到${item.title}背景`"
          @click="setBackground(index)"
        >
          <span>{{ item.title }}</span>
        </button>
      </div>

      <div class="login-scene-caption">
        <strong>{{ currentBackground.title }}</strong>
        <span>{{ currentBackground.subtitle }}</span>
      </div>
    </section>
  </main>
</template>
