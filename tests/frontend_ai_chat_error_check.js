const fs = require("fs");
const path = require("path");

const root = path.resolve(__dirname, "..");
const source = fs.readFileSync(path.join(root, "frontend", "src", "views", "AiChatView.vue"), "utf8");

if (!source.includes("请求失败：")) {
  throw new Error("AI 问答失败时没有在聊天区显示错误消息");
}

if (!source.includes("messages.value.push({ role: \"assistant\", content: `请求失败：${message}` })")) {
  throw new Error("AI 问答 catch 分支没有追加 assistant 错误消息");
}
