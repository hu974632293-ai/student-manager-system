from fastapi import APIRouter, Depends

from app.controllers.auth import require_roles
from app.services.weather_service import WeatherService
from app.views.schemas.weather import CoordinateQueryRequest, WeatherQueryRequest


weather_router = APIRouter(prefix="/weather", tags=["weather"])


@weather_router.get("/current", summary="根据城市或经纬度查询当前天气")
def query_weather(
    payload: WeatherQueryRequest = Depends(),
    current_user=Depends(require_roles("admin", "teacher", "student", "consultant")),
):
    return WeatherService.query_weather(payload)


@weather_router.get("/geocode", summary="根据城市名称查询经纬度")
def query_coordinates(
    payload: CoordinateQueryRequest = Depends(),
    current_user=Depends(require_roles("admin", "teacher", "student", "consultant")),
):
    return WeatherService.query_coordinates(payload)
