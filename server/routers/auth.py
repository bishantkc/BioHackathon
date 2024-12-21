from datetime import timedelta
from typing import Annotated
import uuid
from fastapi import (
    HTTPException,
    Depends,
    status,
    APIRouter,
    Body,
    UploadFile,
    File,
    Form,
)
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

import os
from dotenv import load_dotenv

from models.models import (
    DoctorAvailability,
    User,
    Role,
)
from schema.schema import (
    UserBodyResponse,
    UserBodyRequest,
    UserInformation,
    UserBodyResponse,
    UserInformation,
)

from components.dependencies import (
    get_db,
    hash_password,
    create_access_token,
    authenticate_user,
    get_current_active_user,
    validate_img_upload,
    check_permissions,
)

from sqlalchemy import func
from uuid import UUID
from fastapi_pagination import paginate
from fastapi_pagination.links import Page

# Load environment variables from .env file
load_dotenv()

# Constants
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))
REFRESH_TOKEN_EXPIRE_MINUTES = int(os.getenv("REFRESH_TOKEN_EXPIRE_MINUTES"))

# APIRouter Instance
router = APIRouter()


@router.post("/add-new-user")
@check_permissions(["admin"])
async def register(
    current_user: Annotated[User, Depends(get_current_active_user)],
    user: UserBodyRequest = Body(...),
    db: Session = Depends(get_db),
):
    user_create = UserBodyResponse(**user.model_dump())
    new_user = User(**user_create.model_dump())

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Internal Server Error: {e}"
        )

    if "doctor" in new_user.role.permissions:
        default_availability = {
            "Monday": {"start_time": "09:00", "end_time": "17:00"},
            "Tuesday": {"start_time": "09:00", "end_time": "17:00"},
            "Wednesday": {"start_time": "09:00", "end_time": "17:00"},
            "Thursday": {"start_time": "09:00", "end_time": "17:00"},
            "Friday": {"start_time": "09:00", "end_time": "17:00"},
            "Saturday": None,
            "Sunday": {"start_time": "09:00", "end_time": "14:00"},
        }

        doctor_availability = DoctorAvailability(
            doctor_id=new_user.id,
            availability=default_availability,
        )

        try:
            db.add(doctor_availability)
            db.commit()
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=500, detail=f"Internal Server Error: {e}"
            )

    return {"message": "User created successfully"}


@router.post("/signup")
async def signup(
    email: str = Form(...),
    password: str = Form(...),
    profileImage: UploadFile = File(...),
    db: Session = Depends(get_db),
):

    if not validate_img_upload(profileImage):
        raise HTTPException(
            status_code=400,
            detail=[
                {"profileImage": "Invalid image format.Upload jpg/png/jpeg."}
            ],
        )

    if not password.strip():
        raise HTTPException(
            status_code=400, detail=[{"password": "Password cannot be empty"}]
        )

    check_user = db.query(User).filter(User.email == email).first()

    if not check_user:
        raise HTTPException(
            status_code=404, detail=[{"email": "Email Not Found."}]
        )

    elif check_user.hashed_password:
        raise HTTPException(
            status_code=400, detail=[{"email": "Email already registered."}]
        )

    hashed_password = hash_password(password)

    check_user.hashed_password = hashed_password

    MAX_FILE_SIZE = 1 * 1024 * 1024  # 1 MB

    # Check the file size directly
    file_size = len(profileImage.file.read())
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=[{"profileImage": "Uploaded file is too large."}],
        )

    # Handle photo upload
    name, ext = os.path.splitext(profileImage.filename)

    file_path = os.getenv("PHOTO_PATH")

    photo_uuid = uuid.uuid4()

    full_file_name = f"{photo_uuid}{ext}"
    full_file_path = f"{file_path}/{full_file_name}"

    try:
        profileImage.file.seek(0)
        with open(full_file_path, "wb") as file_object:
            file_object.write(profileImage.file.read())

            check_user.user_photo = full_file_name

            db.commit()
            db.refresh(check_user)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Cannot register User.{e}"
        )

    return {"message": "Signed Up Successfully."}


@router.post("/login")
def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db),
):
    user = authenticate_user(form_data.username, form_data.password, db)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=[
                {"email": "Incorrect email or password"},
                {"password": "Incorrect email or password"},
            ],
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    refresh_token = create_access_token(
        data={"sub": user.email}, expires_delta=refresh_token_expires
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "user_photo": user.user_photo,
            "role_permissions": user.role.permissions,
        },
    }


# Endpoint to reset password by sending new password
@router.post("/reset-password")
async def reset_password(
    current_user: Annotated[User, Depends(get_current_active_user)],
    user_id: UUID,
    password: str,
    db: Session = Depends(get_db),
):
    current_user_role_id = current_user.role_id
    current_user_role = (
        db.query(Role).filter(Role.id == current_user_role_id).first()
    )
    if not password.strip():
        raise HTTPException(status_code=400, detail="Password cannot be empty")

    if not current_user_role:
        raise HTTPException(
            status_code=500,
            detail="You don't have permission to update password.",
        )

    user = db.query(User).filter(User.id == user_id).first()
    hashed_password = hash_password(password)
    user.hashed_password = hashed_password
    db.commit()
    db.refresh(user)
    return {"Message": "Password reset successful"}


@router.get("/user")
async def get_user_details(
    current_user: Annotated[User, Depends(get_current_active_user)]
) -> UserInformation:
    return current_user


@router.get("/user-info")
async def get_selected_user_info(
    user_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Session = Depends(get_db),
) -> UserInformation:
    current_user_role_id = current_user.role_id
    current_user_role = (
        db.query(Role).filter(Role.id == current_user_role_id).first()
    )

    if not current_user_role:
        raise HTTPException(status_code=500, detail="User role not found")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=400, detail="User role not found")

    return user


@router.get("/show_all_users")
async def show_all_users(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Session = Depends(get_db),
) -> Page[UserInformation]:
    current_user_role_id = current_user.role_id
    current_user_role = (
        db.query(Role).filter(Role.id == current_user_role_id).first()
    )

    if not current_user_role:
        raise HTTPException(status_code=500, detail="User role not found")

    users = db.query(User).order_by(User.full_name).all()
    return paginate(users)


@router.get("/search-user")
async def search_user(
    name: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Session = Depends(get_db),
) -> list[UserInformation]:
    current_role_id = current_user.role_id
    if not current_role_id:
        raise HTTPException(
            status_code=403,
            detail=f"You don't have permissions to add roles.",
        )

    lower_name = name.lower()
    users = (
        db.query(User)
        .filter(func.lower(User.full_name).contains(lower_name))
        .all()
    )

    return users


@router.get("/role-of-user")
async def get_role_of_user(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Session = Depends(get_db),
):
    current_user_role_id = current_user.role_id
    current_user_role = (
        db.query(Role).filter(Role.id == current_user_role_id).first()
    )

    if not current_user_role:
        raise HTTPException(status_code=500, detail="User role not found")

    role = current_user.role

    return role
