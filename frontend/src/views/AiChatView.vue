<script setup lang="ts">
import { ChatLineRound, Delete, EditPen, Plus, Refresh, Search } from "@element-plus/icons-vue";
import { ElMessage, ElMessageBox } from "element-plus";
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

interface ChatMessage {
  id?: number;
  session_id?: string;
  role: "user" | "assistant";
  content: string;
  created_at?: string | null;
}

interface ChatSession {
  id: number;
  session_id: string;
  title: string;
  summary?: string | null;
  summary_updated_at?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
  message_count: number;
  last_message?: string;
}

interface MemoryItem {
  id: number;
  content: string;
  source: string;
  is_active: boolean;
}

interface SessionSummary {
  session_id: string;
  summary: string | null;
  summary_updated_at?: string | null;
  message_count?: number;
}

const prompt = ref("");
const sessionId = ref("");
const sessionKeyword = ref("");
const loading = ref(false);
const sessionLoading = ref(false);
const memoryLoading = ref(false);
const summaryLoading = ref(false);
const newMemory = ref("");
const searchQuery = ref("");
const summary = ref<SessionSummary | null>(null);
const sessions = ref<ChatSession[]>([]);
const memories = ref<MemoryItem[]>([]);
const searchItems = ref<Record<string, unknown>[]>([]);
const messages = ref<ChatMessage[]>([]);

const activeSession = computed(() => sessions.value.find((item) => item.session_id === sessionId.value) || null);
const summaryText = computed(() => summary.value?.summary || "当前会话暂无摘要内容");

function formatTime(value?: string | null) {
  if (!value) return "暂无时间";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("zh-CN", { hour12: false });
}

function normalizeMessageItems(items: ChatMessage[]) {
  return items.filter((item) => item.role === "user" || item.role === "assistant");
}

async function loadSessions() {
  sessionLoading.value = true;
  try {
    const params = new URLSearchParams({ limit: "50" });
    const keyword = sessionKeyword.value.trim();
    if (keyword) params.set("keyword", keyword);
    const data = await request<{ total: number; items: ChatSession[] }>(`/ai/sessions?${params.toString()}`);
    sessions.value = data.items || [];
  } catch (error) {
    notifyError(error);
  } finally {
    sessionLoading.value = false;
  }
}

async function createSession() {
  sessionLoading.value = true;
  try {
    const session = await request<ChatSession>("/ai/sessions", {
      method: "POST",
      body: JSON.stringify({ title: "新对话" }),
    });
    sessionId.value = session.session_id;
    messages.value = [];
    summary.value = null;
    prompt.value = "";
    await loadSessions();
    ElMessage.success("已创建新对话");
  } catch (error) {
    notifyError(error);
  } finally {
    sessionLoading.value = false;
  }
}

async function openSession(session: ChatSession) {
  sessionLoading.value = true;
  try {
    const data = await request<{ session: ChatSession; items: ChatMessage[] }>(`/ai/sessions/${session.session_id}/messages`);
    sessionId.value = session.session_id;
    messages.value = normalizeMessageItems(data.items || []);
    summary.value = data.session.summary
      ? {
          session_id: data.session.session_id,
          summary: data.session.summary,
          summary_updated_at: data.session.summary_updated_at,
          message_count: data.session.message_count,
        }
      : null;
  } catch (error) {
    notifyError(error);
  } finally {
    sessionLoading.value = false;
  }
}

async function renameSession(session: ChatSession) {
  try {
    const result = await ElMessageBox.prompt("请输入新的会话名称", "重命名会话", {
      confirmButtonText: "保存",
      cancelButtonText: "取消",
      inputValue: session.title,
      inputPattern: /.+/,
      inputErrorMessage: "会话名称不能为空",
    });
    const title = String(result.value || "").trim();
    if (!title) {
      ElMessage.warning("会话名称不能为空");
      return;
    }
    await request<ChatSession>(`/ai/sessions/${session.session_id}`, {
      method: "PUT",
      body: JSON.stringify({ title }),
    });
    await loadSessions();
    ElMessage.success("会话已重命名");
  } catch (error) {
    if (error !== "cancel" && error !== "close") notifyError(error);
  }
}

async function removeSession(session: ChatSession) {
  try {
    await ElMessageBox.confirm(`确定删除“${session.title || "未命名会话"}”吗？删除后会话消息不可恢复。`, "删除会话", {
      confirmButtonText: "删除",
      cancelButtonText: "取消",
      type: "warning",
    });
    await request(`/ai/sessions/${session.session_id}`, { method: "DELETE" });
    if (sessionId.value === session.session_id) {
      sessionId.value = "";
      messages.value = [];
      summary.value = null;
    }
    await loadSessions();
    ElMessage.success("会话已删除");
  } catch (error) {
    if (error !== "cancel" && error !== "close") notifyError(error);
  }
}

async function send() {
  const content = prompt.value.trim();
  if (!content) return;
  loading.value = true;
  messages.value.push({ role: "user", content });
  prompt.value = "";
  try {
    const data = await request<ChatResult>("/ai/chat", {
      method: "POST",
      body: JSON.stringify({ session_id: sessionId.value || undefined, message: content }),
    });
    sessionId.value = data.session_id;
    messages.value.push({ role: "assistant", content: data.reply || "助手未返回有效内容" });
    if (data.saved_memory) await loadMemories();
    await loadSessions();
  } catch (error) {
    const failureMessage = error instanceof Error ? error.message : "请求失败";
    messages.value.push({ role: "assistant", content: `请求失败：${failureMessage}` });
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
  if (!q) {
    ElMessage.warning("请填写搜索内容");
    return;
  }
  try {
    const data = await request<{ items: Record<string, unknown>[] }>(`/ai/memories/search?q=${encodeURIComponent(q)}&limit=10`);
    searchItems.value = data.items || [];
  } catch (error) {
    notifyError(error);
  }
}

async function loadSummary(regenerate = false) {
  if (!sessionId.value) {
    ElMessage.warning("请先选择或创建会话");
    return;
  }
  summaryLoading.value = true;
  try {
    summary.value = await request<SessionSummary>(`/ai/sessions/${sessionId.value}/${regenerate ? "summarize" : "summary"}`, {
      method: regenerate ? "POST" : "GET",
    });
    await loadSessions();
  } catch (error) {
    notifyError(error);
  } finally {
    summaryLoading.value = false;
  }
}

onMounted(async () => {
  await Promise.all([loadSessions(), loadMemories()]);
});
</script>

<template>
  <section class="ai-workbench expanded">
    <aside class="workbench-side session-side" v-loading="sessionLoading">
      <div class="session-actions">
        <button type="button" class="session-action primary" @click="createSession">
          <el-icon><Plus /></el-icon>
          <span>新对话</span>
        </button>
        <button type="button" class="session-action" @click="loadSessions">
          <el-icon><Refresh /></el-icon>
          <span>刷新会话</span>
        </button>
      </div>

      <el-input v-model="sessionKeyword" clearable placeholder="搜索会话" @keyup.enter="loadSessions" @clear="loadSessions">
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>

      <div class="session-tools">
        <el-button :loading="summaryLoading" :disabled="!sessionId" @click="loadSummary(false)">查看摘要</el-button>
        <el-button :loading="summaryLoading" :disabled="!sessionId" @click="loadSummary(true)">重新摘要</el-button>
      </div>

      <div class="session-section-title">最近会话</div>
      <div class="session-list">
        <button
          v-for="item in sessions"
          :key="item.session_id"
          type="button"
          :class="['session-item', { active: item.session_id === sessionId }]"
          @click="openSession(item)"
        >
          <span class="session-item-icon">
            <el-icon><ChatLineRound /></el-icon>
          </span>
          <span class="session-item-main">
            <strong>{{ item.title || "未命名会话" }}</strong>
            <small>{{ item.last_message || `${item.message_count} 条消息` }}</small>
          </span>
          <span class="session-item-meta">{{ item.message_count }} 条</span>
        </button>
        <div v-if="!sessions.length" class="empty-state compact">暂无会话，点击新对话开始。</div>
      </div>

      <div v-if="activeSession" class="session-footer">
        <el-button :icon="EditPen" @click="renameSession(activeSession)">重命名</el-button>
        <el-button :icon="Delete" type="danger" plain @click="removeSession(activeSession)">删除</el-button>
      </div>

      <div v-if="summary" class="summary-card">
        <strong>会话摘要</strong>
        <p>{{ summaryText }}</p>
        <small>{{ formatTime(summary.summary_updated_at) }} · {{ summary.message_count ?? 0 }} 条消息</small>
      </div>
    </aside>

    <main class="chat-panel">
      <div class="chat-toolbar">
        <div>
          <strong>普通问答</strong>
          <span>{{ activeSession?.title || sessionId || "新会话" }}</span>
        </div>
        <div class="workbench-metrics">
          <span>{{ messages.length }} 条消息</span>
          <span>{{ memories.length }} 条记忆</span>
        </div>
      </div>
      <div class="chat-list">
        <div v-if="!messages.length" class="empty-state compact">开始一次普通问答</div>
        <article v-for="(item, index) in messages" :key="item.id || index" :class="['chat-message', item.role]">
          <strong>{{ item.role === "user" ? "我" : "助手" }}</strong>
          <p>{{ item.content }}</p>
        </article>
      </div>
      <div class="composer">
        <el-input
          v-model="prompt"
          type="textarea"
          :rows="3"
          resize="none"
          placeholder="输入问题后点击发送，也可按 Ctrl + Enter"
          @keyup.ctrl.enter="send"
        />
        <el-button type="primary" :loading="loading" @click="send">发送</el-button>
      </div>
    </main>

    <aside class="workbench-side memory-side" v-loading="memoryLoading">
      <h3>长期记忆</h3>
      <p>支持手动添加、删除和语义搜索当前用户记忆。</p>
      <div class="side-stat">
        <strong>{{ memories.length }}</strong>
        <span>当前可用记忆</span>
      </div>
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
