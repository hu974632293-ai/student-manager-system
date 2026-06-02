const { createApp } = Vue;

const roleLabels = { admin: "管理员", teacher: "教师", consultant: "顾问" };

const menuIcons = {
    overview: '<svg viewBox="0 0 24 24"><path d="M4 19V5"/><path d="M4 19h16"/><path d="M8 16v-5"/><path d="M12 16V8"/><path d="M16 16v-3"/></svg>',
    students: '<svg viewBox="0 0 24 24"><path d="M12 12a4 4 0 1 0-4-4 4 4 0 0 0 4 4Z"/><path d="M4 21a8 8 0 0 1 16 0"/></svg>',
    scores: '<svg viewBox="0 0 24 24"><path d="M8 4h8"/><path d="M9 2h6v4H9z"/><path d="M7 4H5v18h14V4h-2"/><path d="m8 13 2 2 5-5"/><path d="M8 18h8"/></svg>',
    employment: '<svg viewBox="0 0 24 24"><path d="M9 6V4h6v2"/><path d="M4 7h16v12H4z"/><path d="M4 12h16"/><path d="M10 12v2h4v-2"/></svg>',
    classes: '<svg viewBox="0 0 24 24"><path d="M4 4h7v7H4z"/><path d="M13 4h7v7h-7z"/><path d="M4 13h7v7H4z"/><path d="M13 13h7v7h-7z"/></svg>',
    teachers: '<svg viewBox="0 0 24 24"><path d="M4 5h16v10H4z"/><path d="M8 19h8"/><path d="M12 15v4"/><path d="M8 10h8"/></svg>',
    statistics: '<svg viewBox="0 0 24 24"><path d="M12 3v9h9"/><path d="M20 15a8 8 0 1 1-8-12"/><path d="M15 3.6A9 9 0 0 1 20.4 9"/></svg>',
    extensions: '<svg viewBox="0 0 24 24"><path d="M10 4h4v4h-4z"/><path d="M4 14h4v4H4z"/><path d="M16 14h4v4h-4z"/><path d="M12 8v3"/><path d="M8 16h8"/><path d="M12 11H6v3"/><path d="M12 11h6v3"/></svg>',
};

const fieldLabels = {
    id: "ID",
    student_id: "学生编号",
    name: "姓名",
    student_name: "学生姓名",
    gender: "性别",
    age: "年龄",
    native_place: "籍贯",
    graduate_school: "毕业院校",
    major: "专业",
    education: "学历",
    enrollment_date: "入学时间",
    graduation_date: "毕业时间",
    class_id: "班级",
    class_name: "班级",
    teacher_number: "工号",
    phone: "电话",
    email: "邮箱",
    subject: "授课科目",
    is_active: "在职状态",
    is_deleted: "删除状态",
    head_teacher: "班主任",
    teacher_ids: "授课教师",
    teacher_names: "授课教师",
    description: "描述",
    start_date: "开课时间",
    consultant_id: "顾问ID",
    total_count: "总人数",
    male_count: "男生人数",
    female_count: "女生人数",
    exam_round: "考核轮次",
    score: "成绩",
    average_score: "平均分",
    employment_date: "就业开放时间",
    job_open_date: "就业开放时间",
    offer_date: "Offer时间",
    company_name: "就业公司",
    salary: "薪资",
    position: "岗位",
    remark: "备注",
    duration_days: "就业时长(天)",
    average_duration_days: "平均就业时长(天)",
};

const detailGroupLabels = {
    msg: "查询结果",
    select_id: "学生编号匹配",
    select_name: "姓名匹配",
    class_id: "班级匹配",
};

const studentDetailFields = [
    { key: "student_id", label: "学生编号" },
    { key: "name", label: "姓名" },
    { key: "class_id", label: "班级ID" },
    { key: "gender", label: "性别" },
    { key: "age", label: "年龄" },
    { key: "education", label: "学历" },
    { key: "major", label: "专业" },
    { key: "native_place", label: "籍贯" },
    { key: "graduate_school", label: "毕业院校" },
    { key: "enrollment_date", label: "入学时间" },
    { key: "graduation_date", label: "毕业时间" },
    { key: "consultant_id", label: "顾问ID" },
    { key: "is_deleted", label: "删除状态" },
    { key: "id", label: "ID" },
];

const emptyConfig = { name: "", filters: [], columns: [], formFields: [], coverage: "" };

createApp({
    data() {
        return {
            token: localStorage.getItem("wolin_token") || localStorage.getItem("wolin_front_gate") || "",
            user: JSON.parse(localStorage.getItem("wolin_user") || localStorage.getItem("wolin_front_user") || "{}"),
            loginForm: { username: "", password: "" },
            activeModule: "overview",
            activeStatistic: "over30",
            loading: false,
            globalKeyword: "",
            filters: {},
            rows: [],
            pager: { page: 1, size: 10, total: 0 },
            summary: {},
            statistics: { topSalary: [], classAverage: [] },
            statisticParams: {},
            statisticPager: { page: 1, size: 10 },
            statisticRows: [],
            statisticColumns: [],
            teacherOptions: [],
            teacherSourceRows: [],
            studentExact: { student_id: "", student_name: "", class_id: "" },
            scoreRange: { min_score: 60, max_score: 100 },
            employmentQuery: { student_id: "", class_name: "", min_salary: 8000, max_salary: 25000 },
            dialog: { visible: false, mode: "create" },
            form: {},
            bulkDialog: { visible: false, text: "" },
            detailDrawer: { visible: false, data: null },
            menus: [
                { key: "overview", label: "数据总览", icon: menuIcons.overview, subtitle: "汇总学生档案、班级规模、就业进展和成绩概览" },
                { key: "students", label: "学生档案", icon: menuIcons.students, subtitle: "维护学生基础信息，支持编号、姓名和班级精准查询" },
                { key: "scores", label: "成绩跟踪", icon: menuIcons.scores, subtitle: "管理考核成绩，支持单条录入、批量录入、范围查询和修改删除" },
                { key: "employment", label: "就业进展", icon: menuIcons.employment, subtitle: "跟踪学生就业公司、岗位、薪资和 Offer 时间" },
                { key: "classes", label: "班级管理", icon: menuIcons.classes, subtitle: "维护班级编号、开课时间、班主任和授课教师" },
                { key: "teachers", label: "教师管理", icon: menuIcons.teachers, subtitle: "维护教师工号、联系方式、授课科目和在职状态" },
                { key: "statistics", label: "统计分析", icon: menuIcons.statistics, subtitle: "按年龄、性别、成绩和就业维度查看统计结果" },
                { key: "extensions", label: "扩展功能", icon: menuIcons.extensions, subtitle: "预留组织管理、顾问跟进和知识库入口" },
            ],
            extensions: [
                { title: "组织管理", desc: "后续可接入校区、部门、岗位和数据权限管理。" },
                { title: "顾问跟进", desc: "后续可关联学生咨询记录、就业跟进和回访任务。" },
                { title: "AI 知识库", desc: "后续可接入课程资料、就业问答和答辩辅助工具。" },
            ],
            analysisEntries: [
                {
                    key: "over30",
                    label: "查询高龄学生",
                    url: "/statistics/students/over-30",
                    params: [{ key: "min_age", label: "年龄大于", type: "number", default: 30, min: 0 }],
                },
                {
                    key: "gender",
                    label: "查询班级性别分布",
                    url: "/statistics/classes/gender-count",
                    params: [{ key: "class_id", label: "班级ID/编号", placeholder: "如 2 或 PY0520" }],
                },
                {
                    key: "above80",
                    label: "查询优秀学员",
                    url: "/statistics/scores/all-above-80",
                    params: [{ key: "min_score", label: "最低成绩", type: "number", default: 80, min: 0, max: 100 }],
                },
                {
                    key: "failed",
                    label: "查询多次不及格学生",
                    url: "/statistics/scores/failed-more-than-twice",
                    params: [
                        { key: "fail_score", label: "不及格线", type: "number", default: 60, min: 0, max: 100 },
                        { key: "min_fail_count", label: "超过次数", type: "number", default: 2, min: 0 },
                    ],
                },
                {
                    key: "classAverage",
                    label: "查询班级平均成绩",
                    url: "/statistics/scores/class-average",
                    params: [
                        { key: "class_id", label: "班级ID/编号", placeholder: "留空查全部" },
                        { key: "exam_round", label: "考核轮次", type: "number", min: 1, placeholder: "留空查全部" },
                    ],
                },
                {
                    key: "topSalary",
                    label: "查询就业薪资排行",
                    url: "/statistics/employment/top5-salary",
                    params: [{ key: "limit", label: "Top 数量", type: "number", default: 5, min: 1, max: 100 }],
                },
                {
                    key: "duration",
                    label: "查询学生就业时长",
                    url: "/statistics/employment/student-duration",
                    params: [{ key: "class_name", label: "班级名称", placeholder: "如 PY0520，留空查全部" }],
                },
                {
                    key: "classDuration",
                    label: "查询班级就业时长",
                    url: "/statistics/employment/class-average-duration",
                    params: [{ key: "class_name", label: "班级名称", placeholder: "如 PY0520，留空查全部" }],
                },
            ],
            configs: {},
        };
    },
    computed: {
        currentMenu() {
            return this.menus.find((item) => item.key === this.activeModule) || this.menus[0];
        },
        currentConfig() {
            return this.configs[this.activeModule] || emptyConfig;
        },
        currentStatisticEntry() {
            return this.analysisEntries.find((item) => item.key === this.activeStatistic) || this.analysisEntries[0];
        },
        currentStatisticParams() {
            return this.currentStatisticEntry?.params || [];
        },
        pagedStatisticRows() {
            const start = (this.statisticPager.page - 1) * this.statisticPager.size;
            return this.statisticRows.slice(start, start + this.statisticPager.size);
        },
        isCrudModule() {
            return ["students", "scores", "employment", "classes", "teachers"].includes(this.activeModule);
        },
        dialogTitle() {
            return `${this.dialog.mode === "create" ? "新增" : "编辑"}${this.currentConfig.name}`;
        },
        metrics() {
            return [
                { label: "学生档案", value: this.summary.student_total || 0, hint: "来自学生列表" },
                { label: "班级数量", value: this.summary.class_total || 0, hint: "来自班级列表" },
                { label: "就业记录", value: this.summary.employed_total || 0, hint: `就业率 ${this.summary.employment_rate || 0}%` },
                { label: "平均薪资", value: this.money(this.summary.avg_salary || 0), hint: "来自就业分页" },
            ];
        },
    },
    created() {
        this.configs = this.makeConfigs();
        if (this.token) this.bootstrap();
    },
    methods: {
        makeConfigs() {
            return {
                students: {
                    name: "学生",
                    coverage: "学生列表、精准查询、新增学生、编辑学生、删除学生",
                    filters: [
                        { key: "student_id", label: "学生编号", placeholder: "请输入学生编号" },
                        { key: "name", label: "学生姓名", placeholder: "请输入学生姓名" },
                        { key: "class_id", label: "班级ID", placeholder: "请输入班级ID" },
                    ],
                    columns: [
                        { prop: "student_id", label: "学生编号", width: 130 },
                        { prop: "name", label: "姓名" },
                        { prop: "class_id", label: "班级ID", type: "tag" },
                        { prop: "gender", label: "性别" },
                        { prop: "age", label: "年龄" },
                        { prop: "education", label: "学历" },
                        { prop: "major", label: "专业", width: 170 },
                    ],
                    formFields: [
                        { key: "student_id", label: "学生编号", readonlyOnEdit: true },
                        { key: "class_id", label: "班级ID", type: "number", min: 1 },
                        { key: "name", label: "姓名" },
                        { key: "native_place", label: "籍贯" },
                        { key: "graduate_school", label: "毕业院校" },
                        { key: "major", label: "专业" },
                        { key: "enrollment_date", label: "入学时间", type: "date" },
                        { key: "graduation_date", label: "毕业时间", type: "date" },
                        { key: "education", label: "学历" },
                        { key: "consultant_id", label: "顾问ID", type: "number", min: 1 },
                        { key: "age", label: "年龄", type: "number", min: 0, max: 120 },
                        { key: "gender", label: "性别" },
                    ],
                },
                scores: {
                    name: "成绩",
                    coverage: "成绩列表、分数范围查询、单条录入、批量录入、编辑成绩、删除成绩",
                    filters: [
                        { key: "student_id", label: "学生编号", placeholder: "请输入学生编号" },
                        { key: "exam_round", label: "考核轮次", placeholder: "请输入考核轮次" },
                    ],
                    columns: [
                        { prop: "student_id", label: "学生编号", width: 130 },
                        { prop: "student_name", label: "姓名" },
                        { prop: "exam_round", label: "考核轮次" },
                        { prop: "score", label: "成绩" },
                        { prop: "remark", label: "备注", width: 180 },
                    ],
                    formFields: [
                        { key: "student_id", label: "学生编号", readonlyOnEdit: true },
                        { key: "exam_round", label: "考核轮次", type: "number", min: 1, readonlyOnEdit: true },
                        { key: "score", label: "成绩", type: "number", min: 0, max: 100 },
                        { key: "remark", label: "备注" },
                    ],
                },
                employment: {
                    name: "就业信息",
                    coverage: "就业列表、按学生查询、按班级查询、按薪资查询、新增就业、编辑就业、删除就业",
                    filters: [],
                    columns: [
                        { prop: "student_id", label: "学生编号", width: 130 },
                        { prop: "name", label: "姓名" },
                        { prop: "class_name", label: "班级", type: "tag" },
                        { prop: "company_name", label: "就业公司", width: 180 },
                        { prop: "position", label: "岗位" },
                        { prop: "salary", label: "薪资", type: "money" },
                        { prop: "job_open_date", label: "就业开放时间" },
                        { prop: "offer_date", label: "Offer时间" },
                    ],
                    formFields: [
                        { key: "id", label: "就业记录ID", type: "number", min: 1 },
                        { key: "student_id", label: "学生编号", readonlyOnEdit: true },
                        { key: "name", label: "学生姓名" },
                        { key: "class_name", label: "班级名称" },
                        { key: "job_open_date", label: "就业开放时间", type: "date" },
                        { key: "offer_date", label: "Offer时间", type: "date" },
                        { key: "company_name", label: "公司名称" },
                        { key: "salary", label: "薪资", type: "number", min: 0 },
                        { key: "position", label: "岗位" },
                    ],
                },
                classes: {
                    name: "班级",
                    coverage: "班级列表、班级详情、新增班级、编辑班级、删除班级",
                    filters: [{ key: "keyword", label: "关键词", placeholder: "搜索班级、班主任或描述" }],
                    columns: [
                        { prop: "id", label: "ID" },
                        { prop: "class_id", label: "班级编号" },
                        { prop: "start_date", label: "开课时间" },
                        { prop: "head_teacher", label: "班主任" },
                        { prop: "teacher_names", label: "授课教师", width: 260, type: "tags" },
                        { prop: "description", label: "描述", width: 220 },
                    ],
                    formFields: [
                        { key: "class_id", label: "班级编号" },
                        { key: "start_date", label: "开课时间", type: "date" },
                        { key: "head_teacher", label: "班主任" },
                        { key: "description", label: "描述" },
                        { key: "teacher_ids", label: "授课教师", type: "teacherSelect" },
                    ],
                },
                teachers: {
                    name: "教师",
                    coverage: "教师列表、教师详情、新增教师、编辑教师、删除教师",
                    filters: [{ key: "keyword", label: "关键词", placeholder: "搜索工号、姓名或科目" }],
                    columns: [
                        { prop: "id", label: "ID" },
                        { prop: "teacher_number", label: "工号" },
                        { prop: "name", label: "姓名" },
                        { prop: "gender", label: "性别" },
                        { prop: "phone", label: "电话" },
                        { prop: "email", label: "邮箱", width: 180 },
                        { prop: "subject", label: "授课科目" },
                        { prop: "is_active", label: "在职" },
                    ],
                    formFields: [
                        { key: "teacher_number", label: "工号" },
                        { key: "name", label: "姓名" },
                        { key: "gender", label: "性别" },
                        { key: "phone", label: "电话" },
                        { key: "email", label: "邮箱" },
                        { key: "subject", label: "授课科目" },
                    ],
                },
            };
        },
        async request(url, options = {}) {
            const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
            if (this.token) headers.Authorization = `Bearer ${this.token}`;
            const response = await fetch(url, {
                ...options,
                headers,
            });
            if (response.status === 204) return null;
            const data = await response.json().catch(() => ({}));
            const detail = Array.isArray(data.detail) ? data.detail.map((item) => item.msg).join("；") : data.detail;
            if (!response.ok) throw new Error(detail || data.msg || "请求失败");
            return data;
        },
        async login() {
            if (!this.loginForm.username || !this.loginForm.password) {
                ElementPlus.ElMessage.warning("请输入账号和密码");
                return;
            }
            this.loading = true;
            try {
                const data = await this.request("/auth/login", { method: "POST", body: JSON.stringify(this.loginForm) });
                this.token = data.access_token;
                this.user = data.user;
                localStorage.setItem("wolin_token", this.token);
                localStorage.setItem("wolin_user", JSON.stringify(this.user));
                localStorage.removeItem("wolin_front_gate");
                localStorage.removeItem("wolin_front_user");
                ElementPlus.ElMessage.success("登录成功");
                await this.bootstrap();
            } catch (error) {
                ElementPlus.ElMessage.error(error.message);
            } finally {
                this.loading = false;
            }
        },
        logout(showMessage = true) {
            this.token = "";
            this.user = {};
            localStorage.removeItem("wolin_token");
            localStorage.removeItem("wolin_user");
            localStorage.removeItem("wolin_front_gate");
            localStorage.removeItem("wolin_front_user");
            if (showMessage) ElementPlus.ElMessage.success("已退出登录");
        },
        async bootstrap() {
            try {
                if (this.token) {
                    this.user = await this.request("/auth/me");
                    localStorage.setItem("wolin_user", JSON.stringify(this.user));
                }
                await this.loadTeacherOptions();
                await Promise.all([this.loadDashboard(), this.loadHomeStatistics()]);
            } catch (error) {
                this.logout(false);
                ElementPlus.ElMessage.error(error.message || "登录状态无效，请重新登录");
            }
        },
        selectModule(key) {
            this.activeModule = key;
            this.pager.page = 1;
            this.filters = {};
            this.rows = [];
            if (this.isCrudModule) this.reload();
            if (key === "statistics") this.loadStatistic(this.activeStatistic);
        },
        async loadTeacherOptions() {
            try {
                this.teacherOptions = await this.request("/teacher/list");
            } catch {
                this.teacherOptions = [];
            }
        },
        async loadDashboard() {
            try {
                const [students, classes, jobs] = await Promise.all([
                    this.request("/students?skip=0&limit=1"),
                    this.request("/classes/?page=1&size=1"),
                    this.request("/jobs/page?page=1&size=1000"),
                ]);
                const jobRows = (jobs.list || []).map(this.normalizeEmployment);
                const avgSalary = jobRows.length ? jobRows.reduce((sum, item) => sum + Number(item.salary || 0), 0) / jobRows.length : 0;
                this.summary = {
                    student_total: students.total || 0,
                    class_total: classes.total || 0,
                    employed_total: jobs.total || jobRows.length,
                    employment_rate: students.total ? (((jobs.total || jobRows.length) / students.total) * 100).toFixed(1) : 0,
                    avg_salary: avgSalary,
                };
            } catch (error) {
                ElementPlus.ElMessage.warning(error.message);
            }
        },
        async loadHomeStatistics() {
            try {
                const [topSalary, classAverage] = await Promise.all([
                    this.request("/statistics/employment/top5-salary"),
                    this.request("/statistics/scores/class-average"),
                ]);
                this.statistics.topSalary = topSalary || [];
                this.statistics.classAverage = (classAverage || []).slice(0, 5);
            } catch {
                this.statistics = { topSalary: [], classAverage: [] };
            }
        },
        initStatisticParams(key = this.activeStatistic) {
            const entry = this.analysisEntries.find((item) => item.key === key);
            const next = {};
            (entry?.params || []).forEach((param) => {
                next[param.key] = param.default ?? "";
            });
            this.statisticParams = next;
        },
        buildStatisticUrl(entry) {
            const params = new URLSearchParams();
            (entry.params || []).forEach((param) => {
                const value = this.statisticParams[param.key];
                const text = value === undefined || value === null ? "" : String(value).trim();
                if (text) params.set(param.key, text);
            });
            const query = params.toString();
            return query ? `${entry.url}?${query}` : entry.url;
        },
        async reload() {
            if (!this.isCrudModule) return;
            this.loading = true;
            try {
                if (this.activeModule === "students") await this.loadStudents();
                if (this.activeModule === "scores") await this.loadScores();
                if (this.activeModule === "employment") await this.loadEmploymentPage();
                if (this.activeModule === "classes") await this.loadClasses();
                if (this.activeModule === "teachers") await this.loadTeachers();
            } catch (error) {
                ElementPlus.ElMessage.error(error.message);
            } finally {
                this.loading = false;
            }
        },
        async loadStudents() {
            if (this.filters.student_id || this.filters.name || this.filters.class_id) {
                const data = await this.request("/students?skip=0&limit=10000");
                this.rows = this.filterStudentRows(data.students || []);
                this.pager.total = this.rows.length;
                return;
            }
            const skip = (this.pager.page - 1) * this.pager.size;
            const data = await this.request(`/students?skip=${skip}&limit=${this.pager.size}`);
            this.rows = (data.students || []).map(this.normalizeStudent);
            this.pager.total = data.total || 0;
        },
        async loadScores() {
            const params = new URLSearchParams({ page: this.pager.page, page_size: this.pager.size });
            if (this.filters.student_id) params.set("student_id", this.filters.student_id);
            if (this.filters.exam_round) params.set("exam_round", this.filters.exam_round);
            const data = await this.request(`/score/query/?${params}`);
            this.rows = data.items || [];
            this.pager.total = data.total || 0;
        },
        async loadEmploymentPage() {
            const data = await this.request(`/jobs/page?page=${this.pager.page}&size=${this.pager.size}`);
            this.rows = (data.list || []).map(this.normalizeEmployment);
            this.pager.total = data.total || 0;
        },
        async loadClasses() {
            const params = new URLSearchParams({ page: this.pager.page, size: this.pager.size });
            if (this.filters.keyword) params.set("keyword", this.filters.keyword);
            const data = await this.request(`/classes/?${params}`);
            this.rows = (data.items || []).map(this.normalizeClass);
            this.pager.total = data.total || 0;
        },
        async loadTeachers() {
            const data = await this.request("/teacher/list");
            const keyword = (this.filters.keyword || "").trim();
            this.teacherSourceRows = keyword
                ? data.filter((item) => [item.teacher_number, item.name, item.subject].join(" ").includes(keyword))
                : data;
            this.pager.total = this.teacherSourceRows.length;
            const start = (this.pager.page - 1) * this.pager.size;
            this.rows = this.teacherSourceRows.slice(start, start + this.pager.size);
        },
        resetFilters() {
            this.filters = {};
            if (this.activeModule === "students") {
                this.studentExact = { student_id: "", student_name: "", class_id: "" };
            }
            this.pager.page = 1;
            this.reload();
        },
        changePage(page) {
            this.pager.page = page;
            this.reload();
        },
        changeSize(size) {
            this.pager.size = size;
            this.pager.page = 1;
            this.reload();
        },
        openCreate() {
            this.dialog = { visible: true, mode: "create" };
            this.form = this.activeModule === "employment" ? { salary: 10000 } : {};
        },
        openEdit(row) {
            this.dialog = { visible: true, mode: "edit" };
            this.form = { ...row };
        },
        cleanPayload(payload) {
            const next = {};
            Object.entries(payload).forEach(([key, value]) => {
                if (value !== "" && value !== undefined && value !== null && key !== "teacher_names") next[key] = value;
            });
            return next;
        },
        async saveRow() {
            this.loading = true;
            try {
                if (this.activeModule === "students") await this.saveStudent();
                if (this.activeModule === "scores") await this.saveScore();
                if (this.activeModule === "employment") await this.saveEmployment();
                if (this.activeModule === "classes") await this.saveClass();
                if (this.activeModule === "teachers") await this.saveTeacher();
                ElementPlus.ElMessage.success("保存成功");
                this.dialog.visible = false;
                await this.reload();
                this.loadDashboard();
            } catch (error) {
                ElementPlus.ElMessage.error(error.message);
            } finally {
                this.loading = false;
            }
        },
        async saveStudent() {
            const payload = this.cleanPayload(this.form);
            if (this.dialog.mode === "create") {
                await this.request("/students", { method: "POST", body: JSON.stringify(payload) });
            } else {
                const params = new URLSearchParams(payload);
                await this.request(`/update_student/${this.form.student_id}?${params}`, { method: "PUT" });
            }
        },
        async saveScore() {
            const payload = this.cleanPayload(this.form);
            if (this.dialog.mode === "create") {
                await this.request("/score/", { method: "POST", body: JSON.stringify(payload) });
            } else {
                delete payload.student_id;
                delete payload.exam_round;
                await this.request(`/score/update/${this.form.student_id}/${this.form.exam_round}`, { method: "PUT", body: JSON.stringify(payload) });
            }
        },
        async saveEmployment() {
            const payload = this.cleanPayload(this.form);
            const jobId = payload.id;
            delete payload.id;
            if (this.dialog.mode === "create") {
                await this.request("/employment/students/add", { method: "POST", body: JSON.stringify(payload) });
            } else {
                if (!jobId) throw new Error("旧就业更新接口需要填写就业记录ID");
                await this.request(`/employment/students/${jobId}`, { method: "POST", body: JSON.stringify(payload) });
            }
        },
        async saveClass() {
            const payload = this.cleanPayload(this.form);
            if (this.dialog.mode === "create") {
                await this.request("/classes/", { method: "POST", body: JSON.stringify(payload) });
            } else {
                payload.id = this.form.id;
                await this.request("/classes/", { method: "PUT", body: JSON.stringify(payload) });
            }
        },
        async saveTeacher() {
            const payload = this.cleanPayload(this.form);
            if (this.dialog.mode === "create") {
                await this.request("/teacher/add", { method: "POST", body: JSON.stringify(payload) });
            } else {
                payload.id = this.form.id;
                await this.request("/teacher/update", { method: "PUT", body: JSON.stringify(payload) });
            }
            await this.loadTeacherOptions();
        },
        async removeRow(row) {
            try {
                await ElementPlus.ElMessageBox.confirm("确认删除这条记录吗？", "删除确认", { type: "warning" });
                if (this.activeModule === "students") {
                    const studentName = row.name || row.student_name;
                    await this.request(`/students_delete/?student_name=${encodeURIComponent(studentName)}`, { method: "POST" });
                }
                if (this.activeModule === "scores") await this.request(`/score/delete/${row.student_id}/${row.exam_round}`, { method: "DELETE" });
                if (this.activeModule === "employment") await this.request(`/employment/students/by-student-id/${encodeURIComponent(row.student_id)}`, { method: "DELETE" });
                if (this.activeModule === "classes") await this.request(`/classes/${row.id}`, { method: "DELETE" });
                if (this.activeModule === "teachers") await this.request(`/teacher/delete/${row.id}`, { method: "DELETE" });
                ElementPlus.ElMessage.success("删除成功");
                await this.reload();
            } catch (error) {
                if (error !== "cancel") ElementPlus.ElMessage.error(error.message || "已取消");
            }
        },
        async queryStudentOne() {
            this.pager.page = 1;
            if (!this.studentExact.student_id && !this.studentExact.student_name && !this.studentExact.class_id) {
                const data = await this.request(`/students?skip=0&limit=${this.pager.size}`);
                this.rows = (data.students || []).map(this.normalizeStudent);
                this.pager.total = data.total || 0;
                return;
            }
            const params = new URLSearchParams();
            if (this.studentExact.student_id) params.set("student_id", this.studentExact.student_id);
            if (this.studentExact.student_name) params.set("student_name", this.studentExact.student_name);
            if (this.studentExact.class_id) params.set("class_id", this.studentExact.class_id);
            const data = await this.request(`/students/one?${params}`);
            this.rows = this.flattenStudentQuery(data);
            this.pager.total = this.rows.length;
        },
        async queryScoreRange() {
            const params = new URLSearchParams({
                min_score: this.scoreRange.min_score,
                max_score: this.scoreRange.max_score,
                page: this.pager.page,
                page_size: this.pager.size,
            });
            const data = await this.request(`/score/range/?${params}`);
            this.rows = data.items || [];
            this.pager.total = data.total || 0;
        },
        openBulkScore() {
            this.bulkDialog.text = JSON.stringify([
                { student_id: "S202501001", exam_round: 5, score: 88, remark: "批量录入示例" },
            ], null, 2);
            this.bulkDialog.visible = true;
        },
        async submitBulkScore() {
            const payload = JSON.parse(this.bulkDialog.text);
            await this.request("/score/bulk/", { method: "POST", body: JSON.stringify(payload) });
            ElementPlus.ElMessage.success("批量录入成功");
            this.bulkDialog.visible = false;
            this.reload();
        },
        async queryEmploymentByStudent() {
            if (!this.employmentQuery.student_id) return ElementPlus.ElMessage.warning("请输入学生编号");
            const data = await this.request(`/employment/students/${encodeURIComponent(this.employmentQuery.student_id)}`);
            this.rows = (data || []).map(this.normalizeEmployment);
            this.pager.total = this.rows.length;
        },
        async queryEmploymentByClass() {
            if (!this.employmentQuery.class_name) return ElementPlus.ElMessage.warning("请输入班级名称");
            const data = await this.request(`/employment/class/${encodeURIComponent(this.employmentQuery.class_name)}`);
            this.rows = (data || []).map(this.normalizeEmployment);
            this.pager.total = this.rows.length;
        },
        async queryEmploymentBySalary() {
            const params = new URLSearchParams({
                min_salary: this.employmentQuery.min_salary,
                max_salary: this.employmentQuery.max_salary,
            });
            const data = await this.request(`/jobs/salary-range?${params}`);
            this.rows = (data || []).map(this.normalizeEmployment);
            this.pager.total = this.rows.length;
        },
        async showDetail(row) {
            if (this.activeModule === "classes") {
                this.detailDrawer = { visible: true, data: await this.request(`/classes/${row.id}`) };
            }
            if (this.activeModule === "teachers") {
                this.detailDrawer = { visible: true, data: await this.request(`/teacher/get/${row.id}`) };
            }
        },
        openStatistic(key) {
            this.activeModule = "statistics";
            this.initStatisticParams(key);
            this.loadStatistic(key);
        },
        changeStatisticTab(key) {
            this.activeStatistic = key || this.activeStatistic;
            this.initStatisticParams(this.activeStatistic);
            this.loadStatistic(this.activeStatistic);
        },
        async loadStatistic(key) {
            this.activeStatistic = key || this.activeStatistic;
            this.statisticPager.page = 1;
            if (!Object.keys(this.statisticParams).length) this.initStatisticParams(this.activeStatistic);
            const entry = this.currentStatisticEntry;
            if (!entry) return;
            this.loading = true;
            try {
                const data = await this.request(this.buildStatisticUrl(entry));
                this.statisticRows = Array.isArray(data) ? data : [];
                this.statisticColumns = this.statisticRows.length ? Object.keys(this.statisticRows[0]) : [];
            } catch (error) {
                ElementPlus.ElMessage.error(error.message);
            } finally {
                this.loading = false;
            }
        },
        resetStatisticParams() {
            this.initStatisticParams(this.activeStatistic);
            this.loadStatistic(this.activeStatistic);
        },
        changeStatisticPage(page) {
            this.statisticPager.page = page;
        },
        changeStatisticSize(size) {
            this.statisticPager.size = size;
            this.statisticPager.page = 1;
        },
        normalizeStudent(item) {
            return { ...item };
        },
        filterStudentRows(students) {
            const studentId = String(this.filters.student_id || "").trim();
            const name = String(this.filters.name || "").trim();
            const classId = String(this.filters.class_id || "").trim();
            return students.map(this.normalizeStudent).filter((item) => {
                if (studentId && !String(item.student_id || "").includes(studentId)) return false;
                if (name && !String(item.name || "").includes(name)) return false;
                if (classId && String(item.class_id || "") !== classId) return false;
                return true;
            });
        },
        flattenStudentQuery(data) {
            const items = [data.select_id, data.select_name, data.class_id].flatMap((group) => {
                if (Array.isArray(group)) return group;
                if (group) return [group];
                return [];
            });
            const seen = new Set();
            return items.map(this.normalizeStudent).filter((item) => {
                const key = item.student_id || `${item.name}-${item.class_id}`;
                if (seen.has(key)) return false;
                seen.add(key);
                return true;
            });
        },
        normalizeClass(item) {
            const teachers = item.teachers || [];
            return {
                ...item,
                teacher_ids: teachers.map((teacher) => teacher.id),
                teacher_names: teachers.map((teacher) => teacher.name),
            };
        },
        normalizeEmployment(item) {
            return {
                id: item.id,
                student_id: item.student_id || item["学生编号"],
                name: item.name || item["学生姓名"],
                class_name: item.class_name || item["班级名称"],
                job_open_date: item.job_open_date || item["就业开放时间"],
                offer_date: item.offer_date || item["Offer下发时间"],
                company_name: item.company_name || item["公司名称"],
                salary: item.salary ?? item["薪资"],
                position: item.position || item["职位"],
            };
        },
        money(value) {
            return `¥${Number(value || 0).toLocaleString("zh-CN", { maximumFractionDigits: 2 })}`;
        },
        roleLabel(role) {
            return roleLabels[role] || "用户";
        },
        fieldLabel(field) {
            return detailGroupLabels[field] || fieldLabels[field] || field;
        },
        detailRecords(value) {
            if (Array.isArray(value)) {
                if (!value.length) return [{ title: "详情信息", entries: [{ key: "empty", label: "返回内容", value: "暂无数据" }] }];
                return value.map((item, index) => ({
                    title: `第 ${index + 1} 条记录`,
                    entries: this.detailEntries(item),
                }));
            }
            return [{ title: "详情信息", entries: this.detailEntries(value) }];
        },
        detailEntries(value) {
            if (!value || typeof value !== "object") {
                return [{ key: "value", label: "返回内容", value: this.detailValue(value) }];
            }
            return Object.entries(value).map(([key, item]) => ({
                key,
                label: this.fieldLabel(key),
                value: this.detailValue(item),
            }));
        },
        detailValue(value) {
            if (value === null || value === undefined || value === "") return "-";
            if (typeof value === "boolean") return value ? "是" : "否";
            if (Array.isArray(value)) {
                if (!value.length) return "暂无数据";
                return value.map((item) => this.detailValue(item)).join("；");
            }
            if (typeof value === "object") {
                return Object.entries(value)
                    .map(([key, item]) => `${this.fieldLabel(key)}：${this.detailValue(item)}`)
                    .join("；");
            }
            return String(value);
        },
        detailRecords(value) {
            if (Array.isArray(value)) {
                if (!value.length) return [{ title: "详情信息", entries: [{ key: "empty", label: "返回内容", value: "暂无数据" }] }];
                return value.map((item, index) => ({
                    title: `第${index + 1}条记录`,
                    entries: this.detailEntries(item),
                }));
            }
            if (value && typeof value === "object") {
                return Object.entries(value).flatMap(([key, item]) => this.detailRecordFromEntry(key, item));
            }
            return [{ title: "详情信息", entries: this.detailEntries(value) }];
        },
        detailRecordFromEntry(key, item) {
            const label = this.fieldLabel(key);
            if (Array.isArray(item)) {
                if (!item.length) return [{ title: label, entries: [{ key: `${key}-empty`, label, value: "暂无数据" }] }];
                return item.map((row, index) => ({
                    title: item.length > 1 ? `${label}${index + 1}` : label,
                    entries: row && typeof row === "object" ? this.studentDetailEntries(row) : [{ key: `${key}-${index}`, label, value: this.detailValue(row) }],
                }));
            }
            if (item && typeof item === "object") {
                return [{ title: this.fieldLabel(key), entries: this.studentDetailEntries(item) }];
            }
            return [{ title: label, entries: [{ key, label, value: this.detailValue(item) }] }];
        },
        detailEntries(value) {
            if (!value || typeof value !== "object") {
                return [{ key: "value", label: "返回内容", value: this.detailValue(value) }];
            }
            return Object.entries(value).map(([key, item]) => ({
                key,
                label: this.fieldLabel(key),
                value: this.detailValue(item),
            }));
        },
        studentDetailEntries(value) {
            const used = new Set();
            const entries = studentDetailFields
                .filter((field) => Object.prototype.hasOwnProperty.call(value, field.key))
                .map((field) => {
                    used.add(field.key);
                    return {
                        key: field.key,
                        label: field.label,
                        value: this.detailValue(value[field.key]),
                    };
                });
            Object.entries(value).forEach(([key, item]) => {
                if (!used.has(key)) {
                    entries.push({ key, label: this.fieldLabel(key), value: this.detailValue(item) });
                }
            });
            return entries.length ? entries : [{ key: "empty", label: "返回内容", value: "暂无数据" }];
        },
        detailValue(value) {
            if (value === null || value === undefined || value === "") return "-";
            if (typeof value === "boolean") return value ? "是" : "否";
            if (Array.isArray(value)) {
                if (!value.length) return "暂无数据";
                return value.map((item) => this.detailValue(item)).join("；");
            }
            if (typeof value === "object") {
                return Object.entries(value)
                    .map(([key, item]) => `${this.fieldLabel(key)}：${this.detailValue(item)}`)
                    .join("；");
            }
            return String(value);
        },
        normalizeTags(value) {
            if (Array.isArray(value)) return value.length ? value : ["-"];
            if (!value) return ["-"];
            return String(value).split(",").map((item) => item.trim()).filter(Boolean);
        },
        pretty(value) {
            return JSON.stringify(value, null, 2);
        },
    },
}).use(ElementPlus).mount("#app");
