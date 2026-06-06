<script setup lang="ts">
import { ElMessage } from "element-plus";
import { reactive, ref } from "vue";

import { notifyError, request } from "@/api/http";

interface LetterResult {
  recipient: string;
  recipient_name: string;
  to_email?: string;
  subject?: string;
  method: string;
  content: string;
}

const loading = ref(false);
const sending = ref(false);
const result = ref<LetterResult | null>(null);
const methodLabels: Record<string, string> = {
  chat: "对话生成",
  generate: "文本生成",
};
const form = reactive({
  mode: "direct",
  recipient: "assistant_teacher",
  to_email: "",
  subject: "",
  topic: "",
  tone: "真诚、自然",
  method: "chat",
  content: "",
});

function payload(includeEmail: boolean) {
  const data: Record<string, unknown> = {
    recipient: form.recipient,
    topic: form.topic || form.subject || "日常沟通",
    tone: form.tone,
    method: form.method,
  };
  if (includeEmail) {
    data.to_email = form.to_email;
    data.subject = form.subject;
  }
  if (form.mode === "direct") data.content = form.content;
  return data;
}

function methodLabel(method?: string) {
  return method ? methodLabels[method] || method : "-";
}

async function generate() {
  if (!form.topic.trim()) {
    ElMessage.warning("请填写生成主题");
    return;
  }
  loading.value = true;
  try {
    result.value = await request<LetterResult>("/letters/generate", {
      method: "POST",
      body: JSON.stringify(payload(false)),
    });
    form.content = result.value.content;
    ElMessage.success("信件生成成功");
  } catch (error) {
    notifyError(error);
  } finally {
    loading.value = false;
  }
}

async function send() {
  if (!form.to_email.trim()) {
    ElMessage.warning("请填写收件邮箱");
    return;
  }
  if (!form.subject.trim()) {
    ElMessage.warning("请填写邮件主题");
    return;
  }
  if (form.mode === "direct" && !form.content.trim()) {
    ElMessage.warning("请填写邮件正文");
    return;
  }
  sending.value = true;
  try {
    result.value = await request<LetterResult>("/letters/send", {
      method: "POST",
      body: JSON.stringify(payload(true)),
    });
    ElMessage.success("邮件发送成功");
  } catch (error) {
    notifyError(error);
  } finally {
    sending.value = false;
  }
}
</script>

<template>
  <section class="tool-layout">
    <article class="page-surface">
      <div class="section-heading">
        <div>
          <h3>邮件发送</h3>
          <p>支持直接发送正文，也可以先调用本地模型生成信件内容。</p>
        </div>
      </div>
      <el-form label-position="top">
        <el-form-item label="发送方式">
          <el-radio-group v-model="form.mode">
            <el-radio-button label="direct">直接发送正文</el-radio-button>
            <el-radio-button label="generate">生成后发送</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="收件邮箱">
          <el-input v-model="form.to_email" placeholder="请输入收件邮箱" />
        </el-form-item>
        <el-form-item label="邮件主题">
          <el-input v-model="form.subject" placeholder="请输入邮件主题" />
        </el-form-item>
        <el-form-item label="信件对象">
          <el-select v-model="form.recipient" class="full-input">
            <el-option label="助教老师" value="assistant_teacher" />
            <el-option label="班主任" value="head_teacher" />
            <el-option label="Luke" value="luke" />
          </el-select>
        </el-form-item>
        <el-form-item label="生成主题">
          <el-input v-model="form.topic" placeholder="例如：请假说明、学习反馈、就业跟进" />
        </el-form-item>
        <el-form-item label="语气">
          <el-input v-model="form.tone" />
        </el-form-item>
        <el-form-item label="正文">
          <el-input v-model="form.content" type="textarea" :rows="10" resize="vertical" placeholder="直接发送时请填写正文；生成后发送时可先生成再调整。" />
        </el-form-item>
        <div class="toolbar-actions">
          <el-button :loading="loading" @click="generate">生成正文</el-button>
          <el-button type="primary" :loading="sending" @click="send">发送邮件</el-button>
        </div>
      </el-form>
    </article>

    <aside class="page-surface">
      <div class="card-title">
        <h4>发送结果</h4>
        <span>配置缺失会由后端返回明确错误</span>
      </div>
      <el-descriptions v-if="result" :column="1" border>
        <el-descriptions-item label="收件人">{{ result.to_email || "-" }}</el-descriptions-item>
        <el-descriptions-item label="主题">{{ result.subject || form.subject }}</el-descriptions-item>
        <el-descriptions-item label="对象">{{ result.recipient_name }}</el-descriptions-item>
        <el-descriptions-item label="生成方式">{{ methodLabel(result.method) }}</el-descriptions-item>
      </el-descriptions>
      <pre v-if="result" class="result-pre">{{ result.content }}</pre>
      <div v-else class="empty-state compact">暂无发送或生成结果</div>
    </aside>
  </section>
</template>
