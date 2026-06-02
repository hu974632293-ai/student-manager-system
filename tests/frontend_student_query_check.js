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

assertIncludes(appSource, "this.rows = this.flattenStudentQuery(data);", "student exact query should refresh table rows");
assertIncludes(appSource, "this.pager.total = this.rows.length;", "student exact query should sync table total");
assertIncludes(appSource, "this.pager.page = 1;", "student exact query should reset page");
assertIncludes(appSource, "if (!this.studentExact.student_id && !this.studentExact.student_name && !this.studentExact.class_id)", "empty exact query should return to paged list");
assertIncludes(appSource, "this.studentExact = { student_id: \"\", student_name: \"\", class_id: \"\" };", "reset should clear exact query fields");
assertIncludes(appSource, "if (group) return [group];", "student query result should support single objects");
assertIncludes(appSource, "const data = await this.request(\"/students?skip=0&limit=10000\");", "student list filters should use list data");
assertIncludes(appSource, "this.rows = this.filterStudentRows(data.students || []);", "student list filters should refresh table rows");
assertIncludes(appSource, "filterStudentRows(students)", "missing student list filter method");
assertIncludes(appSource, "String(item.student_id || \"\").includes(studentId)", "student id filter should support contains matching");
assertIncludes(appSource, "String(item.name || \"\").includes(name)", "student name filter should support contains matching");
assertIncludes(appSource, "if (classId && String(item.class_id || \"\") !== classId) return false;", "class id filter should use exact matching");
assertIncludes(htmlSource, "v-if=\"activeModule !== 'students'\"", "student module should hide the duplicate generic filter row");
