import { defineStore } from "pinia";

import { clearToken, request, setToken } from "@/api/http";
import type { LoginResponse, UserProfile } from "@/types";

const USER_KEY = "wolin_user";

interface AuthState {
  token: string;
  user: UserProfile | null;
}

export const useAuthStore = defineStore("auth", {
  state: (): AuthState => ({
    token: localStorage.getItem("wolin_token") || "",
    user: JSON.parse(localStorage.getItem(USER_KEY) || "null") as UserProfile | null,
  }),
  getters: {
    isAuthenticated: (state) => Boolean(state.token && state.user),
    role: (state) => state.user?.role,
    modules: (state) => state.user?.modules || [],
    permissions: (state) => state.user?.permissions || [],
  },
  actions: {
    async login(username: string, password: string) {
      const data = await request<LoginResponse>("/auth/login", {
        method: "POST",
        body: JSON.stringify({ username, password }),
      });
      this.token = data.access_token;
      this.user = data.user;
      setToken(data.access_token);
      localStorage.setItem(USER_KEY, JSON.stringify(data.user));
    },
    async fetchMe() {
      const user = await request<UserProfile>("/auth/me");
      this.user = user;
      localStorage.setItem(USER_KEY, JSON.stringify(user));
      return user;
    },
    logout() {
      this.token = "";
      this.user = null;
      clearToken();
      localStorage.removeItem(USER_KEY);
    },
  },
});
