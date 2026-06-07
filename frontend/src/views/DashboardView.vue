<script setup lang="ts">
import * as echarts from "echarts";
import { computed, nextTick, onMounted, onUnmounted, ref } from "vue";

import { notifyError, request } from "@/api/http";
import { roleModules } from "@/permissions";
import { useAuthStore } from "@/stores/auth";

interface DashboardSummary {
  totals: {
    students: number;
    teachers: number;
    classes: number;
    scores: number;
    employment: number;
  };
  score_overview: {
    average_score: number;
    low_score_count: number;
    excellent_score_count: number;
  };
  employment_overview: {
    average_salary: number;
    top_salary: number;
  };
  class_distribution: { class_id: string; student_count: number }[];
  employment_distribution: { company_name: string; job_count: number }[];
  score_trends: { exam_round: number; average_score: number }[];
  recent_students: Record<string, unknown>[];
}

const auth = useAuthStore();
const loading = ref(false);
const summary = ref<DashboardSummary | null>(null);
const classChart = ref<HTMLDivElement>();
const scoreChart = ref<HTMLDivElement>();
const employmentChart = ref<HTMLDivElement>();
let charts: echarts.ECharts[] = [];

const shortcuts = computed(() =>
  roleModules(auth.role, auth.modules).filter((item) =>
    ["students", "scores", "employment", "statistics", "letters", "weather", "geocode"].includes(item.key),
  ),
);

function canOpen(moduleKey: string) {
  return auth.modules.includes(moduleKey);
}

const metrics = computed(() => {
  const data = summary.value;
  return [
    { key: "students", label: "学生总数", value: data?.totals.students ?? 0, route: "/students" },
    { key: "teachers", label: "教师总数", value: data?.totals.teachers ?? 0, route: "/teachers" },
    { key: "classes", label: "班级总数", value: data?.totals.classes ?? 0, route: "/classes" },
    { key: "scores", label: "成绩记录", value: data?.totals.scores ?? 0, route: "/scores" },
    { key: "employment", label: "就业记录", value: data?.totals.employment ?? 0, route: "/employment" },
    { key: "statistics", label: "平均成绩", value: data?.score_overview.average_score ?? 0, route: "/statistics" },
  ];
});

async function load() {
  loading.value = true;
  try {
    summary.value = await request<DashboardSummary>("/statistics/dashboard");
    await nextTick();
    renderCharts();
  } catch (error) {
    notifyError(error);
  } finally {
    loading.value = false;
  }
}

function renderCharts() {
  charts.forEach((chart) => chart.dispose());
  charts = [];
  if (!summary.value) return;

  if (classChart.value) {
    const chart = echarts.init(classChart.value);
    chart.setOption({
      tooltip: { trigger: "axis" },
      grid: { left: 36, right: 18, top: 28, bottom: 42 },
      xAxis: { type: "category", data: summary.value.class_distribution.map((item) => item.class_id) },
      yAxis: { type: "value" },
      series: [{ type: "bar", data: summary.value.class_distribution.map((item) => item.student_count), itemStyle: { color: "#158a8a" } }],
    });
    charts.push(chart);
  }

  if (scoreChart.value) {
    const chart = echarts.init(scoreChart.value);
    chart.setOption({
      tooltip: { trigger: "axis" },
      grid: { left: 36, right: 18, top: 28, bottom: 42 },
      xAxis: { type: "category", data: summary.value.score_trends.map((item) => `第${item.exam_round}轮`) },
      yAxis: { type: "value", min: 0, max: 100 },
      series: [{ type: "line", smooth: true, data: summary.value.score_trends.map((item) => item.average_score), itemStyle: { color: "#f9735b" }, areaStyle: { color: "rgba(249, 115, 91, 0.12)" } }],
    });
    charts.push(chart);
  }

  if (employmentChart.value) {
    const chart = echarts.init(employmentChart.value);
    chart.setOption({
      tooltip: { trigger: "item" },
      series: [
        {
          type: "pie",
          radius: ["42%", "72%"],
          color: ["#158a8a", "#123047", "#f9735b", "#67c9c3", "#9dc8c8"],
          data: summary.value.employment_distribution.map((item) => ({ name: item.company_name, value: item.job_count })),
        },
      ],
    });
    charts.push(chart);
  }
}

function resizeCharts() {
  charts.forEach((chart) => chart.resize());
}

onMounted(() => {
  load();
  window.addEventListener("resize", resizeCharts);
});

onUnmounted(() => {
  window.removeEventListener("resize", resizeCharts);
  charts.forEach((chart) => chart.dispose());
});
</script>

<template>
  <section class="dashboard" v-loading="loading">
    <div class="section-heading">
      <div>
        <h3>运营总览</h3>
        <p>基于当前账号可访问数据生成，统计结果来自后端实时接口。</p>
      </div>
      <el-button :loading="loading" @click="load">刷新</el-button>
    </div>

    <div class="metric-grid dense">
      <RouterLink v-for="item in metrics.filter((metric) => canOpen(metric.key))" :key="item.label" class="metric-card" :to="item.route">
        <span>{{ item.label }}</span>
        <strong>{{ item.value }}</strong>
      </RouterLink>
    </div>

    <div class="bi-grid">
      <article class="chart-card">
        <div class="card-title">
          <h4>班级人数分布</h4>
          <RouterLink v-if="canOpen('classes')" to="/classes">进入班级管理</RouterLink>
        </div>
        <div ref="classChart" class="chart-box" />
      </article>
      <article class="chart-card">
        <div class="card-title">
          <h4>成绩趋势</h4>
          <RouterLink v-if="canOpen('scores')" to="/scores">进入成绩管理</RouterLink>
        </div>
        <div ref="scoreChart" class="chart-box" />
      </article>
      <article class="chart-card">
        <div class="card-title">
          <h4>就业去向统计</h4>
          <RouterLink v-if="canOpen('employment')" to="/employment">进入就业管理</RouterLink>
        </div>
        <div ref="employmentChart" class="chart-box" />
      </article>
      <article class="chart-card risk-panel">
        <div class="card-title">
          <h4>风险与机会</h4>
          <RouterLink v-if="canOpen('statistics')" to="/statistics">查看统计分析</RouterLink>
        </div>
        <div class="risk-grid">
          <div>
            <span>低分记录</span>
            <strong>{{ summary?.score_overview.low_score_count ?? 0 }}</strong>
          </div>
          <div>
            <span>优秀记录</span>
            <strong>{{ summary?.score_overview.excellent_score_count ?? 0 }}</strong>
          </div>
          <div>
            <span>平均薪资</span>
            <strong>{{ summary?.employment_overview.average_salary ?? 0 }}</strong>
          </div>
          <div>
            <span>最高薪资</span>
            <strong>{{ summary?.employment_overview.top_salary ?? 0 }}</strong>
          </div>
        </div>
      </article>
    </div>

    <div class="dashboard-bottom">
      <article class="page-surface">
        <div class="card-title">
          <h4>近期学生</h4>
          <RouterLink v-if="canOpen('students')" to="/students">查看学生</RouterLink>
        </div>
        <el-table :data="summary?.recent_students || []" border height="300">
          <el-table-column prop="student_id" label="学号" width="130" />
          <el-table-column prop="name" label="姓名" width="120" />
          <el-table-column prop="class_id" label="班级编号" width="110" />
          <el-table-column prop="major" label="专业" min-width="160" show-overflow-tooltip />
        </el-table>
      </article>
      <article class="page-surface">
        <div class="card-title">
          <h4>快捷入口</h4>
          <span>按当前角色展示</span>
        </div>
        <div class="shortcut-grid">
          <RouterLink v-for="item in shortcuts" :key="item.key" :to="item.route" class="shortcut-card">
            <strong>{{ item.title }}</strong>
            <span>{{ item.subtitle }}</span>
          </RouterLink>
        </div>
      </article>
    </div>
  </section>
</template>
