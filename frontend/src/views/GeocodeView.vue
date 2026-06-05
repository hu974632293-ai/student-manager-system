<script setup lang="ts">
import { ElMessage } from "element-plus";
import { computed, ref } from "vue";

import { notifyError, request } from "@/api/http";

const city = ref("北京");
const loading = ref(false);
const result = ref<Record<string, unknown>[] | null>(null);

const rows = computed(() => result.value || []);

async function query() {
  const keyword = city.value.trim();
  if (!keyword) {
    ElMessage.warning("请填写城市或地址");
    return;
  }
  loading.value = true;
  try {
    const data = await request<Record<string, unknown>[]>(`/weather/geocode?city=${encodeURIComponent(keyword)}`);
    result.value = Array.isArray(data) ? data : [];
  } catch (error) {
    result.value = null;
    notifyError(error);
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <section class="page-surface">
    <div class="section-heading">
      <div>
        <h3>经纬度查询</h3>
        <p>输入城市或地址，查询标准化地址、经纬度和行政区编码。</p>
      </div>
      <form class="toolbar-actions" @submit.prevent="query">
        <el-input v-model="city" placeholder="例如：北京、杭州市西湖区" style="width: 280px" />
        <el-button type="primary" native-type="submit" :loading="loading">查询</el-button>
      </form>
    </div>

    <el-table :data="rows" border stripe v-loading="loading" height="520">
      <el-table-column prop="formatted_address" label="标准化地址" min-width="260" show-overflow-tooltip />
      <el-table-column prop="country" label="国家" width="100" />
      <el-table-column prop="province" label="省份" width="120" />
      <el-table-column prop="city" label="城市" width="120" />
      <el-table-column prop="district" label="区县" width="120" />
      <el-table-column prop="adcode" label="行政区编码" width="130" />
      <el-table-column prop="location" label="经纬度" min-width="160" />
      <el-table-column prop="level" label="匹配级别" width="120" />
    </el-table>

    <div v-if="result && !rows.length" class="empty-state compact">没有查询到匹配地址</div>
  </section>
</template>
