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
  list: (page: number, size: number) => Promise<{ rows: Row[]; total: number }>;
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
const editingRow = ref<Row | null>(null);
const form = reactive<Row>({});

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
    async list(currentPage, size) {
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
    async list(currentPage, size) {
      const data = await request<{ items?: Row[]; total?: number }>(
        `/score/query/?page=${currentPage}&page_size=${size}`,
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
    async list(currentPage, size) {
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
const visibleFields = computed(() =>
  (config.value?.fields || []).filter((field) => {
    if (editingRow.value && field.createOnly) return false;
    if (!editingRow.value && field.updateOnly) return false;
    return true;
  }),
);

async function load() {
  if (!config.value) return;
  loading.value = true;
  try {
    const data = await config.value.list(page.value, pageSize.value);
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

function copyJson(row: Row) {
  navigator.clipboard.writeText(JSON.stringify(row, null, 2));
  ElMessage.success("已复制");
}

watch(
  () => route.path,
  () => {
    page.value = 1;
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
        <el-button :loading="loading" @click="load">刷新</el-button>
        <el-button v-if="canWrite && config?.create" type="primary" @click="openCreate">新增</el-button>
      </div>
    </div>

    <el-table :data="rows" border stripe v-loading="loading" height="560">
      <el-table-column
        v-for="column in config?.columns"
        :key="column.key"
        :prop="column.key"
        :label="column.label"
        min-width="130"
        show-overflow-tooltip
      />
      <el-table-column label="操作" width="180" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="copyJson(row)">复制</el-button>
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
  </section>
</template>
