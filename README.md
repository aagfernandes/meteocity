# MeteoCity

A Flask Slack slash command that returns the current temperature for a city using OpenWeather.

## Requirements

- Python 3.14 or newer
- A Slack app with the `/jumo_weather` slash command
- An OpenWeather API key
- ngrok

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
chmod 600 .env
```

Set the following values in `.env`:

```text
OPENWEATHER_API_KEY=your-openweather-api-key
SLACK_SIGNING_SECRET=your-slack-signing-secret
```

Never commit `.env` or share its contents.

## Run tests

```bash
source .venv/bin/activate
python -m pytest
```

## Run locally

```bash
source .venv/bin/activate
python app.py
```

The health endpoint is available at:

```text
http://127.0.0.1:8000/health
```

## Configure ngrok and Slack

In another terminal, expose the local application:

```bash
ngrok http 8000
```

Set the Slack slash command Request URL to:

```text
https://YOUR-NGROK-DOMAIN.ngrok-free.dev/slack/weather
```

Then test the command in Slack:

```text
/jumo_weather London
```

Socket Mode is not required. The application returns the slash-command response directly and does not use a Bot User OAuth token.

## Development validation

Run the complete local validation suite with:

```bash
source .venv/bin/activate
python -m pytest
ruff check .
ruff format --check .
```

Install the pre-commit hook once per clone:

```bash
pre-commit install
pre-commit run --all-files
```

GitHub Actions runs the same checks on pushes to `main` and `dev`, and on pull requests targeting `main`.

## Validation coverage

The tests cover successful weather responses, unknown cities, invalid API keys,
timeouts, malformed weather responses, missing city input, and invalid or stale
Slack signatures. Slack city input is limited to 40 characters before an
OpenWeather request is made.

For manual Slack testing, keep both processes running:

```text
Terminal 1: python app.py
Terminal 2: ngrok http 8000
```

Use the active ngrok URL in the Slack Request URL, then run:

```text
/jumo_weather London
```

The ngrok process must remain active while Slack sends the request.

## Security

- Keep `.env` local and ignored by Git.
- Use `.env.example` as the safe configuration template.
- Never put API keys or signing secrets in source code.
- Rotate credentials if they are exposed.