<script setup lang="ts">
import { ElMessage } from "element-plus";
import { computed, onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";

import { notifyError, request } from "@/api/http";
import type { TableColumn } from "@/types";

interface ModuleConfig {
  title: string;
  endpoint: string;
  columns: TableColumn[];
  pickRows: (data: unknown) => Record<string, unknown>[];
  total: (data: unknown) => number;
}

const route = useRoute();
const loading = ref(false);
const rows = ref<Record<string, unknown>[]>([]);
const total = ref(0);

const configs: Record<string, ModuleConfig> = {
  students: {
    title: "学生列表",
    endpoint: "/students?skip=0&limit=20",
    columns: [
      { key: "student_id", label: "学生编号" },
      { key: "name", label: "姓名" },
      { key: "class_id", label: "班级ID" },
      { key: "major", label: "专业" },
      { key: "education", label: "学历" },
    ],
    pickRows: (data) => (data as { students?: Record<string, unknown>[] }).students || [],
    total: (data) => Number((data as { total?: number }).total || 0),
  },
  classes: {
    title: "班级列表",
    endpoint: "/classes/?page=1&size=20",
    columns: [
      { key: "class_id", label: "班级编号" },
      { key: "head_teacher", label: "班主任" },
      { key: "start_date", label: "开班日期" },
      { key: "description", label: "描述" },
    ],
    pickRows: (data) => (data as { items?: Record<string, unknown>[] }).items || [],
    total: (data) => Number((data as { total?: number }).total || 0),
  },
  teachers: {
    title: "教师列表",
    endpoint: "/teacher/list",
    columns: [
      { key: "teacher_number", label: "工号" },
      { key: "name", label: "姓名" },
      { key: "subject", label: "科目" },
      { key: "phone", label: "电话" },
      { key: "email", label: "邮箱" },
    ],
    pickRows: (data) => (Array.isArray(data) ? data : []),
    total: (data) => (Array.isArray(data) ? data.length : 0),
  },
  scores: {
    title: "成绩列表",
    endpoint: "/score/query/?page=1&page_size=20",
    columns: [
      { key: "student_id", label: "学生编号" },
      { key: "student_name", label: "姓名" },
      { key: "exam_round", label: "轮次" },
      { key: "score", label: "分数" },
      { key: "remark", label: "备注" },
    ],
    pickRows: (data) => (data as { items?: Record<string, unknown>[] }).items || [],
    total: (data) => Number((data as { total?: number }).total || 0),
  },
  employment: {
    title: "就业列表",
    endpoint: "/jobs/page?page=1&size=20",
    columns: [
      { key: "student_id", label: "学生编号" },
      { key: "name", label: "姓名" },
      { key: "class_name", label: "班级" },
      { key: "company_name", label: "公司" },
      { key: "salary", label: "薪资" },
      { key: "position", label: "岗位" },
    ],
    pickRows: (data) => (data as { list?: Record<string, unknown>[] }).list || [],
    total: (data) => Number((data as { total?: number }).total || 0),
  },
  statistics: {
    title: "统计结果",
    endpoint: "/statistics/employment/top5-salary?limit=20",
    columns: [
      { key: "name", label: "姓名" },
      { key: "class_name", label: "班级" },
      { key: "company_name", label: "公司" },
      { key: "salary", label: "薪资" },
    ],
    pickRows: (data) => (Array.isArray(data) ? data : []),
    total: (data) => (Array.isArray(data) ? data.length : 0),
  },
};

const moduleKey = computed(() => String(route.meta.module || ""));
const config = computed(() => configs[moduleKey.value]);

async function load() {
  if (!config.value) return;
  loading.value = true;
  try {
    const data = await request<unknown>(config.value.endpoint);
    rows.value = config.value.pickRows(data);
    total.value = config.value.total(data);
  } catch (error) {
    rows.value = [];
    total.value = 0;
    notifyError(error);
  } finally {
    loading.value = false;
  }
}

function copyJson(row: Record<string, unknown>) {
  navigator.clipboard.writeText(JSON.stringify(row, null, 2));
  ElMessage.success("已复制");
}

onMounted(load);
watch(() => route.path, load);
</script>

<template>
  <section class="page-surface">
    <div class="section-heading">
      <div>
        <h3>{{ config?.title }}</h3>
        <p>当前账号只能看到后端授权范围内的数据。</p>
      </div>
      <el-button type="primary" :loading="loading" @click="load">刷新</el-button>
    </div>
    <el-table :data="rows" border stripe v-loading="loading" height="560">
      <el-table-column
        v-for="column in config?.columns"
        :key="column.key"
        :prop="column.key"
        :label="column.label"
        min-width="130"
      />
      <el-table-column label="操作" width="120" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="copyJson(row)">复制</el-button>
        </template>
      </el-table-column>
    </el-table>
    <div class="table-footer">共 {{ total }} 条</div>
  </section>
</template>
