const fs = require("fs");
const path = require("path");

const root = path.resolve(__dirname, "..");
const source = fs.readFileSync(path.join(root, "frontend", "src", "views", "ModuleListView.vue"), "utf8");

function assertIncludes(text, message) {
  if (!source.includes(text)) throw new Error(message);
}

assertIncludes("searchKeyword", "业务列表页缺少当前页筛选状态");
assertIncludes("filteredRows", "业务列表页缺少筛选后的表格数据");
assertIncludes("detailVisible", "业务列表页缺少详情抽屉状态");
assertIncludes("openDetail(row)", "业务列表页缺少详情入口");
assertIncludes("/students?skip=", "学生列表未绑定分页接口");
assertIncludes("/students", "学生新增接口未绑定");
assertIncludes("/update_student/", "学生编辑接口未绑定");
assertIncludes("/students_delete/", "学生删除接口未绑定");
assertIncludes("/teacher/list", "教师列表接口未绑定");
assertIncludes("/classes/?", "班级列表接口未绑定");
assertIncludes("page: String(currentPage)", "班级列表未传递当前页");
assertIncludes("size: String(size)", "班级列表未传递分页大小");
assertIncludes("/score/query/", "成绩列表接口未绑定");
assertIncludes("/jobs/page", "就业列表接口未绑定");
