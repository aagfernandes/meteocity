import hashlib
import hmac
import os
import time

from dotenv import load_dotenv
from flask import Flask, jsonify, request

from weather import (
    CityNotFoundError,
    InvalidApiKeyError,
    OpenWeatherClient,
    WeatherClientError,
)

load_dotenv()

_UNSET = object()


def create_app(weather_client=None, signing_secret=_UNSET) -> Flask:
    app = Flask(__name__)
    app.config["SLACK_SIGNING_SECRET"] = (
        os.getenv("SLACK_SIGNING_SECRET")
        if signing_secret is _UNSET
        else signing_secret
    )
    app.config["OPENWEATHER_API_KEY"] = os.getenv("OPENWEATHER_API_KEY")

    def is_valid_slack_request() -> bool:
        secret = app.config["SLACK_SIGNING_SECRET"]
        if not secret:
            return True

        timestamp = request.headers.get("X-Slack-Request-Timestamp", "")
        signature = request.headers.get("X-Slack-Signature", "")
        try:
            timestamp_value = int(timestamp)
        except ValueError:
            return False

        if abs(time.time() - timestamp_value) > 300:
            return False

        body = request.get_data(as_text=True)
        basestring = f"v0:{timestamp}:{body}".encode()
        expected_signature = (
            "v0=" + hmac.new(secret.encode(), basestring, hashlib.sha256).hexdigest()
        )
        return hmac.compare_digest(expected_signature, signature)

    @app.get("/health")
    def health_check():
        return jsonify({"status": "ok"})

    @app.post("/slack/weather")
    def slack_weather():
        if not is_valid_slack_request():
            return jsonify({"error": "Invalid Slack signature"}), 401

        city = request.form.get("text", "").strip()
        if not city:
            return (
                jsonify(
                    {
                        "response_type": "ephemeral",
                        "text": "Please provide a city, for example: `/jumo_weather London`",
                    }
                ),
                400,
            )

        try:
            client = weather_client or OpenWeatherClient(
                app.config["OPENWEATHER_API_KEY"]
            )
            weather = client.get_current_weather(city)
        except CityNotFoundError:
            return jsonify(_slack_error(f"I could not find a city named {city}."))
        except InvalidApiKeyError:
            return jsonify(
                _slack_error("The weather service is not configured correctly.")
            ), 500
        except WeatherClientError:
            return jsonify(
                _slack_error("The weather service is temporarily unavailable.")
            ), 502

        return jsonify(
            {
                "response_type": "in_channel",
                "text": (
                    f"The current temperature in {weather.city} is "
                    f"{weather.temperature:.1f}°C with {weather.description}."
                ),
            }
        )

    return app


def _slack_error(message: str) -> dict:
    return {"response_type": "ephemeral", "text": message}


app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=True)
