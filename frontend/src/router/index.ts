import { createRouter, createWebHistory, type RouteRecordRaw } from "vue-router";

import { useAuthStore } from "@/stores/auth";

const routes: RouteRecordRaw[] = [
  {
    path: "/login",
    name: "login",
    component: () => import("@/views/LoginView.vue"),
    meta: { public: true },
  },
  {
    path: "/",
    component: () => import("@/components/AppShell.vue"),
    children: [
      { path: "", redirect: "/dashboard" },
      {
        path: "dashboard",
        name: "dashboard",
        component: () => import("@/views/DashboardView.vue"),
        meta: { module: "overview" },
      },
      {
        path: "students",
        name: "students",
        component: () => import("@/views/ModuleListView.vue"),
        meta: { module: "students" },
      },
      {
        path: "profile",
        name: "profile",
        component: () => import("@/views/ProfileView.vue"),
        meta: { module: "profile" },
      },
      {
        path: "classes",
        name: "classes",
        component: () => import("@/views/ModuleListView.vue"),
        meta: { module: "classes" },
      },
      {
        path: "teachers",
        name: "teachers",
        component: () => import("@/views/ModuleListView.vue"),
        meta: { module: "teachers" },
      },
      {
        path: "scores",
        name: "scores",
        component: () => import("@/views/ModuleListView.vue"),
        meta: { module: "scores" },
      },
      {
        path: "employment",
        name: "employment",
        component: () => import("@/views/ModuleListView.vue"),
        meta: { module: "employment" },
      },
      {
        path: "statistics",
        name: "statistics",
        component: () => import("@/views/StatisticsView.vue"),
        meta: { module: "statistics" },
      },
      {
        path: "letters",
        name: "letters",
        component: () => import("@/views/LetterView.vue"),
        meta: { module: "letters" },
      },
      {
        path: "weather",
        name: "weather",
        component: () => import("@/views/WeatherView.vue"),
        meta: { module: "weather" },
      },
      {
        path: "geocode",
        name: "geocode",
        component: () => import("@/views/GeocodeView.vue"),
        meta: { module: "geocode" },
      },
      {
        path: "logs",
        name: "logs",
        component: () => import("@/views/LogsView.vue"),
        meta: { module: "logs" },
      },
      {
        path: "ai-chat",
        name: "ai-chat",
        component: () => import("@/views/AiChatView.vue"),
        meta: { module: "ai-chat" },
      },
      {
        path: "data-query",
        name: "data-query",
        component: () => import("@/views/DataQueryView.vue"),
        meta: { module: "data-query" },
      },
      {
        path: "permissions",
        name: "permissions",
        component: () => import("@/views/PermissionsView.vue"),
        meta: { module: "permissions" },
      },
      {
        path: "forbidden",
        name: "forbidden",
        component: () => import("@/views/ForbiddenView.vue"),
      },
    ],
  },
  {
    path: "/:pathMatch(.*)*",
    name: "not-found",
    component: () => import("@/views/NotFoundView.vue"),
  },
];

export const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach(async (to) => {
  const auth = useAuthStore();
  if (to.meta.public) {
    if (to.name === "login" && auth.isAuthenticated) return "/dashboard";
    return true;
  }
  if (!auth.token) return "/login";
  if (!auth.user || !auth.loadedFromServer) {
    try {
      await auth.fetchMe();
    } catch {
      auth.logout();
      return "/login";
    }
  }
  const moduleKey = to.meta.module as string | undefined;
  if (moduleKey && !auth.modules.includes(moduleKey)) return "/forbidden";
  return true;
});
