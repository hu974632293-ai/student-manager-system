const fs = require("fs");
const path = require("path");

const root = path.resolve(__dirname, "..");
const source = fs.readFileSync(path.join(root, "frontend", "src", "views", "AiChatView.vue"), "utf8");

function assertIncludes(text, message) {
  if (!source.includes(text)) throw new Error(message);
}

assertIncludes("请求失败：", "AI 问答失败时没有在聊天区显示中文错误消息");
assertIncludes("messages.value.push({ role: \"assistant\", content: `请求失败：${failureMessage}` })", "AI 问答 catch 分支没有追加 assistant 错误消息");
assertIncludes("/ai/sessions", "AI 会话列表接口未接入前端");
assertIncludes("createSession", "AI 会话创建入口缺失");
assertIncludes("openSession", "AI 会话打开入口缺失");
assertIncludes("renameSession", "AI 会话重命名入口缺失");
assertIncludes("removeSession", "AI 会话删除入口缺失");
