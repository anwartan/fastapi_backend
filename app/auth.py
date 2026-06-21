from datetime import datetime, time, timedelta, timezone
from typing import Optional
from fastapi import Depends, HTTPException, status, BackgroundTasks
from jose import JWTError
import jwt
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from app.model.kafe.member import Member
from sqlmodel import select
from app.database import SessionDBKafeLogin, get_session_kafe_login

SECRET_KEY = "your_secret_key_here"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 36500
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expired=datetime.now(timezone.utc)+(expires_delta or timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS))
    to_encode.update({"exp": expired})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
def get_current_user(
    session: SessionDBKafeLogin,
    token: str = Depends(oauth2_scheme),
)-> Member:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception

    user_statement = select(Member).where(Member.Username == username)
    user = session.exec(user_statement).first()

    if user is None:
        raise credentials_exception

    # CEK STATUS AKUN
    if user.Active == 0:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account disabled",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user