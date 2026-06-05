<script setup lang="ts">
import { ElMessage } from "element-plus";
import { computed, reactive, ref } from "vue";

import { notifyError, request } from "@/api/http";

const loading = ref(false);
const result = ref<Record<string, unknown> | null>(null);
const form = reactive({
  mode: "city",
  city: "北京",
  latitude: "",
  longitude: "",
});

const lives = computed(() => {
  const value = result.value?.lives;
  return Array.isArray(value) ? (value as Record<string, unknown>[]) : [];
});

async function query() {
  const params = new URLSearchParams();
  if (form.mode === "city") {
    if (!form.city.trim()) {
      ElMessage.warning("请填写城市名称");
      return;
    }
    params.set("city", form.city.trim());
  } else {
    if (!form.latitude || !form.longitude) {
      ElMessage.warning("请填写纬度和经度");
      return;
    }
    params.set("latitude", form.latitude);
    params.set("longitude", form.longitude);
  }
  loading.value = true;
  try {
    result.value = await request<Record<string, unknown>>(`/weather/current?${params.toString()}`);
  } catch (error) {
    result.value = null;
    notifyError(error);
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <section class="tool-layout">
    <article class="page-surface">
      <div class="section-heading">
        <div>
          <h3>天气查询</h3>
          <p>按城市或经纬度调用后端天气接口，结果直接展示在页面。</p>
        </div>
        <el-button type="primary" native-type="submit" :loading="loading" @click="query">查询</el-button>
      </div>

      <el-form label-position="top" @submit.prevent="query" @keydown.enter.prevent="query">
        <el-form-item label="查询方式">
          <el-radio-group v-model="form.mode">
            <el-radio-button label="city">城市</el-radio-button>
            <el-radio-button label="location">经纬度</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-if="form.mode === 'city'" label="城市">
          <el-input v-model="form.city" placeholder="例如：北京、上海、杭州" />
        </el-form-item>
        <div v-else class="form-grid">
          <el-form-item label="纬度">
            <el-input v-model="form.latitude" placeholder="39.9042" />
          </el-form-item>
          <el-form-item label="经度">
            <el-input v-model="form.longitude" placeholder="116.4074" />
          </el-form-item>
        </div>
      </el-form>
    </article>

    <aside class="page-surface">
      <div class="card-title">
        <h4>天气结果</h4>
        <span>{{ lives.length ? "实时天气" : "等待查询" }}</span>
      </div>
      <div v-if="lives.length" class="weather-grid">
        <article v-for="item in lives" :key="String(item.adcode || item.city)" class="weather-card">
          <strong>{{ item.province }} {{ item.city }}</strong>
          <span>{{ item.weather }}</span>
          <div>
            <b>{{ item.temperature }}°C</b>
            <small>湿度 {{ item.humidity }}%</small>
          </div>
          <p>风向 {{ item.winddirection }}，风力 {{ item.windpower }}，更新时间 {{ item.reporttime }}</p>
        </article>
      </div>
      <pre v-if="result" class="result-pre">{{ JSON.stringify(result, null, 2) }}</pre>
      <div v-else class="empty-state compact">接口失败、API key 缺失或城市不存在时会在这里保持空状态并弹出错误提示。</div>
    </aside>
  </section>
</template>
