from app.core.response import fail, success
from app.core.weather_client import (
    WeatherClient,
    WeatherConfigError,
    WeatherRequestError,
    WeatherResponseError,
)
from app.views.schemas.weather import CoordinateQueryRequest, WeatherQueryRequest


class WeatherService:
    client: WeatherClient | None = None

    @staticmethod
    def get_client() -> WeatherClient:
        if WeatherService.client is None:
            WeatherService.client = WeatherClient()
        return WeatherService.client

    @staticmethod
    def query_weather(payload: WeatherQueryRequest):
        try:
            data = WeatherService.get_client().query_weather(payload.city, payload.latitude, payload.longitude)
            return success(data)
        except (WeatherConfigError, WeatherRequestError, WeatherResponseError) as exc:
            return fail(str(exc))

    @staticmethod
    def query_coordinates(payload: CoordinateQueryRequest):
        try:
            data = WeatherService.get_client().query_coordinates(payload.city)
            return success(data)
        except (WeatherConfigError, WeatherRequestError, WeatherResponseError) as exc:
            return fail(str(exc))
