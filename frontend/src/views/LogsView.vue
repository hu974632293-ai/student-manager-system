<script setup lang="ts">
import { onMounted, ref } from "vue";

import { notifyError, request } from "@/api/http";

const loading = ref(false);
const rows = ref<Record<string, unknown>[]>([]);
const total = ref(0);

const levelLabels: Record<string, string> = {
  DEBUG: "调试",
  INFO: "信息",
  WARNING: "警告",
  ERROR: "错误",
  CRITICAL: "严重错误",
};

function levelLabel(level: unknown) {
  if (!level) return "-";
  const value = String(level).toUpperCase();
  return levelLabels[value] || String(level);
}

function formatTime(value: unknown) {
  if (!value) return "-";
  const date = new Date(String(value));
  if (Number.isNaN(date.getTime())) return String(value);
  return date.toLocaleString("zh-CN", { hour12: false });
}

async function load() {
  loading.value = true;
  try {
    const data = await request<{ total: number; items: Record<string, unknown>[] }>("/logs/recent?limit=50");
    rows.value = data.items;
    total.value = data.total;
  } catch (error) {
    notifyError(error);
  } finally {
    loading.value = false;
  }
}

onMounted(load);
</script>

<template>
  <section class="page-surface">
    <div class="section-heading">
      <div>
        <h3>系统日志</h3>
        <p>仅管理员可见，后端接口也会校验角色。</p>
      </div>
      <el-button type="primary" :loading="loading" @click="load">刷新</el-button>
    </div>
    <el-table :data="rows" border stripe v-loading="loading" height="520">
      <el-table-column label="级别" width="120">
        <template #default="{ row }">{{ levelLabel(row.level) }}</template>
      </el-table-column>
      <el-table-column prop="message" label="内容" min-width="220" />
      <el-table-column label="时间" width="180">
        <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
      </el-table-column>
    </el-table>
    <div class="table-footer">共 {{ total }} 条</div>
  </section>
</template>
