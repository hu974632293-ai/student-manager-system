import type { MenuModule, Role } from "@/types";

export const roleLabels: Record<Role, string> = {
  admin: "管理员",
  teacher: "教师",
  student: "学生",
  consultant: "顾问",
};

export const groupLabels: Record<NonNullable<MenuModule["group"]>, string> = {
  business: "教务管理",
  tools: "系统工具",
};

export const modules: MenuModule[] = [
  {
    key: "overview",
    title: "总览",
    subtitle: "关键指标、风险提醒与快捷入口",
    route: "/dashboard",
    icon: "DataBoard",
    roles: ["admin", "teacher", "student", "consultant"],
  },
  {
    key: "students",
    title: "学生管理",
    subtitle: "学生档案、范围数据与基础维护",
    route: "/students",
    icon: "User",
    group: "business",
    roles: ["admin", "teacher", "consultant"],
  },
  {
    key: "classes",
    title: "班级管理",
    subtitle: "班级信息与授课关系",
    route: "/classes",
    icon: "OfficeBuilding",
    group: "business",
    roles: ["admin", "teacher"],
  },
  {
    key: "teachers",
    title: "教师管理",
    subtitle: "教师档案与联系方式",
    route: "/teachers",
    icon: "Avatar",
    group: "business",
    roles: ["admin", "teacher"],
  },
  {
    key: "scores",
    title: "成绩管理",
    subtitle: "成绩查询、录入与异常识别",
    route: "/scores",
    icon: "Memo",
    group: "business",
    roles: ["admin", "teacher", "student"],
  },
  {
    key: "employment",
    title: "就业管理",
    subtitle: "就业进展、企业去向与薪资数据",
    route: "/employment",
    icon: "Briefcase",
    group: "business",
    roles: ["admin", "teacher", "student", "consultant"],
  },
  {
    key: "statistics",
    title: "统计分析",
    subtitle: "成绩、就业与班级统计",
    route: "/statistics",
    icon: "TrendCharts",
    group: "business",
    roles: ["admin", "teacher"],
  },
  {
    key: "letters",
    title: "邮件发送",
    subtitle: "生成信件或直接发送邮件",
    route: "/letters",
    icon: "Message",
    group: "tools",
    roles: ["admin", "teacher", "consultant"],
  },
  {
    key: "weather",
    title: "天气查询",
    subtitle: "按城市或坐标查询实时天气",
    route: "/weather",
    icon: "Sunny",
    group: "tools",
    roles: ["admin", "teacher", "student", "consultant"],
  },
  {
    key: "geocode",
    title: "经纬度查询",
    subtitle: "按城市或地址查询坐标信息",
    route: "/geocode",
    icon: "Location",
    group: "tools",
    roles: ["admin", "teacher", "student", "consultant"],
  },
  {
    key: "ai-chat",
    title: "普通问答",
    subtitle: "大模型普通问答、记忆与摘要",
    route: "/ai-chat",
    icon: "ChatDotRound",
    group: "tools",
    roles: ["admin", "teacher", "student", "consultant"],
  },
  {
    key: "data-query",
    title: "智能问数",
    subtitle: "自然语言转只读 SQL",
    route: "/data-query",
    icon: "Search",
    group: "tools",
    roles: ["admin", "teacher"],
  },
  {
    key: "logs",
    title: "系统日志",
    subtitle: "系统审计与访问记录",
    route: "/logs",
    icon: "Document",
    group: "tools",
    roles: ["admin"],
  },
  {
    key: "knowledge-base",
    title: "知识库",
    subtitle: "本地知识库问答暂未开放",
    route: "/knowledge-base",
    icon: "Collection",
    roles: ["admin", "teacher", "student", "consultant"],
    hidden: true,
  },
  {
    key: "agents",
    title: "智能体",
    subtitle: "任务流与工具调用暂未开放",
    route: "/agents",
    icon: "Operation",
    roles: ["admin", "teacher", "student", "consultant"],
    hidden: true,
  },
  {
    key: "permissions",
    title: "权限矩阵",
    subtitle: "当前角色模块与权限点总览",
    route: "/permissions",
    icon: "Lock",
    group: "tools",
    roles: ["admin"],
  },
];

export function roleModules(role?: Role, serverModules: string[] = []) {
  const allowed = new Set(serverModules);
  return modules.filter(
    (item) =>
      !item.hidden &&
      item.roles.includes(role as Role) &&
      (allowed.size === 0 || allowed.has(item.key)),
  );
}

export function findModule(key?: string) {
  return modules.find((item) => item.key === key);
}
