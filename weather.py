from dataclasses import dataclass

import requests


class WeatherClientError(Exception):
    """Base error for failures while retrieving weather data."""


class InvalidApiKeyError(WeatherClientError):
    pass


class CityNotFoundError(WeatherClientError):
    pass


class WeatherServiceError(WeatherClientError):
    pass


@dataclass(frozen=True)
class Weather:
    city: str
    temperature: float
    description: str


class OpenWeatherClient:
    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = "https://api.openweathermap.org/data/2.5/weather",
        timeout: float = 5.0,
    ):
        if not api_key:
            raise InvalidApiKeyError("An OpenWeather API key is required")

        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout

    def get_current_weather(self, city: str) -> Weather:
        if not city.strip():
            raise CityNotFoundError("A city is required")

        try:
            response = requests.get(
                self.base_url,
                params={
                    "q": city,
                    "appid": self.api_key,
                    "units": "metric",
                },
                timeout=self.timeout,
            )
        except requests.Timeout as error:
            raise WeatherServiceError("The weather service timed out") from error
        except requests.RequestException as error:
            raise WeatherServiceError("The weather service is unavailable") from error

        if response.status_code == 401:
            raise InvalidApiKeyError("The OpenWeather API key is invalid")
        if response.status_code == 404:
            raise CityNotFoundError(f"City not found: {city}")
        if response.status_code >= 400:
            raise WeatherServiceError("The weather service returned an error")

        try:
            payload = response.json()
            return Weather(
                city=payload["name"],
                temperature=payload["main"]["temp"],
                description=payload["weather"][0]["description"],
            )
        except (KeyError, IndexError, TypeError, ValueError) as error:
            raise WeatherServiceError("The weather response was invalid") from error
