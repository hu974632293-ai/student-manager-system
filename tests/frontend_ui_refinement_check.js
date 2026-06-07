const fs = require("fs");
const path = require("path");

const root = path.resolve(__dirname, "..");
const styles = fs.readFileSync(path.join(root, "frontend", "src", "styles.css"), "utf8");
const dashboard = fs.readFileSync(path.join(root, "frontend", "src", "views", "DashboardView.vue"), "utf8");
const moduleList = fs.readFileSync(path.join(root, "frontend", "src", "views", "ModuleListView.vue"), "utf8");

const checks = [
  [styles, "--font-body", "全局样式缺少正文专用字体变量"],
  [styles, "--font-data", "全局样式缺少表格/数字专用字体变量"],
  [styles, ".context-strip", "缺少上下文工具条样式"],
  [styles, ".context-strip-meta", "缺少上下文状态标签样式"],
  [styles, ".table-shell", "缺少表格容器层级样式"],
  [styles, ".business-table .el-table__header-wrapper", "缺少业务表格表头强化样式"],
  [styles, ".business-table .el-table__body", "缺少业务表格正文字体样式"],
  [styles, ".row-actions", "缺少行操作分组样式"],
  [dashboard, "context-strip", "仪表盘未使用上下文工具条"],
  [dashboard, "context-strip-meta", "仪表盘缺少上下文状态标签"],
  [moduleList, "context-strip", "模块列表页未使用上下文工具条"],
  [moduleList, "table-shell", "模块列表页表格未放入新表格容器"],
];

const missing = checks.filter(([source, snippet]) => !source.includes(snippet)).map(([, , message]) => message);

if (missing.length > 0) {
  console.error(`UI 细化检查失败:\n${missing.join("\n")}`);
  process.exit(1);
}

console.log("frontend ui refinement check passed");
