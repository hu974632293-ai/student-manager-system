<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { notifyError, request } from "@/api/http";
import { roleLabels } from "@/permissions";
import { useAuthStore } from "@/stores/auth";

type Row = Record<string, unknown>;

const auth = useAuthStore();
const loading = ref(false);
const student = ref<Row | null>(null);

const accountRows = computed(() => [
  { label: "账号", value: auth.user?.username || "-" },
  { label: "姓名", value: auth.user?.real_name || "-" },
  { label: "角色", value: auth.role ? roleLabels[auth.role] : "-" },
  { label: "绑定学号", value: auth.user?.student_id || "未绑定" },
]);

const profileRows = computed(() => {
  if (!student.value) return [];
  return [
    { label: "学号", value: student.value.student_id },
    { label: "姓名", value: student.value.name },
    { label: "班级ID", value: student.value.class_id },
    { label: "性别", value: student.value.gender },
    { label: "年龄", value: student.value.age },
    { label: "籍贯", value: student.value.native_place },
    { label: "毕业学校", value: student.value.graduate_school },
    { label: "专业", value: student.value.major },
    { label: "学历", value: student.value.education },
    { label: "入学日期", value: student.value.enrollment_date },
    { label: "毕业日期", value: student.value.graduation_date },
  ];
});

async function loadProfile() {
  if (!auth.user?.student_id) return;
  loading.value = true;
  try {
    const data = await request<{ select_id?: Row | null }>(
      `/students/one?student_id=${encodeURIComponent(auth.user.student_id)}`,
    );
    student.value = data.select_id || null;
  } catch (error) {
    student.value = null;
    notifyError(error);
  } finally {
    loading.value = false;
  }
}

onMounted(loadProfile);
</script>

<template>
  <section class="profile-page" v-loading="loading">
    <article class="page-surface">
      <div class="section-heading">
        <div>
          <h3>个人信息</h3>
          <p>展示当前登录账号、绑定身份和本人学生档案。</p>
        </div>
        <el-button :loading="loading" @click="loadProfile">刷新</el-button>
      </div>

      <el-descriptions :column="2" border>
        <el-descriptions-item v-for="item in accountRows" :key="item.label" :label="item.label">
          {{ item.value }}
        </el-descriptions-item>
      </el-descriptions>
    </article>

    <article class="page-surface">
      <div class="card-title">
        <h4>学生档案</h4>
        <span>{{ student ? "已绑定档案" : "暂无档案" }}</span>
      </div>
      <el-descriptions v-if="student" :column="2" border>
        <el-descriptions-item v-for="item in profileRows" :key="item.label" :label="item.label">
          {{ item.value ?? "-" }}
        </el-descriptions-item>
      </el-descriptions>
      <div v-else class="empty-state compact">当前账号未绑定学生档案，请联系管理员处理。</div>
    </article>

    <article class="page-surface">
      <div class="card-title">
        <h4>当前权限</h4>
        <span>{{ auth.permissions.length }} 个权限点</span>
      </div>
      <div class="tag-list">
        <el-tag v-for="item in auth.permissions" :key="item" effect="plain">{{ item }}</el-tag>
      </div>
    </article>
  </section>
</template>
