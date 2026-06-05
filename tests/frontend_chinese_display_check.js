const fs = require("fs");
const path = require("path");

const root = path.resolve(__dirname, "..");
const files = [
  "frontend/src/permissions.ts",
  "frontend/src/components/AppShell.vue",
  "frontend/src/views/DashboardView.vue",
  "frontend/src/views/LetterView.vue",
  "frontend/src/views/WeatherView.vue",
  "frontend/src/views/GeocodeView.vue",
  "frontend/src/views/WorkbenchView.vue",
].map((file) => fs.readFileSync(path.join(root, file), "utf8")).join("\n");

function assertIncludes(text, message) {
  if (!files.includes(text)) throw new Error(message);
}

assertIncludes("教务管理", "侧边栏缺少教务管理分组");
assertIncludes("系统工具", "侧边栏缺少系统工具分组");
assertIncludes("运营总览", "总览页未改造成 BI 看板文案");
assertIncludes("邮件发送", "缺少邮件发送页面文案");
assertIncludes("天气查询", "缺少天气查询页面文案");
assertIncludes("经纬度查询", "缺少经纬度查询页面文案");
assertIncludes("暂未开放", "知识库/智能体缺少暂未开放占位文案");
