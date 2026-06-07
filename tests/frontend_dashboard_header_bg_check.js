const fs = require("fs");
const path = require("path");

const root = path.resolve(__dirname, "..");
const dashboard = fs.readFileSync(path.join(root, "frontend", "src", "views", "DashboardView.vue"), "utf8");
const styles = fs.readFileSync(path.join(root, "frontend", "src", "styles.css"), "utf8");
const assetPath = path.join(root, "frontend", "src", "assets", "dashboard-header-bg.png");

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

assert(dashboard.includes("dashboard-hero-surface"), "总览页缺少顶部背景承接容器");
assert(styles.includes("dashboard-header-bg.png"), "总览页样式未引用顶部背景图");
assert(styles.includes(".dashboard-hero-surface"), "总览页缺少顶部背景容器样式");
assert(fs.existsSync(assetPath), "总览页顶部背景图资产不存在");
