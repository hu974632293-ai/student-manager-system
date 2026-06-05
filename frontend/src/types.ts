export type Role = "admin" | "teacher" | "student" | "consultant";

export interface ApiEnvelope<T> {
  code: number;
  msg: string;
  data: T;
}

export interface UserProfile {
  id: number;
  username: string;
  real_name: string;
  role: Role;
  teacher_id?: number | null;
  student_id?: string | null;
  permissions: string[];
  modules: string[];
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: UserProfile;
}

export interface MenuModule {
  key: string;
  title: string;
  subtitle: string;
  route: string;
  icon: string;
  roles: Role[];
}

export interface TableColumn {
  key: string;
  label: string;
}

export interface DataQueryRequest {
  question: string;
  limit: number;
  show_sql: boolean;
}

export interface DataQueryResult {
  question: string;
  sql: string;
  columns: string[];
  rows: Record<string, unknown>[];
  row_count: number;
  summary: string;
}
