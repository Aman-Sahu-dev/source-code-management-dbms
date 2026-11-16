"""HTTP client wrapper using httpx."""

import httpx
import typer


def _client(base_url: str, token: str | None = None) -> httpx.Client:
    headers = {}
    if token:
        headers["X-Token"] = token
    return httpx.Client(base_url=base_url, headers=headers, timeout=10.0)


def request(method: str, base_url: str, path: str, token: str | None = None, **kwargs) -> dict:
    try:
        with _client(base_url, token) as client:
            resp = getattr(client, method)(path, **kwargs)
        if resp.status_code == 204:
            return {}
        data = resp.json()
        if resp.is_error:
            detail = data.get("detail", resp.text) if isinstance(data, dict) else resp.text
            typer.echo(f"❌ Error {resp.status_code}: {detail}", err=True)
            raise typer.Exit(1)
        return data
    except httpx.ConnectError:
        typer.echo("❌ Could not connect to server. Is it running?", err=True)
        raise typer.Exit(1)


def get(base_url: str, path: str, token: str | None = None, **kwargs) -> dict:
    return request("get", base_url, path, token, **kwargs)


def post(base_url: str, path: str, token: str | None = None, **kwargs) -> dict:
    return request("post", base_url, path, token, **kwargs)


def patch(base_url: str, path: str, token: str | None = None, **kwargs) -> dict:
    return request("patch", base_url, path, token, **kwargs)


def delete(base_url: str, path: str, token: str | None = None, **kwargs) -> dict:
    return request("delete", base_url, path, token, **kwargs)
