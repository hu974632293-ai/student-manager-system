const fs = require("fs");
const path = require("path");

const root = path.resolve(__dirname, "..");
const statisticsSource = fs.readFileSync(path.join(root, "frontend", "src", "views", "StatisticsView.vue"), "utf8");
const dashboardSource = fs.readFileSync(path.join(root, "frontend", "src", "views", "DashboardView.vue"), "utf8");

function assertIncludes(source, text, message) {
  if (!source.includes(text)) throw new Error(message);
}

assertIncludes(dashboardSource, "/statistics/dashboard", "总览页未调用看板统计接口");
assertIncludes(dashboardSource, "echarts.init", "总览页缺少 ECharts 图表");
assertIncludes(statisticsSource, "/statistics/classes/gender-count", "统计页缺少班级性别统计接口");
assertIncludes(statisticsSource, "/statistics/scores/class-average", "统计页缺少班级平均成绩接口");
assertIncludes(statisticsSource, "/statistics/scores/failed-more-than-twice", "统计页缺少挂科风险接口");
assertIncludes(statisticsSource, "/statistics/employment/top5-salary", "统计页缺少就业薪资排行接口");
assertIncludes(statisticsSource, "/statistics/employment/class-average-duration", "统计页缺少就业时长接口");
assertIncludes(statisticsSource, "echarts.init", "统计页缺少 ECharts 图表");
