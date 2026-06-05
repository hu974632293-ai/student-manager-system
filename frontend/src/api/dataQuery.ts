import { request } from "@/api/http";
import type { DataQueryRequest, DataQueryResult } from "@/types";

export function runDataQuery(payload: DataQueryRequest) {
  return request<DataQueryResult>("/data-query/nl2sql", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
