const fs = require("fs");
const path = require("path");

const root = path.resolve(__dirname, "..");
const appSource = fs.readFileSync(path.join(root, "frontend", "app.js"), "utf8");
const htmlSource = fs.readFileSync(path.join(root, "frontend", "index.html"), "utf8");

function assertIncludes(source, text, message) {
    if (!source.includes(text)) {
        throw new Error(message);
    }
}

assertIncludes(appSource, "statisticPager: { page: 1, size: 10 }", "缺少统计分析分页状态");
assertIncludes(appSource, "pagedStatisticRows()", "缺少统计分析分页计算属性");
assertIncludes(appSource, "this.statisticPager.page = 1", "统计查询流程没有重置页码");
assertIncludes(htmlSource, ':data="pagedStatisticRows"', "统计表格未绑定分页后的数据");
assertIncludes(htmlSource, ":total=\"statisticRows.length\"", "统计分页总数未绑定完整统计结果数量");
assertIncludes(htmlSource, "@current-change=\"changeStatisticPage\"", "缺少统计页码切换事件");
assertIncludes(htmlSource, "@size-change=\"changeStatisticSize\"", "缺少统计每页条数切换事件");
