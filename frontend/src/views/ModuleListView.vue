<script setup lang="ts">
import { ElMessage, ElMessageBox } from "element-plus";
import { computed, reactive, ref, watch } from "vue";
import { useRoute } from "vue-router";

import { notifyError, request } from "@/api/http";
import { useAuthStore } from "@/stores/auth";
import type { TableColumn } from "@/types";

type Row = Record<string, unknown>;
type FieldType = "text" | "number" | "date" | "textarea" | "switch";

interface FormField {
  key: string;
  label: string;
  type?: FieldType;
  required?: boolean;
  createOnly?: boolean;
  updateOnly?: boolean;
  readonlyOnEdit?: boolean;
}

interface ModuleConfig {
  title: string;
  description: string;
  writePermission?: string;
  columns: TableColumn[];
  fields: FormField[];
  filters?: FormField[];
  list: (page: number, size: number, filters?: Row) => Promise<{ rows: Row[]; total: number }>;
  create?: (form: Row) => Promise<unknown>;
  update?: (row: Row, form: Row) => Promise<unknown>;
  remove?: (row: Row) => Promise<unknown>;
}

const route = useRoute();
const auth = useAuthStore();
const loading = ref(false);
const saving = ref(false);
const rows = ref<Row[]>([]);
const total = ref(0);
const page = ref(1);
const pageSize = ref(10);
const dialogVisible = ref(false);
const detailVisible = ref(false);
const commentVisible = ref(false);
const bulkScoreVisible = ref(false);
const editingRow = ref<Row | null>(null);
const detailRow = ref<Row | null>(null);
const commentRow = ref<Row | null>(null);
const searchKeyword = ref("");
const form = reactive<Row>({});
const filterForm = reactive<Row>({});
const commentForm = reactive({
  style: "正式",
  extra_notes: "",
});
const commentLoading = ref(false);
const commentResult = ref<Row | null>(null);
const bulkScoreText = ref("");
const bulkScoreLoading = ref(false);

function toQuery(data: Row) {
  const params = new URLSearchParams();
  Object.entries(data).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") params.set(key, String(value));
  });
  return params.toString();
}

function normalizeForm(fields: FormField[], source: Row = {}) {
  Object.keys(form).forEach((key) => delete form[key]);
  fields.forEach((field) => {
    if (field.createOnly && editingRow.value) return;
    if (field.updateOnly && !editingRow.value) return;
    const value = source[field.key];
    form[field.key] = value ?? (field.type === "switch" ? false : "");
  });
}

function cleanPayload() {
  const payload: Row = {};
  Object.entries(form).forEach(([key, value]) => {
    if (value !== "" && value !== undefined && value !== null) payload[key] = value;
  });
  return payload;
}

async function jsonRequest(url: string, method: string, body?: Row) {
  return request(url, {
    method,
    body: body ? JSON.stringify(body) : undefined,
  });
}

function normalizeFilterForm(fields: FormField[] = []) {
  Object.keys(filterForm).forEach((key) => delete filterForm[key]);
  fields.forEach((field) => {
    filterForm[field.key] = "";
  });
}

function cleanFilters() {
  const filters: Row = {};
  Object.entries(filterForm).forEach(([key, value]) => {
    if (value !== "" && value !== undefined && value !== null) filters[key] = value;
  });
  return filters;
}

function hasFilters(filters: Row) {
  return Object.keys(filters).length > 0;
}

function paginateLocalRows(items: Row[], currentPage: number, size: number) {
  const start = (currentPage - 1) * size;
  return { rows: items.slice(start, start + size), total: items.length };
}

function uniqueRows(items: Row[], key: string) {
  const seen = new Set<string>();
  return items.filter((item) => {
    const value = String(item[key] ?? "");
    if (!value || seen.has(value)) return false;
    seen.add(value);
    return true;
  });
}

function filterJobRows(items: Row[], filters: Row) {
  return items.filter((item) => {
    if (filters.student_id && String(item.student_id) !== String(filters.student_id)) return false;
    if (filters.class_name && String(item.class_name) !== String(filters.class_name)) return false;
    if (filters.min_salary !== undefined && Number(item.salary ?? 0) < Number(filters.min_salary)) return false;
    if (filters.max_salary !== undefined && Number(item.salary ?? 0) > Number(filters.max_salary)) return false;
    return true;
  });
}

const configs: Record<string, ModuleConfig> = {
  students: {
    title: "学生管理",
    description: "学生档案支持分页查询、新增、编辑、删除；数据范围由后端权限控制。",
    writePermission: "students:write",
    columns: [
      { key: "student_id", label: "学号" },
      { key: "name", label: "姓名" },
      { key: "class_id", label: "班级ID" },
      { key: "major", label: "专业" },
      { key: "education", label: "学历" },
      { key: "gender", label: "性别" },
      { key: "age", label: "年龄" },
    ],
    fields: [
      { key: "student_id", label: "学号", required: true, readonlyOnEdit: true },
      { key: "class_id", label: "班级ID", type: "number", required: true },
      { key: "name", label: "姓名", required: true },
      { key: "gender", label: "性别" },
      { key: "age", label: "年龄", type: "number" },
      { key: "native_place", label: "籍贯" },
      { key: "graduate_school", label: "毕业学校" },
      { key: "major", label: "专业" },
      { key: "education", label: "学历" },
      { key: "enrollment_date", label: "入学日期", type: "date" },
      { key: "graduation_date", label: "毕业日期", type: "date" },
      { key: "consultant_id", label: "顾问教师ID", type: "number" },
    ],
    filters: [
      { key: "student_id", label: "学号" },
      { key: "student_name", label: "姓名" },
      { key: "class_id", label: "班级ID", type: "number" },
    ],
    async list(currentPage, size, filters = {}) {
      if (hasFilters(filters)) {
        const data = await request<{ select_id?: Row | null; select_name?: Row | null; class_id?: Row[] }>(
          `/students/one?${toQuery(filters)}`,
        );
        const items = uniqueRows(
          [data.select_id, data.select_name, ...(data.class_id || [])].filter(Boolean) as Row[],
          "student_id",
        );
        return paginateLocalRows(items, currentPage, size);
      }
      const data = await request<{ students?: Row[]; total?: number }>(
        `/students?skip=${(currentPage - 1) * size}&limit=${size}`,
      );
      return { rows: data.students || [], total: Number(data.total || 0) };
    },
    create: (payload) => jsonRequest("/students", "POST", payload),
    update: (row, payload) => request(`/update_student/${row.student_id}?${toQuery(payload)}`, { method: "PUT" }),
    remove: (row) => request(`/students_delete/?student_id=${row.student_id}`, { method: "POST" }),
  },
  classes: {
    title: "班级管理",
    description: "班级信息支持分页查询、新增、编辑、删除；教师只能查看授课班级。",
    writePermission: "classes:write",
    columns: [
      { key: "id", label: "ID" },
      { key: "class_id", label: "班级编号" },
      { key: "head_teacher", label: "班主任" },
      { key: "start_date", label: "开班日期" },
      { key: "description", label: "描述" },
    ],
    fields: [
      { key: "id", label: "ID", type: "number", updateOnly: true, readonlyOnEdit: true },
      { key: "class_id", label: "班级编号", required: true },
      { key: "head_teacher", label: "班主任" },
      { key: "start_date", label: "开班日期", type: "date" },
      { key: "description", label: "描述", type: "textarea" },
    ],
    async list(currentPage, size) {
      const data = await request<{ items?: Row[]; total?: number }>(`/classes/?page=${currentPage}&size=${size}`);
      return { rows: data.items || [], total: Number(data.total || 0) };
    },
    create: (payload) => jsonRequest("/classes/", "POST", { ...payload, teacher_ids: [] }),
    update: (_row, payload) => jsonRequest("/classes/", "PUT", payload),
    remove: (row) => request(`/classes/${row.id}`, { method: "DELETE" }),
  },
  teachers: {
    title: "教师管理",
    description: "教师档案当前由后端返回全量列表，前端按页展示。",
    writePermission: "teachers:write",
    columns: [
      { key: "id", label: "ID" },
      { key: "teacher_number", label: "工号" },
      { key: "name", label: "姓名" },
      { key: "gender", label: "性别" },
      { key: "subject", label: "科目" },
      { key: "phone", label: "电话" },
      { key: "email", label: "邮箱" },
    ],
    fields: [
      { key: "id", label: "ID", type: "number", updateOnly: true, readonlyOnEdit: true },
      { key: "teacher_number", label: "工号", required: true },
      { key: "name", label: "姓名", required: true },
      { key: "gender", label: "性别" },
      { key: "subject", label: "科目" },
      { key: "phone", label: "电话" },
      { key: "email", label: "邮箱" },
      { key: "is_active", label: "启用", type: "switch", updateOnly: true },
    ],
    async list(currentPage, size) {
      const data = await request<Row[]>("/teacher/list");
      const start = (currentPage - 1) * size;
      return { rows: (data || []).slice(start, start + size), total: (data || []).length };
    },
    create: (payload) => jsonRequest("/teacher/add", "POST", payload),
    update: (_row, payload) => jsonRequest("/teacher/update", "PUT", payload),
    remove: (row) => request(`/teacher/delete/${row.id}`, { method: "DELETE" }),
  },
  scores: {
    title: "成绩管理",
    description: "成绩支持分页查询、新增、编辑、删除；学生账号只能查看本人数据。",
    writePermission: "scores:write",
    columns: [
      { key: "student_id", label: "学号" },
      { key: "student_name", label: "姓名" },
      { key: "exam_round", label: "考试轮次" },
      { key: "score", label: "分数" },
      { key: "remark", label: "备注" },
    ],
    fields: [
      { key: "student_id", label: "学号", required: true, readonlyOnEdit: true },
      { key: "exam_round", label: "考试轮次", type: "number", required: true, readonlyOnEdit: true },
      { key: "score", label: "分数", type: "number" },
      { key: "remark", label: "备注", type: "textarea" },
    ],
    filters: [
      { key: "student_id", label: "学号" },
      { key: "exam_round", label: "考试轮次", type: "number" },
      { key: "min_score", label: "最低分", type: "number" },
      { key: "max_score", label: "最高分", type: "number" },
    ],
    async list(currentPage, size, filters = {}) {
      if (filters.min_score !== undefined || filters.max_score !== undefined) {
        const params = new URLSearchParams({
          min_score: String(filters.min_score ?? 0),
          max_score: String(filters.max_score ?? 100),
          page: String(currentPage),
          page_size: String(size),
        });
        const data = await request<{ items?: Row[]; total?: number }>(`/score/range/?${params.toString()}`);
        let items = data.items || [];
        if (filters.student_id) items = items.filter((item) => String(item.student_id) === String(filters.student_id));
        if (filters.exam_round) items = items.filter((item) => Number(item.exam_round) === Number(filters.exam_round));
        return { rows: items, total: Number(data.total || items.length) };
      }
      const params = new URLSearchParams({
        page: String(currentPage),
        page_size: String(size),
      });
      if (filters.student_id) params.set("student_id", String(filters.student_id));
      if (filters.exam_round) params.set("exam_round", String(filters.exam_round));
      const data = await request<{ items?: Row[]; total?: number }>(
        `/score/query/?${params.toString()}`,
      );
      return { rows: data.items || [], total: Number(data.total || 0) };
    },
    create: (payload) => jsonRequest("/score/", "POST", payload),
    update: (row, payload) => jsonRequest(`/score/update/${row.student_id}/${row.exam_round}`, "PUT", payload),
    remove: (row) => request(`/score/delete/${row.student_id}/${row.exam_round}`, { method: "DELETE" }),
  },
  employment: {
    title: "就业管理",
    description: "就业记录支持分页查询、新增、编辑、删除；顾问和教师按后端范围过滤。",
    writePermission: "employment:write",
    columns: [
      { key: "id", label: "ID" },
      { key: "student_id", label: "学号" },
      { key: "name", label: "姓名" },
      { key: "class_name", label: "班级" },
      { key: "company_name", label: "公司" },
      { key: "position", label: "岗位" },
      { key: "salary", label: "薪资" },
    ],
    fields: [
      { key: "student_id", label: "学号", required: true, readonlyOnEdit: true },
      { key: "name", label: "姓名", required: true },
      { key: "class_name", label: "班级", required: true },
      { key: "job_open_date", label: "开岗日期", type: "date" },
      { key: "offer_date", label: "Offer 日期", type: "date" },
      { key: "company_name", label: "公司" },
      { key: "position", label: "岗位" },
      { key: "salary", label: "薪资", type: "number", required: true },
    ],
    filters: [
      { key: "student_id", label: "学号" },
      { key: "class_name", label: "班级" },
      { key: "min_salary", label: "最低薪资", type: "number" },
      { key: "max_salary", label: "最高薪资", type: "number" },
    ],
    async list(currentPage, size, filters = {}) {
      if (hasFilters(filters)) {
        let items: Row[] = [];
        if (filters.student_id) {
          items = await request<Row[]>(`/employment/students/${encodeURIComponent(String(filters.student_id))}`);
        } else if (filters.class_name) {
          items = await request<Row[]>(`/employment/class/${encodeURIComponent(String(filters.class_name))}`);
        } else {
          items = await request<Row[]>(`/jobs/salary-range?${toQuery(filters)}`);
        }
        return paginateLocalRows(filterJobRows(items || [], filters), currentPage, size);
      }
      const data = await request<{ list?: Row[]; total?: number }>(`/jobs/page?page=${currentPage}&size=${size}`);
      return { rows: data.list || [], total: Number(data.total || 0) };
    },
    create: (payload) => jsonRequest("/employment/students/add", "POST", payload),
    update: (row, payload) => jsonRequest(`/employment/students/${row.id}`, "POST", payload),
    remove: (row) => request(`/employment/students/by-student-id/${row.student_id}`, { method: "DELETE" }),
  },
  statistics: {
    title: "统计结果",
    description: "统计页面当前按后端只读接口展示，不提供 CRUD 操作。",
    columns: [
      { key: "name", label: "姓名" },
      { key: "class_name", label: "班级" },
      { key: "company_name", label: "公司" },
      { key: "salary", label: "薪资" },
    ],
    fields: [],
    async list() {
      const data = await request<Row[]>("/statistics/employment/top5-salary?limit=20");
      return { rows: Array.isArray(data) ? data : [], total: Array.isArray(data) ? data.length : 0 };
    },
  },
};

const moduleKey = computed(() => String(route.meta.module || ""));
const config = computed(() => configs[moduleKey.value]);
const canWrite = computed(() => Boolean(config.value?.writePermission && auth.permissions.includes(config.value.writePermission)));
const canGenerateComment = computed(() => moduleKey.value === "students" && ["admin", "teacher", "consultant"].includes(String(auth.role || "")));
const canBulkCreateScores = computed(() => moduleKey.value === "scores" && canWrite.value);
const filteredRows = computed(() => {
  const keyword = searchKeyword.value.trim().toLowerCase();
  if (!keyword) return rows.value;
  return rows.value.filter((row) => JSON.stringify(row).toLowerCase().includes(keyword));
});
const visibleFields = computed(() =>
  (config.value?.fields || []).filter((field) => {
    if (editingRow.value && field.createOnly) return false;
    if (!editingRow.value && field.updateOnly) return false;
    return true;
  }),
);
const filterFields = computed(() => config.value?.filters || []);
const detailItems = computed(() => {
  if (!detailRow.value || !config.value) return [];
  return config.value.columns
    .filter((column) => Object.prototype.hasOwnProperty.call(detailRow.value, column.key))
    .map((column) => ({
      key: column.key,
      label: column.label,
      value: formatValue(detailRow.value?.[column.key]),
    }));
});

function formatValue(value: unknown) {
  if (value === null || value === undefined || value === "") return "-";
  if (typeof value === "boolean") return value ? "是" : "否";
  return String(value);
}

async function load() {
  if (!config.value) return;
  loading.value = true;
  try {
    const data = await config.value.list(page.value, pageSize.value, cleanFilters());
    rows.value = data.rows;
    total.value = data.total;
  } catch (error) {
    rows.value = [];
    total.value = 0;
    notifyError(error);
  } finally {
    loading.value = false;
  }
}

async function applyFilters() {
  page.value = 1;
  await load();
}

async function resetFilters() {
  normalizeFilterForm(filterFields.value);
  searchKeyword.value = "";
  page.value = 1;
  await load();
}

function openCreate() {
  if (!config.value) return;
  editingRow.value = null;
  normalizeForm(config.value.fields);
  dialogVisible.value = true;
}

function openEdit(row: Row) {
  if (!config.value) return;
  editingRow.value = row;
  normalizeForm(config.value.fields, row);
  dialogVisible.value = true;
}

function validateForm() {
  for (const field of visibleFields.value) {
    if (field.required && (form[field.key] === "" || form[field.key] === undefined || form[field.key] === null)) {
      ElMessage.warning(`请填写${field.label}`);
      return false;
    }
  }
  return true;
}

async function save() {
  if (!config.value || !validateForm()) return;
  saving.value = true;
  try {
    const payload = cleanPayload();
    if (editingRow.value) {
      await config.value.update?.(editingRow.value, payload);
      ElMessage.success("更新成功");
    } else {
      await config.value.create?.(payload);
      ElMessage.success("新增成功");
    }
    dialogVisible.value = false;
    await load();
  } catch (error) {
    notifyError(error);
  } finally {
    saving.value = false;
  }
}

async function remove(row: Row) {
  if (!config.value?.remove) return;
  try {
    await ElMessageBox.confirm("确认删除这条记录？", "删除确认", {
      confirmButtonText: "删除",
      cancelButtonText: "取消",
      type: "warning",
    });
    await config.value.remove(row);
    ElMessage.success("删除成功");
    if (rows.value.length === 1 && page.value > 1) page.value -= 1;
    await load();
  } catch (error) {
    if (error !== "cancel") notifyError(error);
  }
}

async function copyDetail(row: Row) {
  if (!config.value) return;
  const text = config.value.columns
    .filter((column) => Object.prototype.hasOwnProperty.call(row, column.key))
    .map((column) => `${column.label}：${formatValue(row[column.key])}`)
    .join("\n");
  try {
    await navigator.clipboard.writeText(text);
    ElMessage.success("详情已复制");
  } catch {
    ElMessage.error("复制失败，请手动选择详情内容");
  }
}

function openDetail(row: Row) {
  detailRow.value = row;
  detailVisible.value = true;
}

function openComment(row: Row) {
  commentRow.value = row;
  commentResult.value = null;
  commentForm.style = "正式";
  commentForm.extra_notes = "";
  commentVisible.value = true;
}

async function generateComment() {
  if (!commentRow.value?.student_id) {
    ElMessage.warning("缺少学生学号，无法生成评语");
    return;
  }
  commentLoading.value = true;
  try {
    commentResult.value = await request<Row>("/students/comment", {
      method: "POST",
      body: JSON.stringify({
        student_id: commentRow.value.student_id,
        style: commentForm.style,
        extra_notes: commentForm.extra_notes || undefined,
      }),
    });
    ElMessage.success("评语生成成功");
  } catch (error) {
    notifyError(error);
  } finally {
    commentLoading.value = false;
  }
}

async function copyComment() {
  const text = String(commentResult.value?.comment || "");
  if (!text) return;
  try {
    await navigator.clipboard.writeText(text);
    ElMessage.success("评语已复制");
  } catch {
    ElMessage.error("复制失败，请手动选择评语内容");
  }
}

function openBulkScores() {
  bulkScoreText.value = "";
  bulkScoreVisible.value = true;
}

function parseBulkScores() {
  return bulkScoreText.value
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line, index) => {
      const [studentId, examRound, score, ...remarkParts] = line.split(/[,，\t]/).map((item) => item.trim());
      if (!studentId || !examRound || !score) {
        throw new Error(`第 ${index + 1} 行请按“学号,考试轮次,分数,备注”填写`);
      }
      const examRoundValue = Number(examRound);
      const scoreValue = Number(score);
      if (!Number.isFinite(examRoundValue) || examRoundValue < 1) {
        throw new Error(`第 ${index + 1} 行考试轮次必须是大于 0 的数字`);
      }
      if (!Number.isFinite(scoreValue) || scoreValue < 0 || scoreValue > 100) {
        throw new Error(`第 ${index + 1} 行分数必须在 0 到 100 之间`);
      }
      const item: Row = {
        student_id: studentId,
        exam_round: examRoundValue,
        score: scoreValue,
      };
      const remark = remarkParts.join("，").trim();
      if (remark) item.remark = remark;
      return item;
    });
}

async function submitBulkScores() {
  let scores: Row[] = [];
  try {
    scores = parseBulkScores();
  } catch (error) {
    ElMessage.warning(error instanceof Error ? error.message : "批量成绩格式不正确");
    return;
  }
  if (!scores.length) {
    ElMessage.warning("请至少填写一条成绩");
    return;
  }
  bulkScoreLoading.value = true;
  try {
    await request("/score/bulk/", {
      method: "POST",
      body: JSON.stringify(scores),
    });
    ElMessage.success(`已提交 ${scores.length} 条成绩`);
    bulkScoreVisible.value = false;
    await load();
  } catch (error) {
    notifyError(error);
  } finally {
    bulkScoreLoading.value = false;
  }
}

watch(
  () => route.path,
  () => {
    page.value = 1;
    normalizeFilterForm(config.value?.filters);
    load();
  },
  { immediate: true },
);
</script>

<template>
  <section class="page-surface">
    <div class="section-heading">
      <div>
        <h3>{{ config?.title }}</h3>
        <p>{{ config?.description }}</p>
      </div>
      <div class="toolbar-actions">
        <el-input v-model="searchKeyword" clearable placeholder="筛选当前页数据" style="width: 220px" />
        <el-button :loading="loading" @click="load">刷新</el-button>
        <el-button v-if="canBulkCreateScores" @click="openBulkScores">批量新增</el-button>
        <el-button v-if="canWrite && config?.create" type="primary" @click="openCreate">新增</el-button>
      </div>
    </div>

    <div v-if="filterFields.length" class="filter-bar">
      <el-form label-position="top">
        <div class="filter-grid">
          <el-form-item v-for="field in filterFields" :key="field.key" :label="field.label">
            <el-input-number
              v-if="field.type === 'number'"
              v-model="filterForm[field.key]"
              controls-position="right"
              class="full-input"
            />
            <el-input v-else v-model="filterForm[field.key]" clearable />
          </el-form-item>
          <div class="filter-actions">
            <el-button type="primary" :loading="loading" @click="applyFilters">查询</el-button>
            <el-button @click="resetFilters">重置</el-button>
          </div>
        </div>
      </el-form>
    </div>

    <el-table :data="filteredRows" border stripe v-loading="loading" height="560" empty-text="暂无数据">
      <el-table-column
        v-for="column in config?.columns"
        :key="column.key"
        :prop="column.key"
        :label="column.label"
        min-width="130"
        show-overflow-tooltip
      />
      <el-table-column label="操作" width="260" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openDetail(row)">详情</el-button>
          <el-button link type="primary" @click="copyDetail(row)">复制详情</el-button>
          <el-button v-if="canGenerateComment" link type="primary" @click="openComment(row)">生成评语</el-button>
          <el-button v-if="canWrite && config?.update" link type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button v-if="canWrite && config?.remove" link type="danger" @click="remove(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="table-footer">
      <span>共 {{ total }} 条</span>
      <el-pagination
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        :total="total"
        layout="sizes, prev, pager, next, jumper"
        background
        @size-change="load"
        @current-change="load"
      />
    </div>

    <el-dialog v-model="dialogVisible" :title="editingRow ? '编辑记录' : '新增记录'" width="640px">
      <el-form label-position="top">
        <el-form-item v-for="field in visibleFields" :key="field.key" :label="field.label">
          <el-input-number
            v-if="field.type === 'number'"
            v-model="form[field.key]"
            :disabled="field.readonlyOnEdit && Boolean(editingRow)"
            controls-position="right"
            class="full-input"
          />
          <el-date-picker
            v-else-if="field.type === 'date'"
            v-model="form[field.key]"
            :disabled="field.readonlyOnEdit && Boolean(editingRow)"
            type="date"
            value-format="YYYY-MM-DD"
            class="full-input"
          />
          <el-switch
            v-else-if="field.type === 'switch'"
            v-model="form[field.key]"
            :disabled="field.readonlyOnEdit && Boolean(editingRow)"
          />
          <el-input
            v-else
            v-model="form[field.key]"
            :type="field.type === 'textarea' ? 'textarea' : 'text'"
            :rows="3"
            :disabled="field.readonlyOnEdit && Boolean(editingRow)"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="detailVisible" title="记录详情" size="520px">
      <el-descriptions v-if="detailRow" :column="1" border>
        <el-descriptions-item v-for="item in detailItems" :key="item.key" :label="item.label">
          {{ item.value }}
        </el-descriptions-item>
      </el-descriptions>
    </el-drawer>

    <el-dialog v-model="commentVisible" title="生成学生评语" width="680px">
      <el-form label-position="top">
        <el-form-item label="学生">
          <el-input :model-value="`${commentRow?.name || '-'}（${commentRow?.student_id || '-'}）`" disabled />
        </el-form-item>
        <el-form-item label="评语口吻">
          <el-select v-model="commentForm.style" class="full-input">
            <el-option label="正式" value="正式" />
            <el-option label="鼓励" value="鼓励" />
            <el-option label="简洁" value="简洁" />
            <el-option label="详细" value="详细" />
            <el-option label="班主任口吻" value="班主任口吻" />
          </el-select>
        </el-form-item>
        <el-form-item label="补充表现">
          <el-input
            v-model="commentForm.extra_notes"
            type="textarea"
            :rows="3"
            resize="none"
            placeholder="例如：近期作业完成稳定，课堂互动更积极"
          />
        </el-form-item>
      </el-form>
      <div v-if="commentResult" class="comment-result">
        <div class="card-title">
          <h4>{{ commentResult.name }}的评语</h4>
          <el-button link type="primary" @click="copyComment">复制评语</el-button>
        </div>
        <p>{{ commentResult.comment }}</p>
      </div>
      <template #footer>
        <el-button @click="commentVisible = false">关闭</el-button>
        <el-button type="primary" :loading="commentLoading" @click="generateComment">生成评语</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="bulkScoreVisible" title="批量新增成绩" width="720px">
      <div class="bulk-score-panel">
        <p>每行一条成绩，格式为：学号,考试轮次,分数,备注。备注可不填。</p>
        <el-input
          v-model="bulkScoreText"
          type="textarea"
          :rows="10"
          resize="vertical"
          placeholder="例如：S202501001,1,86,课堂表现稳定"
        />
      </div>
      <template #footer>
        <el-button @click="bulkScoreVisible = false">取消</el-button>
        <el-button type="primary" :loading="bulkScoreLoading" @click="submitBulkScores">提交成绩</el-button>
      </template>
    </el-dialog>
  </section>
</template>
