import type { MenuModule, Role } from "@/types";

export const roleLabels: Record<Role, string> = {
  admin: "管理员",
  teacher: "教师",
  student: "学生",
  consultant: "顾问",
};

export const modules: MenuModule[] = [
  {
    key: "overview",
    title: "总览",
    subtitle: "角色视角与系统概况",
    route: "/dashboard",
    icon: "DataBoard",
    roles: ["admin", "teacher", "student", "consultant"],
  },
  {
    key: "students",
    title: "学生",
    subtitle: "学生档案与范围数据",
    route: "/students",
    icon: "User",
    roles: ["admin", "teacher", "consultant"],
  },
  {
    key: "classes",
    title: "班级",
    subtitle: "班级与授课关系",
    route: "/classes",
    icon: "OfficeBuilding",
    roles: ["admin", "teacher"],
  },
  {
    key: "teachers",
    title: "教师",
    subtitle: "教师档案与联系方式",
    route: "/teachers",
    icon: "Avatar",
    roles: ["admin", "teacher"],
  },
  {
    key: "scores",
    title: "成绩",
    subtitle: "成绩查询与录入",
    route: "/scores",
    icon: "Memo",
    roles: ["admin", "teacher", "student"],
  },
  {
    key: "employment",
    title: "就业",
    subtitle: "就业进展与薪资数据",
    route: "/employment",
    icon: "Briefcase",
    roles: ["admin", "teacher", "student", "consultant"],
  },
  {
    key: "statistics",
    title: "统计",
    subtitle: "成绩与就业统计",
    route: "/statistics",
    icon: "TrendCharts",
    roles: ["admin", "teacher"],
  },
  {
    key: "logs",
    title: "日志",
    subtitle: "系统审计与访问记录",
    route: "/logs",
    icon: "Document",
    roles: ["admin"],
  },
  {
    key: "ai-chat",
    title: "普通问答",
    subtitle: "大模型普通问答",
    route: "/ai-chat",
    icon: "ChatDotRound",
    roles: ["admin", "teacher", "student", "consultant"],
  },
  {
    key: "data-query",
    title: "智能问数",
    subtitle: "自然语言转 SQL",
    route: "/data-query",
    icon: "Search",
    roles: ["admin", "teacher"],
  },
  {
    key: "knowledge-base",
    title: "知识库",
    subtitle: "本地知识库问答",
    route: "/knowledge-base",
    icon: "Collection",
    roles: ["admin", "teacher", "student", "consultant"],
  },
  {
    key: "agents",
    title: "智能体",
    subtitle: "任务流与工具调用",
    route: "/agents",
    icon: "Operation",
    roles: ["admin", "teacher", "student", "consultant"],
  },
  {
    key: "permissions",
    title: "权限",
    subtitle: "账号与权限配置",
    route: "/permissions",
    icon: "Lock",
    roles: ["admin"],
  },
];

export function roleModules(role?: Role, serverModules: string[] = []) {
  const allowed = new Set(serverModules);
  return modules.filter((item) => item.roles.includes(role as Role) && (allowed.size === 0 || allowed.has(item.key)));
}
