import json
import os
from dataclasses import dataclass
from urllib import error, parse, request

from dotenv import load_dotenv


DEFAULT_WEATHER_BASE_URL = "https://restapi.amap.com"
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
            api_key=os.getenv("WEATHER_API_KEY") or os.getenv("AMAP_API_KEY") or os.getenv("OPENWEATHER_API_KEY"),
            base_url=os.getenv("WEATHER_BASE_URL", DEFAULT_WEATHER_BASE_URL).rstrip("/"),
            timeout_seconds=timeout_seconds,
        )

    def require_api_key(self) -> str:
        if not self.api_key:
            raise WeatherConfigError("WEATHER_API_KEY or AMAP_API_KEY is required")
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
        api_key = self.config.require_api_key()
        if city:
            geocodes = self.query_coordinates(city)
            if not geocodes:
                raise WeatherResponseError("city geocode result is empty")
            adcode = geocodes[0].get("adcode")
        elif latitude is not None and longitude is not None:
            adcode = self.query_adcode_by_location(latitude, longitude)
        else:
            raise WeatherConfigError("city or latitude/longitude is required")

        if not adcode:
            raise WeatherResponseError("weather city adcode is empty")
        params = {"key": api_key, "city": str(adcode), "extensions": "base", "output": "JSON"}
        data = self._get(f"{self.config.base_url}/v3/weather/weatherInfo", params)
        self._ensure_amap_success(data)
        return data

    def query_coordinates(self, city: str) -> list[dict]:
        keyword = city.strip()
        if not keyword:
            raise WeatherConfigError("city is required")
        params = {"key": self.config.require_api_key(), "address": keyword, "output": "JSON"}
        data = self._get(f"{self.config.base_url}/v3/geocode/geo", params)
        self._ensure_amap_success(data)
        geocodes = data.get("geocodes")
        if not isinstance(geocodes, list):
            raise WeatherResponseError("geocode response missing geocodes")
        return geocodes

    def query_adcode_by_location(self, latitude: float, longitude: float) -> str:
        params = {
            "key": self.config.require_api_key(),
            "location": f"{longitude},{latitude}",
            "output": "JSON",
        }
        data = self._get(f"{self.config.base_url}/v3/geocode/regeo", params)
        self._ensure_amap_success(data)
        regeocode = data.get("regeocode")
        if not isinstance(regeocode, dict):
            raise WeatherResponseError("reverse geocode response missing regeocode")
        address_component = regeocode.get("addressComponent")
        if not isinstance(address_component, dict):
            raise WeatherResponseError("reverse geocode response missing addressComponent")
        adcode = address_component.get("adcode")
        if not isinstance(adcode, str) or not adcode:
            raise WeatherResponseError("reverse geocode response missing adcode")
        return adcode

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

    def _ensure_amap_success(self, data: dict | list) -> None:
        if not isinstance(data, dict):
            raise WeatherResponseError("weather response must be a JSON object")
        if data.get("status") != "1":
            message = data.get("info") or data.get("infocode") or data
            raise WeatherRequestError(f"weather request failed: {message}")

    def _read_error_message(self, exc: error.HTTPError) -> str:
        try:
            body = exc.read().decode("utf-8")
            data = json.loads(body)
        except Exception:
            return str(exc.reason)
        if isinstance(data, dict):
            return str(data.get("message") or data)
        return str(data)
