import pytest

from app.core.weather_client import WeatherClient, WeatherConfig, WeatherResponseError


def test_reverse_geocode_missing_adcode_returns_chinese_error():
    client = WeatherClient(WeatherConfig(api_key="test", base_url="https://example.com", timeout_seconds=1))

    def fake_get(url, params):
        return {"status": "1", "regeocode": {"addressComponent": {}}}

    client._get = fake_get

    with pytest.raises(WeatherResponseError, match="行政区编码"):
        client.query_adcode_by_location(40, 12)
