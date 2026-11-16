"""Client configuration — stores server URL and auth token."""

import json
from pathlib import Path

CONFIG_DIR = Path.home() / ".dbms-scm"
CONFIG_FILE = CONFIG_DIR / "config.json"


def _load() -> dict:
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return {}


def _save(data: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(data, indent=2))


def get_server_url() -> str | None:
    return _load().get("server_url")


def set_server_url(url: str) -> None:
    data = _load()
    data["server_url"] = url.rstrip("/")
    _save(data)


def get_token() -> str | None:
    return _load().get("token")


def save_token(token: str, username: str) -> None:
    data = _load()
    data["token"] = token
    data["username"] = username
    _save(data)


def clear_token() -> None:
    data = _load()
    data.pop("token", None)
    data.pop("username", None)
    _save(data)


def get_username() -> str | None:
    return _load().get("username")


def require_server() -> str:
    url = get_server_url()
    if not url:
        import typer
        typer.echo("❌ No server configured. Run: scm config set-server <url>", err=True)
        raise typer.Exit(1)
    return url


def require_login() -> tuple[str, str]:
    """Returns (server_url, token) or exits."""
    url = require_server()
    token = get_token()
    if not token:
        import typer
        typer.echo("❌ Not logged in. Run: scm auth login", err=True)
        raise typer.Exit(1)
    return url, token
