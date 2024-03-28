from utils.database.general import _session as session_
from datetime import datetime, timedelta
from datetime import UTC
from typing import Annotated
from starlette import status
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError


def get_db():
    db = session_()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]

form_data = Annotated[OAuth2PasswordRequestForm, Depends()]

# Generate JWT token access

SECRET_KEY = "b9c372cec5dad2643bdaeaa0bec188070fa450a5d145ad0218a9514158072223"
ALGORITHM = "HS256"


def create_access_token(
    username: str,
    user_id: int,
    role: str,
    expire_delta: timedelta = timedelta(minutes=60),
):
    encode = {"sub": username, "id": user_id, "role": role}
    expire = datetime.now(UTC) + expire_delta
    encode.update({"exp": expire})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)


oauth2_bearer = OAuth2PasswordBearer(tokenUrl="auth/token")


async def get_current_user_from_cookie(request: Request):
    try:
        from routers.auth import logout

        if (token := request.cookies.get("access_token")) is None:
            return None
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("id")
        role: str = payload.get("role")
        if username is None or user_id is None:
            await logout(request)
        return {"username": username, "id": user_id, "user_role": role}
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate user.",
        ) from exc


async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("id")
        role: str = payload.get("role")
        if username is None or user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate user.",
            )
        return {"username": username, "id": user_id, "user_role": role}
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate user.",
        ) from exc


user_dependency = Annotated[dict, Depends(get_current_user)]
