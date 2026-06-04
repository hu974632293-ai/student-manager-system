import time
from urllib.parse import quote_plus

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from app.core.logger import get_logger


logger = get_logger("request")

SENSITIVE_PARAM_NAMES = {
    "password",
    "token",
    "authorization",
    "secret",
    "api_key",
    "apikey",
}


def _is_sensitive_key(key: str) -> bool:
    lower_key = key.lower()
    return any(name in lower_key for name in SENSITIVE_PARAM_NAMES)


def _safe_query_string(request: Request) -> str:
    safe_items = []
    for key, value in request.query_params.multi_items():
        safe_value = "***" if _is_sensitive_key(key) else quote_plus(value)
        safe_items.append(f"{quote_plus(key)}={safe_value}")
    return "&".join(safe_items)


def _client_host(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start_time = time.perf_counter()
        method = request.method
        path = request.url.path
        query_string = _safe_query_string(request)
        client_host = _client_host(request)

        try:
            response = await call_next(request)
        except Exception:
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            logger.exception(
                "请求异常 method=%s path=%s query=%s duration_ms=%s ip=%s",
                method,
                path,
                query_string,
                duration_ms,
                client_host,
            )
            raise

        duration_ms = int((time.perf_counter() - start_time) * 1000)
        logger.info(
            "请求完成 method=%s path=%s query=%s status=%s duration_ms=%s ip=%s",
            method,
            path,
            query_string,
            response.status_code,
            duration_ms,
            client_host,
        )
        return response
