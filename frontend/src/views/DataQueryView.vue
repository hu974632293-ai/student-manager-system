<script setup lang="ts">
import { computed, ref } from "vue";

import { notifyError } from "@/api/http";
import { runDataQuery } from "@/api/dataQuery";
import type { DataQueryResult } from "@/types";

const question = ref("");
const limit = ref(100);
const loading = ref(false);
const result = ref<DataQueryResult | null>(null);

const hasRows = computed(() => Boolean(result.value?.rows.length));
const columnLabels: Record<string, string> = {
  student_id: "学号",
  student_name: "学生姓名",
  name: "姓名",
  gender: "性别",
  age: "年龄",
  major: "专业",
  class_id: "班级编号",
  class_name: "班级",
  teacher_id: "教师编号",
  teacher_name: "教师姓名",
  exam_round: "考试轮次",
  score: "分数",
  average_score: "平均分",
  avg_score: "平均分",
  min_score: "最低分",
  max_score: "最高分",
  score_count: "成绩记录数",
  student_count: "学生人数",
  count: "数量",
  total: "总数",
  company_name: "公司",
  job_title: "岗位",
  salary: "薪资",
  employment_date: "就业日期",
  duration_days: "就业时长（天）",
  average_duration_days: "平均就业时长（天）",
};

function columnLabel(column: string) {
  return columnLabels[column] || column.replace(/_/g, " ");
}

async function submit() {
  const text = question.value.trim();
  if (!text || loading.value) return;
  loading.value = true;
  try {
    result.value = await runDataQuery({
      question: text,
      limit: limit.value,
      show_sql: true,
    });
  } catch (error) {
    notifyError(error);
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <section class="data-query-page">
    <aside class="workbench-side">
      <h3>智能问数</h3>
      <p>输入自然语言问题，系统会转换为只读查询语句，并返回中文摘要和表格结果。</p>
      <div class="query-examples">
        <button type="button" @click="question = '哪个班级平均成绩最高？'">哪个班级平均成绩最高？</button>
        <button type="button" @click="question = '薪资最高的前 5 名学生是谁？'">薪资最高的前 5 名学生是谁？</button>
        <button type="button" @click="question = '每个班级男女学生人数是多少？'">每个班级男女学生人数是多少？</button>
      </div>
    </aside>

    <main class="data-query-main">
      <section class="query-composer">
        <el-input
          v-model="question"
          type="textarea"
          :rows="4"
          resize="none"
          placeholder="例如：哪个班级平均成绩最高？"
          @keyup.ctrl.enter="submit"
        />
        <div class="query-actions">
          <el-input-number v-model="limit" :min="1" :max="100" controls-position="right" />
          <el-button type="primary" :loading="loading" @click="submit">查询</el-button>
        </div>
      </section>

      <section v-if="result" class="query-result">
        <div class="result-summary">
          <h3>查询结论</h3>
          <p>{{ result.summary }}</p>
        </div>

        <div class="sql-block">
          <span>执行查询语句</span>
          <pre>{{ result.sql || "已隐藏" }}</pre>
        </div>

        <div class="result-table">
          <div class="table-footer">
            <span>返回 {{ result.row_count }} 条数据</span>
          </div>
          <el-table v-if="hasRows" :data="result.rows" border height="420">
            <el-table-column
              v-for="column in result.columns"
              :key="column"
              :prop="column"
              :label="columnLabel(column)"
              min-width="140"
              show-overflow-tooltip
            />
          </el-table>
          <div v-else class="empty-state">没有查询到符合条件的数据</div>
        </div>
      </section>

      <section v-else class="empty-state">
        输入问题后点击查询，这里会展示查询语句、摘要和结果表格。
      </section>
    </main>

    <aside class="workbench-side">
      <h3>安全边界</h3>
      <p>当前仅支持学生、班级、教师、成绩和就业相关白名单表，只执行 SELECT 查询。</p>
      <p>教师账号会按授课班级限制可查询学生范围。</p>
    </aside>
  </section>
</template>
