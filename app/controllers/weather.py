from fastapi import APIRouter, Depends

from app.services.weather_service import WeatherService
from app.views.schemas.weather import CoordinateQueryRequest, WeatherQueryRequest


weather_router = APIRouter(prefix="/weather", tags=["weather"])


@weather_router.get("/current")
def query_weather(payload: WeatherQueryRequest = Depends()):
    return WeatherService.query_weather(payload)


@weather_router.get("/geocode")
def query_coordinates(payload: CoordinateQueryRequest = Depends()):
    return WeatherService.query_coordinates(payload)
