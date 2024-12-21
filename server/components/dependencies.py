from datetime import timedelta
import datetime
from typing import Annotated
from fastapi import status
from fastapi import HTTPException, Depends, UploadFile
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import create_engine
from passlib.context import CryptContext
from functools import wraps

import os
from dotenv import load_dotenv

from models.models import (
    User,
)
from schema import schema as validation_schema

load_dotenv()

# Constants
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
DATABASE_URL = os.getenv("POSTGRES_URL")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))
REFRESH_TOKEN_EXPIRE_MINUTES = int(os.getenv("REFRESH_TOKEN_EXPIRE_MINUTES"))


# SQLAlchemy setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Password hashing setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 setup
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


# Dependency to load database
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Hashing passwords
def hash_password(password):
    return pwd_context.hash(password)


# Verify passwords
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


# Get user from the database by email
def get_user(email: str, db: Session = Depends(get_db)):
    return db.query(User).filter(User.email == email).first()


# Authenticate user
def authenticate_user(
    email: str, password: str, db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == email).first()

    if user and verify_password(password, user.hashed_password):
        return user
    else:
        return None


# Create access token
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.now() + expires_delta
    else:
        expire = datetime.datetime.now() + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# Validate email to enter only certain mail
def validate_email(email: str):
    allowed_domains = ["brocoders.com"]
    username, domain = email.split("@", 1) if "@" in email else (None, None)
    if username and domain in allowed_domains:
        return True
    else:
        return False


def validate_img_upload(file: UploadFile):
    allowed_format = ["jpg", "jpeg", "png"]
    filename = file.filename
    if filename.split(".")[-1].lower() in allowed_format:
        return True
    else:
        return False


def validate_file_upload(file: UploadFile):
    allowed_format = ["pdf"]
    filename = file.filename
    if filename.split(".")[-1].lower() in allowed_format:
        return True
    else:
        return False


# Get current user from the token


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Session = Depends(get_db),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = validation_schema.TokenData(email=email)
    except JWTError:
        raise credentials_exception

    user = get_user(email=token_data.email, db=db)
    if user is None:
        raise credentials_exception

    return user


# Get current active user
async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
):   
    return current_user


def check_permissions(required_roles: list[str] = None):
    """
    Decorator to check if the current user has the necessary permissions.

    Args:
        required_roles (List[str], optional): A list of role names required to access the endpoint. Defaults to None.

    Raises:
        HTTPException: Raises a 403 error if the user does not have the necessary permissions.

    Returns:
        The decorated function with permission checks.
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user")
            if (
                not (current_user.role_id or current_user.role)
            ):
                raise HTTPException(
                    status_code=403,
                    detail=f"You do not have the required permissions.",
                )

            if required_roles and not any(
                role in required_roles
                for role in current_user.role.permissions
            ):
                raise HTTPException(
                    status_code=403,
                    detail="You do not have the required permissions to access this resource.",
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


