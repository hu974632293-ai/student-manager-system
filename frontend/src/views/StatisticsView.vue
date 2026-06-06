<script setup lang="ts">
import * as echarts from "echarts";
import { nextTick, onMounted, onUnmounted, ref } from "vue";

import { notifyError, request } from "@/api/http";

type Row = Record<string, unknown>;

const loading = ref(false);
const overAgeRows = ref<Row[]>([]);
const genderRows = ref<Row[]>([]);
const excellentRows = ref<Row[]>([]);
const scoreAverageRows = ref<Row[]>([]);
const failedRows = ref<Row[]>([]);
const topSalaryRows = ref<Row[]>([]);
const studentDurationRows = ref<Row[]>([]);
const durationRows = ref<Row[]>([]);
const genderChart = ref<HTMLDivElement>();
const scoreChart = ref<HTMLDivElement>();
let charts: echarts.ECharts[] = [];

async function load() {
  loading.value = true;
  try {
    const [overAge, gender, excellent, scoreAverage, failed, topSalary, studentDuration, duration] = await Promise.all([
      request<Row[]>("/statistics/students/over-30"),
      request<Row[]>("/statistics/classes/gender-count"),
      request<Row[]>("/statistics/scores/all-above-80"),
      request<Row[]>("/statistics/scores/class-average"),
      request<Row[]>("/statistics/scores/failed-more-than-twice"),
      request<Row[]>("/statistics/employment/top5-salary?limit=20"),
      request<Row[]>("/statistics/employment/student-duration"),
      request<Row[]>("/statistics/employment/class-average-duration"),
    ]);
    overAgeRows.value = Array.isArray(overAge) ? overAge : [];
    genderRows.value = Array.isArray(gender) ? gender : [];
    excellentRows.value = Array.isArray(excellent) ? excellent : [];
    scoreAverageRows.value = Array.isArray(scoreAverage) ? scoreAverage : [];
    failedRows.value = Array.isArray(failed) ? failed : [];
    topSalaryRows.value = Array.isArray(topSalary) ? topSalary : [];
    studentDurationRows.value = Array.isArray(studentDuration) ? studentDuration : [];
    durationRows.value = Array.isArray(duration) ? duration : [];
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
  if (genderChart.value) {
    const chart = echarts.init(genderChart.value);
    chart.setOption({
      tooltip: { trigger: "axis" },
      legend: {},
      grid: { left: 36, right: 18, top: 42, bottom: 42 },
      xAxis: { type: "category", data: genderRows.value.map((item) => item.class_id) },
      yAxis: { type: "value" },
      series: [
        { name: "男", type: "bar", stack: "gender", data: genderRows.value.map((item) => item.male_count || 0) },
        { name: "女", type: "bar", stack: "gender", data: genderRows.value.map((item) => item.female_count || 0) },
      ],
    });
    charts.push(chart);
  }
  if (scoreChart.value) {
    const chart = echarts.init(scoreChart.value);
    const rows = scoreAverageRows.value.slice(0, 20);
    chart.setOption({
      tooltip: { trigger: "axis" },
      grid: { left: 36, right: 18, top: 28, bottom: 64 },
      xAxis: { type: "category", data: rows.map((item) => `${item.class_id}-第${item.exam_round}轮`), axisLabel: { rotate: 35 } },
      yAxis: { type: "value", min: 0, max: 100 },
      series: [{ type: "line", smooth: true, data: rows.map((item) => item.average_score || 0), itemStyle: { color: "#0f766e" } }],
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
        <h3>统计分析</h3>
        <p>使用后端统计接口展示班级、成绩与就业分析。</p>
      </div>
      <el-button :loading="loading" @click="load">刷新</el-button>
    </div>

    <div class="bi-grid">
      <article class="chart-card">
        <div class="card-title">
          <h4>班级性别分布</h4>
          <span>{{ genderRows.length }} 个班级</span>
        </div>
        <div ref="genderChart" class="chart-box" />
      </article>
      <article class="chart-card">
        <div class="card-title">
          <h4>班级平均成绩</h4>
          <span>{{ scoreAverageRows.length }} 条统计</span>
        </div>
        <div ref="scoreChart" class="chart-box" />
      </article>
    </div>

    <div class="dashboard-bottom">
      <article class="page-surface">
        <div class="card-title">
          <h4>年龄大于 30 岁学生</h4>
          <span>{{ overAgeRows.length }} 条记录</span>
        </div>
        <el-table :data="overAgeRows" border height="320">
          <el-table-column prop="student_id" label="学号" width="130" />
          <el-table-column prop="name" label="姓名" width="120" />
          <el-table-column prop="class_id" label="班级" width="120" />
          <el-table-column prop="age" label="年龄" width="100" />
          <el-table-column prop="major" label="专业" min-width="160" show-overflow-tooltip />
        </el-table>
      </article>
      <article class="page-surface">
        <div class="card-title">
          <h4>全科优秀成绩明细</h4>
          <span>默认筛选所有成绩不低于 80 分的学生</span>
        </div>
        <el-table :data="excellentRows" border height="320">
          <el-table-column prop="student_id" label="学号" width="130" />
          <el-table-column prop="name" label="姓名" width="120" />
          <el-table-column prop="exam_round" label="考试轮次" width="120" />
          <el-table-column prop="score" label="分数" width="120" />
        </el-table>
      </article>
    </div>

    <div class="dashboard-bottom">
      <article class="page-surface">
        <div class="card-title">
          <h4>挂科风险</h4>
          <span>默认低于 60 分且次数超过 2 次</span>
        </div>
        <el-table :data="failedRows" border height="320">
          <el-table-column prop="name" label="姓名" width="120" />
          <el-table-column prop="class_id" label="班级" width="120" />
          <el-table-column prop="exam_round" label="轮次" width="100" />
          <el-table-column prop="score" label="分数" width="100" />
        </el-table>
      </article>
      <article class="page-surface">
        <div class="card-title">
          <h4>就业薪资排行</h4>
          <RouterLink to="/employment">进入就业管理</RouterLink>
        </div>
        <el-table :data="topSalaryRows" border height="320">
          <el-table-column prop="name" label="姓名" width="120" />
          <el-table-column prop="class_name" label="班级" width="120" />
          <el-table-column prop="company_name" label="公司" min-width="160" show-overflow-tooltip />
          <el-table-column prop="salary" label="薪资" width="120" />
        </el-table>
      </article>
    </div>

    <div class="dashboard-bottom">
      <article class="page-surface">
        <div class="card-title">
          <h4>学生就业时长</h4>
          <span>基于录用日期与开岗日期计算</span>
        </div>
        <el-table :data="studentDurationRows" border height="300">
          <el-table-column prop="student_id" label="学号" width="130" />
          <el-table-column prop="name" label="姓名" width="120" />
          <el-table-column prop="class_name" label="班级" min-width="140" />
          <el-table-column prop="duration_days" label="就业时长（天）" min-width="160" />
        </el-table>
      </article>
      <article class="page-surface">
        <div class="card-title">
          <h4>班级平均就业时长</h4>
          <span>按班级汇总就业效率</span>
        </div>
        <el-table :data="durationRows" border height="300">
          <el-table-column prop="class_name" label="班级" min-width="160" />
          <el-table-column prop="average_duration_days" label="平均就业时长（天）" min-width="180" />
        </el-table>
      </article>
    </div>
  </section>
</template>
