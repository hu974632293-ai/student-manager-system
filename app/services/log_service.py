from app.core.response import success


class LogService:
    @staticmethod
    def list_recent_logs(limit: int = 20):
        safe_limit = min(max(int(limit), 1), 100)
        return success(
            {
                "total": 0,
                "limit": safe_limit,
                "items": [],
            },
            "logs found",
        )
