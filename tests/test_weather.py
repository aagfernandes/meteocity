import pytest
import requests

from weather import (
    CityNotFoundError,
    InvalidApiKeyError,
    OpenWeatherClient,
    Weather,
    WeatherServiceError,
)


class FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self.payload = payload

    def json(self):
        return self.payload


def test_returns_current_weather(monkeypatch):
    def fake_get(url, *, params, timeout):
        assert url.endswith("/weather")
        assert params == {"q": "London", "appid": "test-key", "units": "metric"}
        assert timeout == 5.0
        return FakeResponse(
            200,
            {
                "name": "London",
                "main": {"temp": 22.66},
                "weather": [{"description": "broken clouds"}],
            },
        )

    monkeypatch.setattr("weather.requests.get", fake_get)

    result = OpenWeatherClient("test-key").get_current_weather("London")

    assert result == Weather("London", 22.66, "broken clouds")


def test_rejects_missing_api_key():
    with pytest.raises(InvalidApiKeyError):
        OpenWeatherClient("")


def test_maps_invalid_api_key(monkeypatch):
    monkeypatch.setattr(
        "weather.requests.get",
        lambda *args, **kwargs: FakeResponse(401, {"message": "Invalid API key"}),
    )

    with pytest.raises(InvalidApiKeyError):
        OpenWeatherClient("bad-key").get_current_weather("London")


def test_maps_unknown_city(monkeypatch):
    monkeypatch.setattr(
        "weather.requests.get",
        lambda *args, **kwargs: FakeResponse(404, {"message": "city not found"}),
    )

    with pytest.raises(CityNotFoundError):
        OpenWeatherClient("test-key").get_current_weather("Atlantis")


def test_maps_timeout(monkeypatch):
    def fake_get(*args, **kwargs):
        raise requests.Timeout

    monkeypatch.setattr("weather.requests.get", fake_get)

    with pytest.raises(WeatherServiceError, match="timed out"):
        OpenWeatherClient("test-key").get_current_weather("London")


def test_rejects_malformed_weather_response(monkeypatch):
    monkeypatch.setattr(
        "weather.requests.get",
        lambda *args, **kwargs: FakeResponse(200, {"name": "London"}),
    )

    with pytest.raises(WeatherServiceError, match="invalid"):
        OpenWeatherClient("test-key").get_current_weather("London")


def test_rejects_blank_city_before_request(monkeypatch):
    def fake_get(*args, **kwargs):
        pytest.fail("HTTP request should not be made")

    monkeypatch.setattr("weather.requests.get", fake_get)

    with pytest.raises(CityNotFoundError):
        OpenWeatherClient("test-key").get_current_weather("  ")
