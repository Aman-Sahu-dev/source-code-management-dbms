"""Issue tracking."""

from fastapi import APIRouter, Depends, Header, HTTPException
from psycopg import AsyncConnection

from server.auth import validate_token
from server.database import get_db
from server.models import IssueCreate, IssueOut

router = APIRouter(tags=["issues"])


def _get_current_user(x_token: str | None = Header(default=None)):
    if not x_token:
        raise HTTPException(status_code=401, detail="Missing X-Token header")
    username = validate_token(x_token)
    if not username:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return username


async def _get_user_id(username: str, db: AsyncConnection) -> int:
    row = await db.execute("SELECT id FROM users WHERE username = %s", (username,))
    user = await row.fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user[0]


async def _check_access(repo_id: int, user_id: int, db: AsyncConnection):
    row = await db.execute(
        "SELECT role FROM collaborators WHERE repo_id = %s AND user_id = %s",
        (repo_id, user_id),
    )
    if not await row.fetchone():
        raise HTTPException(status_code=403, detail="Access denied")


@router.get("/repos/{repo_id}/issues", response_model=list[IssueOut])
async def list_issues(
    repo_id: int,
    username: str = Depends(_get_current_user),
    db: AsyncConnection = Depends(get_db),
):
    user_id = await _get_user_id(username, db)
    await _check_access(repo_id, user_id, db)
    rows = await db.execute(
        """
        SELECT i.id, i.repo_id, i.author_id, u.username, i.title, i.body, i.status, i.created_at
        FROM issues i JOIN users u ON i.author_id = u.id
        WHERE i.repo_id = %s ORDER BY i.created_at DESC
        """,
        (repo_id,),
    )
    return [
        IssueOut(id=r[0], repo_id=r[1], author_id=r[2], author_username=r[3],
                 title=r[4], body=r[5], status=r[6], created_at=r[7])
        for r in await rows.fetchall()
    ]


@router.post("/repos/{repo_id}/issues", response_model=IssueOut, status_code=201)
async def create_issue(
    repo_id: int,
    body: IssueCreate,
    username: str = Depends(_get_current_user),
    db: AsyncConnection = Depends(get_db),
):
    user_id = await _get_user_id(username, db)
    await _check_access(repo_id, user_id, db)
    try:
        row = await db.execute(
            "INSERT INTO issues (repo_id, author_id, title, body) VALUES (%s, %s, %s, %s) RETURNING id, status, created_at",
            (repo_id, user_id, body.title, body.body),
        )
        i = await row.fetchone()
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    return IssueOut(id=i[0], repo_id=repo_id, author_id=user_id, author_username=username,
                    title=body.title, body=body.body, status=i[1], created_at=i[2])


@router.patch("/repos/{repo_id}/issues/{issue_id}", response_model=IssueOut)
async def close_issue(
    repo_id: int,
    issue_id: int,
    username: str = Depends(_get_current_user),
    db: AsyncConnection = Depends(get_db),
):
    user_id = await _get_user_id(username, db)
    await _check_access(repo_id, user_id, db)
    # Use stored procedure
    try:
        await db.execute("CALL close_issue(%s)", (issue_id,))
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    row = await db.execute(
        """
        SELECT i.id, i.repo_id, i.author_id, u.username, i.title, i.body, i.status, i.created_at
        FROM issues i JOIN users u ON i.author_id = u.id
        WHERE i.id = %s
        """,
        (issue_id,),
    )
    r = await row.fetchone()
    return IssueOut(id=r[0], repo_id=r[1], author_id=r[2], author_username=r[3],
                    title=r[4], body=r[5], status=r[6], created_at=r[7])
