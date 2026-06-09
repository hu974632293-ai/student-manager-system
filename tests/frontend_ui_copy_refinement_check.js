const fs = require("fs");
const path = require("path");

const root = path.resolve(__dirname, "..");
const styles = fs.readFileSync(path.join(root, "frontend", "src", "styles.css"), "utf8");
const moduleList = fs.readFileSync(path.join(root, "frontend", "src", "views", "ModuleListView.vue"), "utf8");
const statistics = fs.readFileSync(path.join(root, "frontend", "src", "views", "StatisticsView.vue"), "utf8");
const dataQuery = fs.readFileSync(path.join(root, "frontend", "src", "views", "DataQueryView.vue"), "utf8");

const required = [
  [styles, ".info-rail", "缺少低干扰信息条样式"],
  [styles, ".info-chip", "缺少信息标签样式"],
  [styles, ".rule-chip", "缺少统计规则标签样式"],
  [styles, ".empty-state.soft", "缺少弱化空状态样式"],
  [moduleList, "contextTags", "模块页缺少上下文标签配置"],
  [moduleList, "context-strip-meta", "模块页未把说明转为标签"],
  [statistics, "rule-chip", "统计页未使用规则标签"],
  [dataQuery, "info-rail", "智能问数页未使用信息条"],
  [dataQuery, "empty-state soft", "智能问数页未使用弱化空状态"],
];

const forbidden = [
  [moduleList, "<p>{{ config?.description }}</p>", "模块页仍在主视觉裸露长说明"],
  [statistics, "默认筛选所有成绩不低于 80 分的学生", "统计页仍裸露优秀成绩规则长文案"],
  [statistics, "默认低于 60 分且次数超过 2 次", "统计页仍裸露挂科风险规则长文案"],
  [statistics, "基于录用日期与开岗日期计算", "统计页仍裸露就业时长规则长文案"],
  [dataQuery, "输入问题后点击查询，这里会展示查询语句、摘要和结果表格。", "智能问数空状态仍裸露长说明"],
  [dataQuery, "当前仅支持学生、班级、教师、成绩和就业相关白名单表，只执行 SELECT 查询。", "智能问数安全边界仍裸露长说明"],
];

const missing = required.filter(([source, snippet]) => !source.includes(snippet)).map(([, , message]) => message);
const exposed = forbidden.filter(([source, snippet]) => source.includes(snippet)).map(([, , message]) => message);

if (missing.length > 0 || exposed.length > 0) {
  console.error(`UI 文案弱化检查失败:\n${[...missing, ...exposed].join("\n")}`);
  process.exit(1);
}

console.log("frontend ui copy refinement check passed");
