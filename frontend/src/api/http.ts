import { ElMessage } from "element-plus";

import type { ApiEnvelope } from "@/types";

const TOKEN_KEY = "wolin_token";

const CLIENT_ERROR_MAP: Record<string, string> = {
  "Failed to fetch": "无法连接后端服务，请确认后端已启动",
  "Load failed": "无法连接后端服务，请确认后端已启动",
  "NetworkError when attempting to fetch resource.": "网络请求失败，请确认后端服务和网络连接正常",
};

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

  let response: Response;
  try {
    response = await fetch(url, {
      ...options,
      headers,
    });
  } catch (error) {
    const rawMessage = error instanceof Error ? error.message : "";
    throw new ApiError(CLIENT_ERROR_MAP[rawMessage] || "网络请求失败，请确认后端服务已启动", 0);
  }

  let payload: ApiEnvelope<T> | null = null;
  try {
    payload = (await response.json()) as ApiEnvelope<T>;
  } catch {
    throw new ApiError("服务响应格式异常，请稍后重试", response.status);
  }
  if (!response.ok) {
    throw new ApiError(payload?.msg || "请求失败，请稍后重试", response.status);
  }
  if (payload.code !== 1) {
    throw new ApiError(payload.msg || "业务处理失败，请检查输入后重试", response.status);
  }
  return payload.data;
}

export function notifyError(error: unknown) {
  const rawMessage = error instanceof Error ? error.message : "";
  const message = CLIENT_ERROR_MAP[rawMessage] || rawMessage || "请求失败，请稍后重试";
  ElMessage.error(message);
}
