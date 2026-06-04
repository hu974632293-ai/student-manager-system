<script setup lang="ts">
import { ref } from "vue";

import { notifyError, request } from "@/api/http";

interface ChatResult {
  session_id: string;
  message: string;
  reply: string;
  context_message_count: number;
}

const prompt = ref("");
const sessionId = ref("");
const loading = ref(false);
const messages = ref<{ role: "user" | "assistant"; content: string }[]>([]);

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
    messages.value.push({ role: "assistant", content: data.reply });
  } catch (error) {
    notifyError(error);
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <section class="ai-workbench">
    <aside class="workbench-side">
      <h3>普通问答</h3>
      <p>会话 ID</p>
      <el-input v-model="sessionId" clearable placeholder="自动创建或继续已有会话" />
    </aside>
    <main class="chat-panel">
      <div class="chat-list">
        <div v-if="!messages.length" class="empty-state">开始一次问答</div>
        <article v-for="(item, index) in messages" :key="index" :class="['chat-message', item.role]">
          <strong>{{ item.role === "user" ? "我" : "AI" }}</strong>
          <p>{{ item.content }}</p>
        </article>
      </div>
      <div class="composer">
        <el-input v-model="prompt" type="textarea" :rows="3" resize="none" placeholder="输入你的问题" @keyup.ctrl.enter="send" />
        <el-button type="primary" :loading="loading" @click="send">发送</el-button>
      </div>
    </main>
    <aside class="workbench-side">
      <h3>上下文</h3>
      <p>后端会按当前登录用户记录会话上下文，后续可扩展引用、工具调用和流式输出。</p>
    </aside>
  </section>
</template>
