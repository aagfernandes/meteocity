import hashlib
import hmac
import time

from app import create_app
from weather import CityNotFoundError, Weather


class FakeWeatherClient:
    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error
        self.requested_city = None

    def get_current_weather(self, city):
        self.requested_city = city
        if self.error:
            raise self.error
        return self.result


def slack_headers(body, secret):
    timestamp = str(int(time.time()))
    base_string = f"v0:{timestamp}:{body}".encode()
    signature = hmac.new(secret.encode(), base_string, hashlib.sha256).hexdigest()
    return {
        "X-Slack-Request-Timestamp": timestamp,
        "X-Slack-Signature": f"v0={signature}",
    }


def test_returns_weather_for_slack_command():
    client = FakeWeatherClient(Weather("London", 22.66, "broken clouds"))
    app = create_app(weather_client=client, signing_secret="test-secret")
    body = "text=London"

    response = app.test_client().post(
        "/slack/weather",
        data=body,
        content_type="application/x-www-form-urlencoded",
        headers=slack_headers(body, "test-secret"),
    )

    assert response.status_code == 200
    assert response.get_json() == {
        "response_type": "in_channel",
        "text": "The current temperature in London is 22.7°C with broken clouds.",
    }
    assert client.requested_city == "London"


def test_rejects_missing_city():
    app = create_app(weather_client=FakeWeatherClient(), signing_secret="test-secret")
    body = "text="

    response = app.test_client().post(
        "/slack/weather",
        data=body,
        content_type="application/x-www-form-urlencoded",
        headers=slack_headers(body, "test-secret"),
    )

    assert response.status_code == 400
    assert "provide a city" in response.get_json()["text"]


def test_rejects_invalid_signature():
    app = create_app(weather_client=FakeWeatherClient(), signing_secret="test-secret")

    response = app.test_client().post(
        "/slack/weather",
        data={"text": "London"},
        headers={
            "X-Slack-Request-Timestamp": str(int(time.time())),
            "X-Slack-Signature": "v0=invalid",
        },
    )

    assert response.status_code == 401


def test_returns_not_found_message(monkeypatch):
    monkeypatch.setenv("FLASK_TESTING", "true")
    client = FakeWeatherClient(error=CityNotFoundError())
    app = create_app(weather_client=client)

    response = app.test_client().post("/slack/weather", data={"text": "Atlantis"})

    assert response.status_code == 200
    assert response.get_json() == {
        "response_type": "ephemeral",
        "text": "I could not find a city named Atlantis.",
    }
