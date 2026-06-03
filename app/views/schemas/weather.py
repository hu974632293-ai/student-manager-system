from typing import Optional

from pydantic import BaseModel, Field, model_validator


class WeatherQueryRequest(BaseModel):
    city: Optional[str] = Field(default=None, max_length=100)
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    @model_validator(mode="after")
    def validate_city_or_coordinates(self):
        if self.city:
            return self
        if self.latitude is not None and self.longitude is not None:
            return self
        raise ValueError("city or latitude/longitude is required")


class CoordinateQueryRequest(BaseModel):
    city: str = Field(min_length=1, max_length=100)
