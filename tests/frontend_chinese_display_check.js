const fs = require("fs");
const path = require("path");

const root = path.resolve(__dirname, "..");
const appSource = fs.readFileSync(path.join(root, "frontend", "app.js"), "utf8");
const htmlSource = fs.readFileSync(path.join(root, "frontend", "index.html"), "utf8");
const cssSource = fs.readFileSync(path.join(root, "frontend", "styles.css"), "utf8");

function assertIncludes(source, text, message) {
    if (!source.includes(text)) {
        throw new Error(message);
    }
}

assertIncludes(htmlSource, "就业薪资排行前五", "首页薪资排行标题未改成正常中文");
assertIncludes(htmlSource, "班级平均成绩排行", "首页班级成绩标题未改成正常中文");
assertIncludes(htmlSource, "统计分析入口", "首页统计入口标题未改成正常中文");
assertIncludes(htmlSource, "第{{ item.exam_round }}轮", "首页轮次显示未使用正常中文模板");
assertIncludes(htmlSource, "title=\"查询详情\"", "详情抽屉标题未改成正常中文");
assertIncludes(appSource, "label: \"查询高龄学生\"", "统计入口文案未保持正常中文");
assertIncludes(appSource, "msg: \"查询结果\"", "详情字段 msg 未映射为中文");
assertIncludes(appSource, "select_id: \"学生编号匹配\"", "详情字段 select_id 未映射为中文");
assertIncludes(appSource, "select_name: \"姓名匹配\"", "详情字段 select_name 未映射为中文");
assertIncludes(appSource, "class_id: \"班级匹配\"", "详情字段 class_id 未映射为中文");
assertIncludes(appSource, "studentDetailFields", "缺少学生详情字段拆分配置");
assertIncludes(appSource, "studentDetailEntries(value)", "缺少学生详情逐字段展示方法");
assertIncludes(appSource, "return [{ title: this.fieldLabel(key), entries: this.studentDetailEntries(item) }];", "详情对象未拆分成字段网格");
assertIncludes(cssSource, ".detail-record", "缺少详情卡片样式");
assertIncludes(cssSource, ".detail-item strong", "缺少详情字段值样式");
