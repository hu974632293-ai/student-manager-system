const fs = require("fs");
const path = require("path");
const { createRequire } = require("module");

// Codex 内置 Node 依赖采用 pnpm 结构，这里直接从 pptxgenjs 的包目录加载，
// 避免 Windows 环境下 NODE_PATH 找不到 jszip 等子依赖。
const runtimeNodeModules = path.join(
  process.env.USERPROFILE || "",
  ".cache",
  "codex-runtimes",
  "codex-primary-runtime",
  "dependencies",
  "node",
  "node_modules",
  ".pnpm",
  "pptxgenjs@4.0.1",
  "node_modules",
  "pptxgenjs",
  "package.json"
);
const PptxGenJS = createRequire(runtimeNodeModules)("pptxgenjs");

// 课程答辩 PPT 生成脚本：内容基于当前项目真实代码、git 记录和统计模块说明。
const root = path.resolve(__dirname, "..");
const outputDir = path.join(root, "outputs", "defense_ppt");
const outputPath = path.join(outputDir, "沃林学生管理系统_项目答辩.pptx");
const heroImage = path.join(root, "frontend", "assets", "dashboard-hero.png");

fs.mkdirSync(outputDir, { recursive: true });

const pptx = new PptxGenJS();
pptx.layout = "LAYOUT_WIDE";
pptx.author = "six_god";
pptx.subject = "沃林学生管理系统项目答辩";
pptx.title = "沃林学生管理系统项目答辩";
pptx.company = "six_god";
pptx.lang = "zh-CN";
pptx.theme = {
  headFontFace: "Microsoft YaHei",
  bodyFontFace: "Microsoft YaHei",
  lang: "zh-CN",
};
pptx.defineLayout({ name: "LAYOUT_WIDE", width: 13.333, height: 7.5 });

const C = {
  bg: "F4F7FB",
  ink: "172033",
  muted: "6B778C",
  line: "D9E2EE",
  navy: "101C33",
  navy2: "162844",
  teal: "14B8A6",
  cyan: "38BDF8",
  amber: "F59E0B",
  red: "EF4444",
  green: "22C55E",
  white: "FFFFFF",
  softTeal: "E7FAF7",
  softBlue: "EAF6FF",
  softAmber: "FFF7E6",
};

function addBg(slide, color = C.bg) {
  slide.background = { color };
}

function addFooter(slide, page) {
  slide.addShape(pptx.ShapeType.line, {
    x: 0.55, y: 7.05, w: 12.25, h: 0,
    line: { color: C.line, width: 0.8 },
  });
  slide.addText("沃林学生管理系统 · 项目答辩", {
    x: 0.65, y: 7.12, w: 5.5, h: 0.18,
    fontFace: "Microsoft YaHei", fontSize: 7.5, color: C.muted,
    margin: 0,
  });
  slide.addText(String(page).padStart(2, "0"), {
    x: 12.15, y: 7.08, w: 0.6, h: 0.22,
    fontFace: "Microsoft YaHei", fontSize: 8.5, color: C.teal,
    align: "right", bold: true, margin: 0,
  });
}

function addKicker(slide, text, x = 0.7, y = 0.42, dark = false) {
  slide.addShape(pptx.ShapeType.rect, {
    x, y: y + 0.055, w: 0.18, h: 0.18,
    fill: { color: dark ? C.cyan : C.teal },
    line: { color: dark ? C.cyan : C.teal },
  });
  slide.addText(text, {
    x: x + 0.28, y, w: 3.6, h: 0.28,
    fontSize: 8, bold: true, color: dark ? "DFF7FF" : C.teal,
    charSpace: 0.8, margin: 0,
  });
}

function title(slide, kicker, claim, support, page, dark = false) {
  addKicker(slide, kicker, 0.7, 0.42, dark);
  slide.addText(claim, {
    x: 0.7, y: 0.82, w: 8.7, h: 0.72,
    fontFace: "Microsoft YaHei", fontSize: 25, bold: true,
    color: dark ? C.white : C.ink, breakLine: false,
    margin: 0,
    fit: "shrink",
  });
  if (support) {
    slide.addText(support, {
      x: 0.72, y: 1.62, w: 8.6, h: 0.42,
      fontSize: 10.5, color: dark ? "B7C8DC" : C.muted,
      margin: 0, fit: "shrink",
    });
  }
  addFooter(slide, page);
}

function textBox(slide, text, x, y, w, h, opts = {}) {
  slide.addText(text, {
    x, y, w, h,
    fontFace: "Microsoft YaHei",
    fontSize: opts.size || 12,
    color: opts.color || C.ink,
    bold: opts.bold || false,
    margin: opts.margin ?? 0.08,
    valign: opts.valign || "mid",
    align: opts.align || "left",
    breakLine: false,
    fit: "shrink",
    bullet: opts.bullet,
  });
}

function card(slide, x, y, w, h, fill = C.white, line = C.line) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x, y, w, h,
    rectRadius: 0.08,
    fill: { color: fill },
    line: { color: line, width: 0.8 },
  });
}

function metric(slide, label, value, hint, x, y, w, color = C.teal) {
  card(slide, x, y, w, 0.86, C.white, C.line);
  textBox(slide, label, x + 0.16, y + 0.12, w - 0.25, 0.18, { size: 7.5, color: C.muted, bold: true });
  textBox(slide, value, x + 0.16, y + 0.32, w - 0.25, 0.28, { size: 17, color, bold: true });
  textBox(slide, hint, x + 0.16, y + 0.64, w - 0.25, 0.15, { size: 6.7, color: C.muted });
}

function arrow(slide, x1, y1, x2, y2, color = C.teal) {
  slide.addShape(pptx.ShapeType.line, {
    x: x1, y: y1, w: x2 - x1, h: y2 - y1,
    line: { color, width: 1.6, beginArrowType: "none", endArrowType: "triangle" },
  });
}

function addNotes(slide, notes) {
  if (typeof slide.addNotes === "function") {
    slide.addNotes(notes);
  }
}

function slide1() {
  const s = pptx.addSlide();
  addBg(s, C.navy);
  if (fs.existsSync(heroImage)) {
    s.addImage({ path: heroImage, x: 0, y: 0, w: 13.333, h: 7.5, transparency: 18 });
  }
  s.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: 13.333, h: 7.5, fill: { color: C.navy, transparency: 8 }, line: { color: C.navy } });
  addKicker(s, "PROJECT DEFENSE", 0.82, 0.74, true);
  s.addText("沃林学生管理系统", { x: 0.82, y: 1.35, w: 7.4, h: 0.78, fontSize: 33, bold: true, color: C.white, margin: 0, fit: "shrink" });
  s.addText("统计查询模块 · 前端界面落地 · 小组代码整合", { x: 0.86, y: 2.16, w: 7.3, h: 0.36, fontSize: 14, color: "C8D7EA", margin: 0 });
  metric(s, "后端负责", "统计查询", "8 个统计接口", 0.86, 5.54, 2.3, C.cyan);
  metric(s, "前端负责", "界面落地", "可视化 + 实用功能", 3.35, 5.54, 2.3, C.teal);
  metric(s, "团队协同", "代码整合", "Git + 测试 + PPT", 5.84, 5.54, 2.3, C.amber);
  s.addText("答辩重点：不把内容讲得太玄，重点说清楚“我做了什么、怎么运行、为什么这样设计”。", {
    x: 0.86, y: 6.62, w: 9.1, h: 0.25, fontSize: 9.5, color: "BED0E6", margin: 0,
  });
  addNotes(s, "开场：先说明自己负责后端统计查询模块、前端界面落地，以及小组代码整合和 PPT。语气自然，不需要把自己包装成专业前端。");
}

function slide2() {
  const s = pptx.addSlide(); addBg(s); title(s, "SYSTEM OVERVIEW", "系统不是单个页面，而是一套前后端联动的学生管理后台。", "用一张图说明整体结构，后面再展开自己负责的统计和前端。", 2);
  const xs = [0.9, 3.9, 6.85, 9.85];
  const labels = [
    ["前端页面", "Vue3 + Element Plus\n登录、菜单、表格、统计页"],
    ["FastAPI 路由", "接收请求\n校验参数\n分发模块"],
    ["DAO 查询层", "SQLAlchemy\n联表、过滤、分组统计"],
    ["MySQL 数据库", "学生、成绩、就业\n班级、教师、用户"],
  ];
  labels.forEach((it, i) => {
    card(s, xs[i], 2.35, 2.25, 1.45, i === 0 ? C.softBlue : i === 2 ? C.softTeal : C.white);
    textBox(s, it[0], xs[i] + 0.16, 2.55, 1.9, 0.25, { bold: true, size: 14, color: i === 0 ? C.cyan : i === 2 ? C.teal : C.ink });
    textBox(s, it[1], xs[i] + 0.16, 2.9, 1.9, 0.6, { size: 9.5, color: C.muted });
    if (i < labels.length - 1) arrow(s, xs[i] + 2.33, 3.08, xs[i + 1] - 0.15, 3.08);
  });
  textBox(s, "我的工作横跨两边：后端统计接口要能查，前端页面要能用，最后还要把组员代码合到一个能运行的系统里。", 1.05, 4.7, 10.6, 0.65, { size: 15, bold: true });
  addNotes(s, "这页讲整体架构。重点说：不是孤立写一个函数，而是前端发请求，FastAPI 接住，DAO 查数据库，再返回页面展示。");
}

function slide3() {
  const s = pptx.addSlide(); addBg(s); title(s, "MY ROLE", "我的贡献可以分成三条线：统计模块、前端落地、团队整合。", "这样讲比只说“我写了某些文件”更清楚。", 3);
  const rows = [
    ["后端统计查询", "设计并维护统计接口：年龄、性别、成绩、就业薪资和就业时长。", C.teal],
    ["前端界面落地", "把管理后台做成可视化页面：登录、菜单、表格、统计入口、分页。", C.cyan],
    ["小组整合协调", "合并后端项目代码，使用 Git 管理版本，做测试验证和 PPT 展示。", C.amber],
  ];
  rows.forEach((r, i) => {
    const y = 2.25 + i * 1.22;
    s.addShape(pptx.ShapeType.rect, { x: 1.0, y: y + 0.08, w: 0.16, h: 0.78, fill: { color: r[2] }, line: { color: r[2] } });
    card(s, 1.25, y, 10.8, 0.95, C.white);
    textBox(s, r[0], 1.55, y + 0.2, 2.1, 0.32, { size: 15, bold: true, color: r[2] });
    textBox(s, r[1], 3.75, y + 0.18, 7.8, 0.4, { size: 12.2, color: C.ink });
  });
  addNotes(s, "这页强调三条线。老师如果问分工，你可以回答：统计模块是后端重点，前端主要由我推进落地，另外承担整合测试和 PPT。");
}

function slide4() {
  const s = pptx.addSlide(); addBg(s); title(s, "BACKEND STRUCTURE", "统计模块按三层拆开：API 接请求，Schema 定格式，DAO 查数据。", "这是我后端部分最重要的设计逻辑。", 4);
  const blocks = [
    ["API 层", "API_statistics.py", "定义 /statistics 路由\n接收 Query 参数\n调用 DAO 方法", C.cyan],
    ["Schema 层", "Schemas_statistics.py", "定义返回字段\n保证响应结构稳定\n便于前端接收", C.amber],
    ["DAO 层", "Dao_statistics.py", "写查询逻辑\n过滤、联表、分组\n排序和聚合统计", C.teal],
  ];
  blocks.forEach((b, i) => {
    const x = 1 + i * 3.95;
    card(s, x, 2.32, 3.25, 2.55, i === 1 ? C.softAmber : i === 2 ? C.softTeal : C.softBlue);
    textBox(s, b[0], x + 0.22, 2.55, 2.6, 0.28, { size: 18, bold: true, color: b[3] });
    textBox(s, b[1], x + 0.22, 2.96, 2.7, 0.25, { size: 9.5, color: C.muted, bold: true });
    textBox(s, b[2], x + 0.22, 3.42, 2.8, 0.9, { size: 11.5, color: C.ink });
    if (i < 2) arrow(s, x + 3.35, 3.58, x + 3.78, 3.58);
  });
  textBox(s, "答辩时可以这样说：API 不直接写复杂查询，复杂统计统一放在 DAO，返回字段统一由 Schema 管住。", 1.1, 5.55, 10.9, 0.45, { size: 13.5, bold: true });
  addNotes(s, "这页是后端设计逻辑：分层不是为了显得复杂，而是为了代码更容易读，接口、返回格式、查询逻辑各管一块。");
}

function slide5() {
  const s = pptx.addSlide(); addBg(s); title(s, "DATA FLOW", "一次统计查询的运行流程是：参数进来，DAO 统计，JSON 返回。", "用这个流程解释所有统计接口，老师更容易听懂。", 5);
  const steps = [
    ["1", "Swagger/前端请求", "例如 min_score=80"],
    ["2", "FastAPI 参数校验", "Query 控制范围和默认值"],
    ["3", "statistics_dao", "进入对应查询方法"],
    ["4", "SQLAlchemy 查询", "联表、过滤、分组、聚合"],
    ["5", "Pydantic 返回", "转成稳定 JSON 字段"],
  ];
  steps.forEach((st, i) => {
    const x = 0.72 + i * 2.48;
    s.addShape(pptx.ShapeType.ellipse, { x, y: 2.35, w: 0.58, h: 0.58, fill: { color: i === 2 ? C.teal : C.navy }, line: { color: i === 2 ? C.teal : C.navy } });
    textBox(s, st[0], x, 2.46, 0.58, 0.18, { size: 10.5, color: C.white, bold: true, align: "center" });
    card(s, x - 0.28, 3.05, 2.0, 1.2, C.white);
    textBox(s, st[1], x - 0.1, 3.22, 1.65, 0.28, { size: 12.5, bold: true, color: i === 2 ? C.teal : C.ink, align: "center" });
    textBox(s, st[2], x - 0.04, 3.62, 1.55, 0.35, { size: 8.8, color: C.muted, align: "center" });
    if (i < steps.length - 1) arrow(s, x + 0.68, 2.64, x + 2.14, 2.64);
  });
  textBox(s, "关键点：统计模块不是简单查表，而是把多张表的数据变成“年龄、成绩、就业”等业务问题的答案。", 1.05, 5.35, 11, 0.48, { size: 14, bold: true });
  addNotes(s, "这页可以作为所有接口的总逻辑。你不用每个接口都从零讲，先讲统一流程，再举例。");
}

function slide6() {
  const s = pptx.addSlide(); addBg(s); title(s, "STATISTICS API MAP", "我实现的统计查询覆盖学生、班级、成绩、就业四类问题。", "接口命名都在 /statistics 前缀下面，方便统一管理。", 6);
  const groups = [
    ["学生画像", ["/students/over-30"], C.cyan],
    ["班级结构", ["/classes/gender-count"], C.teal],
    ["成绩表现", ["/scores/all-above-80", "/scores/failed-more-than-twice", "/scores/class-average"], C.amber],
    ["就业结果", ["/employment/top5-salary", "/employment/student-duration", "/employment/class-average-duration"], C.green],
  ];
  groups.forEach((g, i) => {
    const x = 0.86 + (i % 2) * 6.0;
    const y = 2.2 + Math.floor(i / 2) * 1.8;
    card(s, x, y, 5.35, 1.35, C.white);
    s.addShape(pptx.ShapeType.rect, { x, y, w: 0.13, h: 1.35, fill: { color: g[2] }, line: { color: g[2] } });
    textBox(s, g[0], x + 0.28, y + 0.18, 1.4, 0.25, { size: 13.5, bold: true, color: g[2] });
    textBox(s, g[1].join("\n"), x + 1.78, y + 0.14, 3.28, 0.82, { size: 8.8, color: C.ink });
  });
  textBox(s, "答辩表达：这些接口不是为了数量多，而是围绕培训管理最常问的几个问题：学生情况、班级结构、成绩表现、就业结果。", 0.95, 6.0, 11.2, 0.42, { size: 12.6, bold: true });
  addNotes(s, "这页讲功能覆盖。不要机械念接口名，要说它们回答了什么管理问题。");
}

function slide7() {
  const s = pptx.addSlide(); addBg(s); title(s, "CODE WALKTHROUGH", "以班级性别统计为例：从班级出发，外连接学生，再按性别聚合。", "这是一个适合答辩现场逐行讲的代表接口。", 7);
  card(s, 0.85, 2.18, 5.65, 3.6, "111827", "111827");
  const code = [
    "db.query(",
    "  Class.class_id.label('class_id'),",
    "  count(Student.student_id).label('total_count'),",
    "  sum(case(Student.gender == '男')).label('male_count'),",
    "  sum(case(Student.gender == '女')).label('female_count'),",
    ")",
    ".outerjoin(Student, Student.class_id == Class.id)",
    ".filter(Class.is_deleted == False)",
    ".group_by(Class.class_id)",
  ].join("\n");
  textBox(s, code, 1.12, 2.42, 5.15, 2.95, { size: 8.6, color: "E5E7EB" });
  const notes = [
    ["为什么从班级出发", "即使班级暂时没有学生，也能保留统计行。"],
    ["为什么用 outerjoin", "外连接能保证“空班级”不丢失。"],
    ["为什么用 group_by", "按班级编号分组，得到每个班一行结果。"],
    ["为什么用 case + sum", "把男/女条件转换成 1 或 0，再求和。"],
  ];
  notes.forEach((n, i) => {
    const y = 2.18 + i * 0.86;
    card(s, 6.82, y, 5.25, 0.65, i % 2 ? C.softBlue : C.white);
    textBox(s, n[0], 7.05, y + 0.1, 1.65, 0.18, { size: 9.2, bold: true, color: C.teal });
    textBox(s, n[1], 8.65, y + 0.08, 3.1, 0.26, { size: 9.5, color: C.ink });
  });
  addNotes(s, "这页按代码讲。重点是 outerjoin、group_by、case+sum 三个点，用学习阶段语言解释：外连接保留班级，分组让每班一行，case 负责分别数男女。");
}

function slide8() {
  const s = pptx.addSlide(); addBg(s); title(s, "FRONTEND LANDING", "前端重点不是炫技术，而是把后台系统真正落到可操作界面。", "登录页、导航、数据总览和统计入口都围绕“能看、能查、能用”。", 8);
  card(s, 0.85, 2.05, 11.75, 4.25, "0F1B31", "0F1B31");
  s.addShape(pptx.ShapeType.rect, { x: 0.85, y: 2.05, w: 2.1, h: 4.25, fill: { color: "101C33" }, line: { color: "101C33" } });
  textBox(s, "沃林学生管理系统", 1.12, 2.34, 1.6, 0.34, { size: 10, color: C.white, bold: true });
  ["数据总览", "学生档案", "成绩跟踪", "就业进展", "班级管理", "统计分析"].forEach((m, i) => {
    const y = 2.94 + i * 0.42;
    s.addShape(pptx.ShapeType.roundRect, { x: 1.08, y, w: 1.55, h: 0.26, rectRadius: 0.04, fill: { color: m === "统计分析" ? "1F766F" : "162844" }, line: { color: m === "统计分析" ? "1F766F" : "162844" } });
    textBox(s, m, 1.22, y + 0.045, 1.1, 0.1, { size: 6.8, color: "E6EEFB" });
  });
  s.addShape(pptx.ShapeType.rect, { x: 2.95, y: 2.05, w: 9.65, h: 0.65, fill: { color: C.white }, line: { color: C.white } });
  textBox(s, "统计分析", 3.25, 2.27, 1.2, 0.16, { size: 10, bold: true, color: C.ink });
  ["学生档案 286", "班级数量 12", "就业记录 168", "平均薪资 ¥14,900"].forEach((m, i) => metric(s, m.split(" ")[0], m.split(" ")[1], "系统核心指标", 3.25 + i * 2.12, 3.02, 1.82, i === 3 ? C.amber : C.teal));
  card(s, 3.25, 4.25, 4.0, 1.42, C.white);
  textBox(s, "就业薪资 Top 5", 3.48, 4.43, 1.7, 0.18, { size: 9, bold: true });
  [0.88, 0.72, 0.66].forEach((w, i) => s.addShape(pptx.ShapeType.rect, { x: 3.52, y: 4.82 + i * 0.22, w: 2.8 * w, h: 0.09, fill: { color: i === 0 ? C.teal : C.cyan }, line: { color: i === 0 ? C.teal : C.cyan } }));
  card(s, 7.55, 4.25, 3.9, 1.42, C.white);
  textBox(s, "班级平均成绩", 7.78, 4.43, 1.7, 0.18, { size: 9, bold: true });
  [92, 87, 83].forEach((v, i) => {
    textBox(s, `第${i + 1}轮`, 7.82, 4.75 + i * 0.25, 0.5, 0.1, { size: 6.5, color: C.muted });
    s.addShape(pptx.ShapeType.rect, { x: 8.42, y: 4.78 + i * 0.25, w: 2.25 * v / 100, h: 0.08, fill: { color: C.teal }, line: { color: C.teal } });
  });
  addNotes(s, "这页讲前端界面落地：登录页、侧边栏、总览卡片、统计入口都是为了让后台能实际使用。不要说太多 Vue 技术。");
}

function slide9() {
  const s = pptx.addSlide(); addBg(s); title(s, "VISUAL DETAILS", "可视化细腻程度体现在：页面有层次、数据有重点、操作有入口。", "我通过反复描述视觉目标，让 AI 输出更接近真实后台，而不是简单表格堆叠。", 9);
  const items = [
    ["层次", "左侧导航 + 顶部标题 + 主内容区", C.cyan],
    ["数据", "卡片指标、进度条、排名条、统计表格", C.teal],
    ["状态", "登录态、加载态、分页、空数据提示", C.amber],
    ["实用", "查询、筛选、新增编辑删除、统计切换", C.green],
  ];
  items.forEach((it, i) => {
    const x = 0.85 + i * 3.1;
    card(s, x, 2.2, 2.55, 2.35, C.white);
    s.addShape(pptx.ShapeType.ellipse, { x: x + 0.22, y: 2.45, w: 0.55, h: 0.55, fill: { color: it[2] }, line: { color: it[2] } });
    textBox(s, it[0], x + 0.92, 2.5, 1.0, 0.22, { size: 15, bold: true, color: it[2] });
    textBox(s, it[1], x + 0.24, 3.25, 2.05, 0.55, { size: 11, color: C.ink, align: "center" });
  });
  textBox(s, "前端核心思想：不只是能打开页面，而是让页面“看起来像管理系统、用起来像管理系统”。", 1.0, 5.45, 10.9, 0.42, { size: 15, bold: true, color: C.ink, align: "center" });
  addNotes(s, "这页回应新增需求：界面落地、可视化细腻、功能实用性。可以说自己不会前端语法，但会判断页面是否像一个真正系统。");
}

function slide10() {
  const s = pptx.addSlide(); addBg(s); title(s, "PRACTICAL FUNCTIONS", "前端实用性体现在：用户不是只能看，还能查、筛、改、分页和进入统计。", "这些功能让页面从展示稿变成实际后台。", 10);
  const funcs = [
    ["登录进入", "账号密码进入后台，恢复登录认证功能。"],
    ["模块导航", "学生、成绩、就业、班级、教师、统计统一入口。"],
    ["查询筛选", "按学生编号、姓名、班级、薪资、分数范围查询。"],
    ["CRUD 操作", "新增、编辑、删除等按钮和表单结构。"],
    ["统计分页", "统计结果分页展示，避免数据太多挤在一页。"],
  ];
  funcs.forEach((f, i) => {
    const y = 2.12 + i * 0.7;
    s.addShape(pptx.ShapeType.rect, { x: 1.05, y: y + 0.08, w: 0.12, h: 0.44, fill: { color: i % 2 ? C.cyan : C.teal }, line: { color: i % 2 ? C.cyan : C.teal } });
    textBox(s, f[0], 1.35, y + 0.04, 1.6, 0.25, { size: 12.5, bold: true, color: C.ink });
    textBox(s, f[1], 3.1, y + 0.04, 8.4, 0.25, { size: 11.3, color: C.muted });
  });
  card(s, 8.95, 4.95, 2.55, 0.78, C.softTeal, C.teal);
  textBox(s, "验证依据", 9.18, 5.08, 0.85, 0.16, { size: 9, bold: true, color: C.teal });
  textBox(s, "frontend_statistic_pagination_check.js", 9.18, 5.32, 1.92, 0.13, { size: 6.8, color: C.muted });
  addNotes(s, "这页讲功能实用性：不仅界面漂亮，还要能登录、导航、查询、分页。统计分页还专门有测试脚本验证。");
}

function slide11() {
  const s = pptx.addSlide(); addBg(s); title(s, "FRONTEND ITERATION", "前端不是一次成型，而是按阶段从初版走到最终可用。", "这条时间线来自 git 提交记录。", 11);
  const stages = [
    ["前端版1.0", "搭出后台基本页面和视觉方向"],
    ["前端版2.0", "补充就业、成绩、数据展示等模块"],
    ["接口接入", "接入原有后端接口，移除重复新增后端"],
    ["登录恢复", "恢复登录认证，系统更像真实后台"],
    ["统计分页", "统计结果分页优化，并增加验证脚本"],
    ["最终版1.0", "形成当前答辩展示版本"],
  ];
  s.addShape(pptx.ShapeType.line, { x: 1.0, y: 3.6, w: 11.2, h: 0, line: { color: C.line, width: 2 } });
  stages.forEach((st, i) => {
    const x = 1.0 + i * 2.18;
    s.addShape(pptx.ShapeType.ellipse, { x: x - 0.12, y: 3.48, w: 0.25, h: 0.25, fill: { color: i === 5 ? C.amber : C.teal }, line: { color: i === 5 ? C.amber : C.teal } });
    textBox(s, st[0], x - 0.45, 2.72, 0.9, 0.25, { size: 9.3, bold: true, color: C.ink, align: "center" });
    textBox(s, st[1], x - 0.78, 4.02, 1.55, 0.5, { size: 8.2, color: C.muted, align: "center" });
  });
  textBox(s, "答辩表达：前端工作最重要的是持续迭代。每一次提交都解决一个更具体的问题。", 1.1, 5.45, 10.8, 0.42, { size: 14, bold: true, align: "center" });
  addNotes(s, "这页讲真实过程。可以按 git 线索说：先有初版，再优化页面，再接接口，再恢复登录，最后补统计分页。");
}

function slide12() {
  const s = pptx.addSlide(); addBg(s); title(s, "AI COLLABORATION", "AI 协同的重点不是让 AI 替我想，而是我把目标说清楚并不断验收。", "这也是我完成前端界面落地的核心方法。", 12);
  const flow = [
    ["提出目标", "我要什么页面\n解决什么场景"],
    ["拆成模块", "登录、导航、表格\n统计、分页、弹窗"],
    ["细化要求", "颜色、层次、间距\n可视化重点"],
    ["检查结果", "能不能用\n像不像系统"],
    ["继续调整", "接接口\n修体验\n补测试"],
  ];
  flow.forEach((f, i) => {
    const x = 0.86 + i * 2.45;
    card(s, x, 2.42, 1.8, 1.58, i === 2 ? C.softAmber : C.white);
    textBox(s, f[0], x + 0.18, 2.68, 1.42, 0.22, { size: 12.5, bold: true, color: i === 2 ? C.amber : C.teal, align: "center" });
    textBox(s, f[1], x + 0.18, 3.08, 1.42, 0.46, { size: 8.7, color: C.ink, align: "center" });
    if (i < flow.length - 1) arrow(s, x + 1.86, 3.2, x + 2.36, 3.2, C.amber);
  });
  textBox(s, "我的体会：学习阶段不一定马上掌握所有前端语法，但必须能提出清晰需求、判断结果质量、推动下一轮修改。", 1.05, 5.1, 11, 0.52, { size: 14.2, bold: true, align: "center" });
  addNotes(s, "这页讲 AI 协同思想。重点：你不是被动复制，而是指挥、拆解、验收、迭代。");
}

function slide13() {
  const s = pptx.addSlide(); addBg(s); title(s, "TEAM INTEGRATION", "小组协同里，我承担的是把大家的模块合成一个能运行的项目。", "整合工作看起来琐碎，但决定项目最后能不能演示。", 13);
  const lanes = [
    ["合并代码", "整合学生、教师、成绩、就业、班级、统计等后端模块。"],
    ["统一入口", "在 main.py 注册各模块路由，统一挂载前端静态页面。"],
    ["版本控制", "用 Git 记录前端迭代、接口接入、登录恢复、统计分页等节点。"],
    ["测试验证", "统计接口测试、前端分页脚本、联调后检查页面展示。"],
    ["PPT制作", "整理分工、运行逻辑、截图与答辩讲稿。"],
  ];
  lanes.forEach((l, i) => {
    const x = i < 3 ? 0.85 + i * 4.0 : 2.85 + (i - 3) * 4.0;
    const y = i < 3 ? 2.25 : 4.25;
    card(s, x, y, 3.15, 1.1, C.white);
    textBox(s, l[0], x + 0.22, y + 0.16, 1.3, 0.22, { size: 12.8, bold: true, color: i === 2 ? C.amber : C.teal });
    textBox(s, l[1], x + 0.22, y + 0.5, 2.65, 0.3, { size: 8.8, color: C.muted });
  });
  addNotes(s, "这页讲小组协同。把重点放在整合协调，而不是说自己做了所有东西。");
}

function slide14() {
  const s = pptx.addSlide(); addBg(s); title(s, "PROBLEMS & SOLUTIONS", "项目中遇到的问题，基本都靠拆分、验证和迭代解决。", "这页用来体现真实开发过程，而不是只展示最终结果。", 14);
  const problems = [
    ["字段不熟悉", "先梳理所有表字段含义，再写统计模块注释和答辩文档。"],
    ["统计逻辑难讲", "把代码拆成 API、Schema、DAO 三层，再按数据流讲。"],
    ["前端基础弱", "先明确页面目标，再通过 AI 协同逐步落地和验收。"],
    ["组员代码整合", "用 Git 记录版本，合并后统一入口和接口调用。"],
    ["展示效果不够", "增加页面可视化细节、统计分页和演示讲稿。"],
  ];
  problems.forEach((p, i) => {
    const y = 2.05 + i * 0.72;
    s.addShape(pptx.ShapeType.roundRect, { x: 0.95, y, w: 2.0, h: 0.42, rectRadius: 0.04, fill: { color: C.navy }, line: { color: C.navy } });
    textBox(s, p[0], 1.13, y + 0.11, 1.65, 0.1, { size: 8.8, color: C.white, bold: true, align: "center" });
    arrow(s, 3.05, y + 0.21, 3.75, y + 0.21, C.teal);
    card(s, 3.9, y - 0.02, 7.8, 0.48, C.white);
    textBox(s, p[1], 4.12, y + 0.07, 7.2, 0.18, { size: 10.2, color: C.ink });
  });
  addNotes(s, "这页讲问题与解决。不要怕承认不会前端，学习阶段更重要的是能拆问题、查资料、让结果跑起来。");
}

function slide15() {
  const s = pptx.addSlide(); addBg(s, C.navy);
  addKicker(s, "SUMMARY", 0.82, 0.68, true);
  s.addText("我的答辩总结", { x: 0.82, y: 1.18, w: 4.2, h: 0.52, fontSize: 28, bold: true, color: C.white, margin: 0 });
  const summary = [
    ["后端", "我能讲清统计查询模块的代码设计和运行逻辑。"],
    ["前端", "我推动界面从想法落地成可视化、可操作、可演示的后台。"],
    ["协同", "我承担代码整合、版本控制、测试验证和 PPT 制作。"],
  ];
  summary.forEach((it, i) => {
    card(s, 0.9 + i * 4.05, 2.55, 3.35, 1.55, i === 1 ? "123A53" : "162844", "29425F");
    textBox(s, it[0], 1.16 + i * 4.05, 2.86, 0.8, 0.28, { size: 18, color: i === 1 ? C.cyan : C.teal, bold: true });
    textBox(s, it[1], 1.16 + i * 4.05, 3.28, 2.65, 0.4, { size: 10.8, color: "DDE8F7" });
  });
  s.addText("谢谢老师", { x: 0.86, y: 5.68, w: 3.4, h: 0.48, fontSize: 24, bold: true, color: C.white, margin: 0 });
  s.addText("如果老师追问，我优先从统计模块的数据流和前端落地过程展开。", { x: 0.88, y: 6.24, w: 7.4, h: 0.25, fontSize: 10.5, color: "B7C8DC", margin: 0 });
  addNotes(s, "结尾：用三句话收束。后端讲逻辑，前端讲落地，协同讲整合。");
}

[
  slide1, slide2, slide3, slide4, slide5,
  slide6, slide7, slide8, slide9, slide10,
  slide11, slide12, slide13, slide14, slide15,
].forEach((fn) => fn());

pptx.writeFile({ fileName: outputPath });
console.log(outputPath);
