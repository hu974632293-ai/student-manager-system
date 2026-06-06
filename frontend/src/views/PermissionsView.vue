<script setup lang="ts">
import { computed } from "vue";

import { modules, roleLabels } from "@/permissions";
import type { Role } from "@/types";

const roles: Role[] = ["admin", "teacher", "student", "consultant"];
const visibleModules = computed(() => modules.filter((item) => !item.hidden));
</script>

<template>
  <section class="page-surface">
    <div class="section-heading">
      <div>
        <h3>权限矩阵</h3>
        <p>按当前权限配置展示角色可访问模块；真实安全边界由后端依赖和 service 数据范围控制。</p>
      </div>
    </div>

    <el-table :data="visibleModules" border stripe height="620">
      <el-table-column prop="title" label="模块" width="150" />
      <el-table-column prop="subtitle" label="说明" min-width="240" />
      <el-table-column v-for="role in roles" :key="role" :label="roleLabels[role]" width="120" align="center">
        <template #default="{ row }">
          <el-tag v-if="row.roles.includes(role)" type="success">允许</el-tag>
          <el-tag v-else type="info">无</el-tag>
        </template>
      </el-table-column>
    </el-table>
  </section>
</template>
