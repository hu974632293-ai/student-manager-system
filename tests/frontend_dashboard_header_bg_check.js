const fs = require("fs");
const path = require("path");

const root = path.resolve(__dirname, "..");
const dashboard = fs.readFileSync(path.join(root, "frontend", "src", "views", "DashboardView.vue"), "utf8");
const styles = fs.readFileSync(path.join(root, "frontend", "src", "styles.css"), "utf8");
const assetPath = path.join(root, "frontend", "src", "assets", "dashboard-header-bg.png");

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

function blocks(selector) {
  const escaped = selector.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  return Array.from(styles.matchAll(new RegExp(`${escaped}\\s*\\{([\\s\\S]*?)\\n\\}`, "g"))).map((match) => match[1]).join("\n");
}

const topbarBlock = blocks(".topbar");
const titleBlock = blocks(".title-block h2");
const subtitleBlock = blocks(".title-block p");
const sectionTitleBlock = blocks(".section-heading h3");
const cardTitleBlock = blocks(".card-title h4");
const workbenchTitleBlock = blocks(".workbench-side h3");
const composerTitleBlock = blocks(".composer-head h3");

assert(dashboard.includes("dashboard-hero-surface"), "总览页缺少顶部背景承接容器");
assert(topbarBlock.includes("dashboard-header-bg.png"), "全局顶栏未使用顶部背景图");
assert(styles.includes(".dashboard-hero-surface"), "总览页缺少顶部背景容器样式");
assert(fs.existsSync(assetPath), "总览页顶部背景图资产不存在");
assert(styles.includes("--font-display"), "全局缺少主标题专用字体变量");
assert(titleBlock.includes("var(--font-display)") && titleBlock.includes("font-size") && titleBlock.includes("font-weight"), "全局页面标题缺少字体优化");
assert(subtitleBlock.includes("font-size") && subtitleBlock.includes("font-weight"), "全局页面副标题缺少字体优化");
assert(sectionTitleBlock.includes("var(--font-display)") && sectionTitleBlock.includes("font-weight"), "页面区块主标题缺少字体优化");
assert(cardTitleBlock.includes("var(--font-display)") && cardTitleBlock.includes("font-weight"), "卡片主标题缺少字体优化");
assert(workbenchTitleBlock.includes("var(--font-display)") && workbenchTitleBlock.includes("font-weight"), "工作台侧栏主标题缺少字体优化");
assert(composerTitleBlock.includes("var(--font-display)") && composerTitleBlock.includes("font-weight"), "查询/编辑区主标题缺少字体优化");
