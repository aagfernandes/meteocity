from app import create_app


def test_app_reads_environment_configuration(monkeypatch):
    monkeypatch.setenv("OPENWEATHER_API_KEY", "test-key")
    monkeypatch.setenv("SLACK_SIGNING_SECRET", "test-secret")

    app = create_app()

    assert app.config["OPENWEATHER_API_KEY"] == "test-key"
    assert app.config["SLACK_SIGNING_SECRET"] == "test-secret"