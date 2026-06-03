import json
import os
from dataclasses import dataclass
from urllib import error, parse, request

from dotenv import load_dotenv


DEFAULT_WEATHER_BASE_URL = "https://api.openweathermap.org"
DEFAULT_WEATHER_TIMEOUT_SECONDS = 30


class WeatherConfigError(Exception):
    pass


class WeatherRequestError(Exception):
    pass


class WeatherResponseError(Exception):
    pass


@dataclass(frozen=True)
class WeatherConfig:
    api_key: str | None
    base_url: str
    timeout_seconds: int

    @classmethod
    def from_env(cls) -> "WeatherConfig":
        load_dotenv()
        timeout_value = os.getenv("WEATHER_TIMEOUT_SECONDS", str(DEFAULT_WEATHER_TIMEOUT_SECONDS))
        try:
            timeout_seconds = int(timeout_value)
        except ValueError as exc:
            raise WeatherConfigError("WEATHER_TIMEOUT_SECONDS must be an integer") from exc
        if timeout_seconds <= 0:
            raise WeatherConfigError("WEATHER_TIMEOUT_SECONDS must be greater than 0")

        return cls(
            api_key=os.getenv("WEATHER_API_KEY") or os.getenv("OPENWEATHER_API_KEY"),
            base_url=os.getenv("WEATHER_BASE_URL", DEFAULT_WEATHER_BASE_URL).rstrip("/"),
            timeout_seconds=timeout_seconds,
        )

    def require_api_key(self) -> str:
        if not self.api_key:
            raise WeatherConfigError("WEATHER_API_KEY or OPENWEATHER_API_KEY is required")
        return self.api_key


class WeatherClient:
    def __init__(self, config: WeatherConfig | None = None):
        self.config = config or WeatherConfig.from_env()

    def query_weather(
        self,
        city: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
    ) -> dict:
        params = {"appid": self.config.require_api_key(), "units": "metric", "lang": "zh_cn"}
        if city:
            params["q"] = city
        elif latitude is not None and longitude is not None:
            params["lat"] = str(latitude)
            params["lon"] = str(longitude)
        else:
            raise WeatherConfigError("city or latitude/longitude is required")
        return self._get(f"{self.config.base_url}/data/2.5/weather", params)

    def query_coordinates(self, city: str) -> list[dict]:
        keyword = city.strip()
        if not keyword:
            raise WeatherConfigError("city is required")
        params = {"appid": self.config.require_api_key(), "q": keyword, "limit": "5"}
        data = self._get(f"{self.config.base_url}/geo/1.0/direct", params)
        if not isinstance(data, list):
            raise WeatherResponseError("geocode response must be a JSON array")
        return data

    def _get(self, url: str, params: dict[str, str]) -> dict | list:
        query = parse.urlencode(params)
        req = request.Request(f"{url}?{query}", method="GET")
        try:
            with request.urlopen(req, timeout=self.config.timeout_seconds) as response:
                status_code = getattr(response, "status", None) or response.getcode()
                response_body = response.read().decode("utf-8")
        except error.HTTPError as exc:
            message = self._read_error_message(exc)
            raise WeatherRequestError(f"weather request failed: HTTP {exc.code} {message}") from exc
        except (error.URLError, TimeoutError) as exc:
            raise WeatherRequestError(f"weather request failed: {exc}") from exc

        if status_code < 200 or status_code >= 300:
            raise WeatherRequestError(f"weather request failed: HTTP {status_code}")

        try:
            return json.loads(response_body)
        except json.JSONDecodeError as exc:
            raise WeatherResponseError("weather response is not valid JSON") from exc

    def _read_error_message(self, exc: error.HTTPError) -> str:
        try:
            body = exc.read().decode("utf-8")
            data = json.loads(body)
        except Exception:
            return str(exc.reason)
        if isinstance(data, dict):
            return str(data.get("message") or data)
        return str(data)
