<script setup lang="ts">
import { ElMessage } from "element-plus";
import { computed, onMounted, ref } from "vue";

import { notifyError, request } from "@/api/http";

interface ChatResult {
  session_id: string;
  reply: string;
  context_message_count: number;
  memory_count: number;
  saved_memory?: string | null;
  compression_applied?: boolean;
  retrieval_count?: number;
}

interface MemoryItem {
  id: number;
  content: string;
  source: string;
  is_active: boolean;
}

interface SessionSummary {
  session_id: string;
  summary: string;
  summary_updated_at?: string | null;
  message_count?: number;
}

const prompt = ref("");
const sessionId = ref("");
const loading = ref(false);
const memoryLoading = ref(false);
const summaryLoading = ref(false);
const newMemory = ref("");
const searchQuery = ref("");
const summary = ref<SessionSummary | null>(null);
const memories = ref<MemoryItem[]>([]);
const searchItems = ref<Record<string, unknown>[]>([]);
const messages = ref<{ role: "user" | "assistant"; content: string }[]>([]);

const summaryText = computed(() => summary.value?.summary || "当前会话暂无摘要内容");

function formatTime(value?: string | null) {
  if (!value) return "暂未生成";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("zh-CN", { hour12: false });
}

async function send() {
  const message = prompt.value.trim();
  if (!message) return;
  loading.value = true;
  messages.value.push({ role: "user", content: message });
  prompt.value = "";
  try {
    const data = await request<ChatResult>("/ai/chat", {
      method: "POST",
      body: JSON.stringify({ session_id: sessionId.value || undefined, message }),
    });
    sessionId.value = data.session_id;
    messages.value.push({ role: "assistant", content: data.reply || "助手未返回有效内容" });
    if (data.saved_memory) await loadMemories();
  } catch (error) {
    const message = error instanceof Error ? error.message : "请求失败";
    messages.value.push({ role: "assistant", content: `请求失败：${message}` });
    notifyError(error);
  } finally {
    loading.value = false;
  }
}

async function loadMemories() {
  memoryLoading.value = true;
  try {
    const data = await request<{ total: number; items: MemoryItem[] }>("/ai/memories?limit=50");
    memories.value = data.items || [];
  } catch (error) {
    notifyError(error);
  } finally {
    memoryLoading.value = false;
  }
}

async function addMemory() {
  const content = newMemory.value.trim();
  if (!content) {
    ElMessage.warning("请填写记忆内容");
    return;
  }
  try {
    await request<MemoryItem>("/ai/memories", {
      method: "POST",
      body: JSON.stringify({ content }),
    });
    newMemory.value = "";
    ElMessage.success("记忆已添加");
    await loadMemories();
  } catch (error) {
    notifyError(error);
  }
}

async function removeMemory(id: number) {
  try {
    await request(`/ai/memories/${id}`, { method: "DELETE" });
    ElMessage.success("记忆已删除");
    await loadMemories();
  } catch (error) {
    notifyError(error);
  }
}

async function searchMemories() {
  const q = searchQuery.value.trim();
  if (!q) return;
  try {
    const data = await request<{ items: Record<string, unknown>[] }>(`/ai/memories/search?q=${encodeURIComponent(q)}&limit=10`);
    searchItems.value = data.items || [];
  } catch (error) {
    notifyError(error);
  }
}

async function loadSummary(regenerate = false) {
  if (!sessionId.value) {
    ElMessage.warning("请先创建或填写会话编号");
    return;
  }
  summaryLoading.value = true;
  try {
    summary.value = await request<SessionSummary>(
      `/ai/sessions/${sessionId.value}/${regenerate ? "summarize" : "summary"}`,
      { method: regenerate ? "POST" : "GET" },
    );
  } catch (error) {
    notifyError(error);
  } finally {
    summaryLoading.value = false;
  }
}

onMounted(loadMemories);
</script>

<template>
  <section class="ai-workbench expanded">
    <aside class="workbench-side">
      <h3>会话</h3>
      <p>填写会话编号可继续已有对话；留空会自动创建。</p>
      <el-input v-model="sessionId" clearable placeholder="会话编号" />
      <div class="side-actions">
        <el-button :loading="summaryLoading" @click="loadSummary(false)">查看摘要</el-button>
        <el-button :loading="summaryLoading" @click="loadSummary(true)">重新摘要</el-button>
      </div>
      <div v-if="summary" class="summary-card">
        <el-descriptions :column="1" size="small" border>
          <el-descriptions-item label="会话编号">{{ summary.session_id }}</el-descriptions-item>
          <el-descriptions-item label="消息数量">{{ summary.message_count ?? 0 }}</el-descriptions-item>
          <el-descriptions-item label="更新时间">{{ formatTime(summary.summary_updated_at) }}</el-descriptions-item>
        </el-descriptions>
        <p>{{ summaryText }}</p>
      </div>
    </aside>

    <main class="chat-panel">
      <div class="chat-list">
        <div v-if="!messages.length" class="empty-state compact">开始一次普通问答</div>
        <article v-for="(item, index) in messages" :key="index" :class="['chat-message', item.role]">
          <strong>{{ item.role === "user" ? "我" : "助手" }}</strong>
          <p>{{ item.content }}</p>
        </article>
      </div>
      <div class="composer">
        <el-input v-model="prompt" type="textarea" :rows="3" resize="none" placeholder="输入问题后点击发送，也可按 Ctrl + Enter" @keyup.ctrl.enter="send" />
        <el-button type="primary" :loading="loading" @click="send">发送</el-button>
      </div>
    </main>

    <aside class="workbench-side memory-side" v-loading="memoryLoading">
      <h3>长期记忆</h3>
      <p>支持手动添加、删除和语义搜索当前用户记忆。</p>
      <el-input v-model="newMemory" type="textarea" :rows="3" placeholder="例如：记住我的专业是软件工程" />
      <el-button type="primary" class="full-button" @click="addMemory">添加记忆</el-button>
      <el-input v-model="searchQuery" placeholder="搜索记忆" @keyup.enter="searchMemories" />
      <el-button class="full-button" @click="searchMemories">语义搜索</el-button>
      <div class="memory-list">
        <article v-for="item in memories" :key="item.id" class="memory-card">
          <p>{{ item.content }}</p>
          <el-button link type="danger" @click="removeMemory(item.id)">删除</el-button>
        </article>
      </div>
      <div v-if="searchItems.length" class="memory-list">
        <strong>搜索结果</strong>
        <article v-for="item in searchItems" :key="String(item.id)" class="memory-card">
          <p>{{ item.content }}</p>
          <small>相似度：{{ item.similarity }}</small>
        </article>
      </div>
    </aside>
  </section>
</template>
