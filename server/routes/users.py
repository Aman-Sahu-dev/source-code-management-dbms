"""User registration, login, logout."""

from fastapi import APIRouter, Depends, Header, HTTPException
from psycopg import AsyncConnection

from server.auth import create_token, hash_password, revoke_token, validate_token, verify_password
from server.database import get_db
from server.models import TokenOut, UserLogin, UserOut, UserRegister

router = APIRouter(prefix="/users", tags=["users"])


def _get_current_user(x_token: str | None = Header(default=None)):
    if not x_token:
        raise HTTPException(status_code=401, detail="Missing X-Token header")
    username = validate_token(x_token)
    if not username:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return username


@router.post("/register", response_model=UserOut, status_code=201)
async def register(body: UserRegister, db: AsyncConnection = Depends(get_db)):
    pw_hash = hash_password(body.password)
    try:
        row = await db.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s) RETURNING id, username, email, created_at",
            (body.username, body.email, pw_hash),
        )
        user = await row.fetchone()
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    return UserOut(id=user[0], username=user[1], email=user[2], created_at=user[3])


@router.post("/login", response_model=TokenOut)
async def login(body: UserLogin, db: AsyncConnection = Depends(get_db)):
    row = await db.execute(
        "SELECT id, password_hash FROM users WHERE username = %s", (body.username,)
    )
    user = await row.fetchone()
    if not user or not verify_password(body.password, user[1]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token(body.username)
    return TokenOut(token=token, username=body.username)


@router.post("/logout")
async def logout(username: str = Depends(_get_current_user), x_token: str | None = Header(default=None)):
    if x_token:
        revoke_token(x_token)
    return {"message": "Logged out"}


@router.get("/me", response_model=UserOut)
async def me(username: str = Depends(_get_current_user), db: AsyncConnection = Depends(get_db)):
    row = await db.execute(
        "SELECT id, username, email, created_at FROM users WHERE username = %s", (username,)
    )
    user = await row.fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserOut(id=user[0], username=user[1], email=user[2], created_at=user[3])
