"""Command-line interface for the Repository Management System."""

from datetime import datetime
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich import print as rprint

from client import api, config

app = typer.Typer(help="Repository Management System CLI", no_args_is_help=True)
console = Console()

# ── Sub-apps ──────────────────────────────────────────────────────────────────
cfg_app = typer.Typer(help="Client configuration", no_args_is_help=True)
auth_app = typer.Typer(help="Authentication", no_args_is_help=True)
repo_app = typer.Typer(help="Repository management", no_args_is_help=True)
branch_app = typer.Typer(help="Branch management", no_args_is_help=True)
commit_app = typer.Typer(help="Commit management", no_args_is_help=True)
issue_app = typer.Typer(help="Issue tracking", no_args_is_help=True)

app.add_typer(cfg_app, name="config")
app.add_typer(auth_app, name="auth")
app.add_typer(repo_app, name="repo")
app.add_typer(branch_app, name="branch")
app.add_typer(commit_app, name="commit")
app.add_typer(issue_app, name="issue")


# ── Config ────────────────────────────────────────────────────────────────────

@cfg_app.command("set-server")
def config_set_server(url: str = typer.Argument(..., help="Server base URL, e.g. http://192.168.1.10:8000")):
    """Set the server URL."""
    config.set_server_url(url)
    typer.echo(f"✅ Server set to: {url}")


@cfg_app.command("show")
def config_show():
    """Show current configuration."""
    url = config.get_server_url()
    username = config.get_username()
    typer.echo(f"Server URL : {url or '(not set)'}")
    typer.echo(f"Logged in  : {username or '(not logged in)'}")


# ── Auth ──────────────────────────────────────────────────────────────────────

@auth_app.command("register")
def auth_register(
    username: str = typer.Option(..., prompt=True),
    email: str = typer.Option(..., prompt=True),
    password: str = typer.Option(..., prompt=True, hide_input=True, confirmation_prompt=True),
):
    """Register a new account."""
    url = config.require_server()
    data = api.post(url, "/users/register", json={"username": username, "email": email, "password": password})
    typer.echo(f"✅ Registered as {data['username']} (id={data['id']})")


@auth_app.command("login")
def auth_login(
    username: str = typer.Option(..., prompt=True),
    password: str = typer.Option(..., prompt=True, hide_input=True),
):
    """Login and save session token."""
    url = config.require_server()
    data = api.post(url, "/users/login", json={"username": username, "password": password})
    config.save_token(data["token"], data["username"])
    typer.echo(f"✅ Logged in as {data['username']}")


@auth_app.command("logout")
def auth_logout():
    """Logout and clear session."""
    url, token = config.require_login()
    api.post(url, "/users/logout", token=token)
    config.clear_token()
    typer.echo("✅ Logged out")


@auth_app.command("whoami")
def auth_whoami():
    """Show currently logged-in user."""
    url, token = config.require_login()
    data = api.get(url, "/users/me", token=token)
    typer.echo(f"Logged in as: {data['username']} <{data['email']}>")


# ── Repos ─────────────────────────────────────────────────────────────────────

@repo_app.command("list")
def repo_list():
    """List repositories you have access to."""
    url, token = config.require_login()
    repos = api.get(url, "/repos", token=token)
    if not repos:
        typer.echo("No repositories found.")
        return
    table = Table(title="Repositories")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="bold")
    table.add_column("Owner")
    table.add_column("Private")
    table.add_column("Commits", justify="right")
    table.add_column("Open Issues", justify="right")
    for r in repos:
        table.add_row(str(r["id"]), r["name"], r["owner_username"],
                      "🔒" if r["is_private"] else "🌐",
                      str(r["commit_count"]), str(r["open_issue_count"]))
    console.print(table)


@repo_app.command("create")
def repo_create(
    name: str = typer.Argument(..., help="Repository name"),
    description: Optional[str] = typer.Option(None, "--desc", "-d"),
    private: bool = typer.Option(False, "--private", "-p"),
):
    """Create a new repository."""
    url, token = config.require_login()
    data = api.post(url, "/repos", token=token,
                    json={"name": name, "description": description, "is_private": private})
    typer.echo(f"✅ Created repo '{data['name']}' (id={data['id']})")


@repo_app.command("view")
def repo_view(repo_id: int = typer.Argument(..., help="Repository ID")):
    """View repository details."""
    url, token = config.require_login()
    r = api.get(url, f"/repos/{repo_id}", token=token)
    rprint(f"[bold]Name:[/bold]        {r['name']}")
    rprint(f"[bold]ID:[/bold]          {r['id']}")
    rprint(f"[bold]Owner:[/bold]       {r['owner_username']}")
    rprint(f"[bold]Description:[/bold] {r.get('description') or '—'}")
    rprint(f"[bold]Private:[/bold]     {'Yes' if r['is_private'] else 'No'}")
    rprint(f"[bold]Commits:[/bold]     {r['commit_count']}")
    rprint(f"[bold]Open Issues:[/bold] {r['open_issue_count']}")
    rprint(f"[bold]Created:[/bold]     {r['created_at']}")


@repo_app.command("delete")
def repo_delete(
    repo_id: int = typer.Argument(..., help="Repository ID"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
):
    """Delete a repository (owner only)."""
    if not yes:
        typer.confirm(f"Delete repository {repo_id}? This cannot be undone.", abort=True)
    url, token = config.require_login()
    api.delete(url, f"/repos/{repo_id}", token=token)
    typer.echo(f"✅ Repository {repo_id} deleted")


# ── Branches ──────────────────────────────────────────────────────────────────

@branch_app.command("list")
def branch_list(repo_id: int = typer.Argument(...)):
    """List branches in a repository."""
    url, token = config.require_login()
    branches = api.get(url, f"/repos/{repo_id}/branches", token=token)
    if not branches:
        typer.echo("No branches found.")
        return
    table = Table(title=f"Branches (repo {repo_id})")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="bold")
    table.add_column("Created At")
    for b in branches:
        table.add_row(str(b["id"]), b["name"], b["created_at"])
    console.print(table)


@branch_app.command("create")
def branch_create(
    repo_id: int = typer.Argument(...),
    name: str = typer.Argument(..., help="Branch name"),
):
    """Create a new branch."""
    url, token = config.require_login()
    data = api.post(url, f"/repos/{repo_id}/branches", token=token, json={"name": name})
    typer.echo(f"✅ Created branch '{data['name']}' (id={data['id']})")


# ── Commits ───────────────────────────────────────────────────────────────────

@commit_app.command("list")
def commit_list(
    repo_id: int = typer.Argument(...),
    branch_id: int = typer.Argument(...),
):
    """List commits on a branch."""
    url, token = config.require_login()
    commits = api.get(url, f"/repos/{repo_id}/branches/{branch_id}/commits", token=token)
    if not commits:
        typer.echo("No commits found.")
        return
    table = Table(title=f"Commits (branch {branch_id})")
    table.add_column("ID", style="cyan")
    table.add_column("Author")
    table.add_column("Message")
    table.add_column("Date")
    for c in commits:
        table.add_row(str(c["id"]), c["author_username"], c["message"][:60], c["committed_at"])
    console.print(table)


@commit_app.command("add")
def commit_add(
    repo_id: int = typer.Argument(...),
    branch_id: int = typer.Argument(...),
    message: str = typer.Option(..., "--message", "-m", prompt=True),
):
    """Record a commit on a branch."""
    url, token = config.require_login()
    data = api.post(url, f"/repos/{repo_id}/branches/{branch_id}/commits",
                    token=token, json={"message": message})
    typer.echo(f"✅ Commit recorded (id={data['id']}): {message}")


# ── Issues ────────────────────────────────────────────────────────────────────

@issue_app.command("list")
def issue_list(repo_id: int = typer.Argument(...)):
    """List issues for a repository."""
    url, token = config.require_login()
    issues = api.get(url, f"/repos/{repo_id}/issues", token=token)
    if not issues:
        typer.echo("No issues found.")
        return
    table = Table(title=f"Issues (repo {repo_id})")
    table.add_column("ID", style="cyan")
    table.add_column("Status")
    table.add_column("Title")
    table.add_column("Author")
    table.add_column("Created At")
    for i in issues:
        status_str = "[green]open[/green]" if i["status"] == "open" else "[red]closed[/red]"
        table.add_row(str(i["id"]), status_str, i["title"], i["author_username"], i["created_at"])
    console.print(table)


@issue_app.command("create")
def issue_create(
    repo_id: int = typer.Argument(...),
    title: str = typer.Option(..., "--title", "-t", prompt=True),
    body: Optional[str] = typer.Option(None, "--body", "-b"),
):
    """Create a new issue."""
    url, token = config.require_login()
    data = api.post(url, f"/repos/{repo_id}/issues", token=token,
                    json={"title": title, "body": body})
    typer.echo(f"✅ Issue #{data['id']} created: {title}")


@issue_app.command("close")
def issue_close(
    repo_id: int = typer.Argument(...),
    issue_id: int = typer.Argument(...),
):
    """Close an issue."""
    url, token = config.require_login()
    data = api.patch(url, f"/repos/{repo_id}/issues/{issue_id}", token=token)
    typer.echo(f"✅ Issue #{data['id']} closed")


if __name__ == "__main__":
    app()
