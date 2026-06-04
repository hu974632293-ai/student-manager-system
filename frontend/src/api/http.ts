import { ElMessage } from "element-plus";

import type { ApiEnvelope } from "@/types";

const TOKEN_KEY = "wolin_token";

export class ApiError extends Error {
  status: number;

  constructor(message: string, status = 0) {
    super(message);
    this.status = status;
  }
}

export function getToken() {
  return localStorage.getItem(TOKEN_KEY) || "";
}

export function setToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

export async function request<T>(url: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set("Content-Type", headers.get("Content-Type") || "application/json");
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const response = await fetch(url, {
    ...options,
    headers,
  });

  let payload: ApiEnvelope<T> | null = null;
  try {
    payload = (await response.json()) as ApiEnvelope<T>;
  } catch {
    throw new ApiError("服务响应格式异常", response.status);
  }
  if (!response.ok) {
    throw new ApiError(payload?.msg || "请求失败", response.status);
  }
  if (payload.code !== 1) {
    throw new ApiError(payload.msg || "业务处理失败", response.status);
  }
  return payload.data;
}

export function notifyError(error: unknown) {
  const message = error instanceof Error ? error.message : "请求失败";
  ElMessage.error(message);
}
