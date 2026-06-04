<script setup lang="ts">
import { onMounted, ref } from "vue";

import { notifyError, request } from "@/api/http";

const loading = ref(false);
const rows = ref<Record<string, unknown>[]>([]);
const total = ref(0);

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
      <el-table-column prop="level" label="级别" width="120" />
      <el-table-column prop="message" label="内容" min-width="220" />
      <el-table-column prop="created_at" label="时间" width="180" />
    </el-table>
    <div class="table-footer">共 {{ total }} 条</div>
  </section>
</template>
