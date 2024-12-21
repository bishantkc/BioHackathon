from pydantic import BaseModel, model_validator, validator
from datetime import date, datetime
from typing import Optional, List
from fastapi import HTTPException
from uuid import UUID


# Pydantic models
class DataModel(BaseModel):
    class ConfigDict:
        from_attributes = True


class Token(DataModel):
    access_token: str
    token_type: str


class TokenData(DataModel):
    email: str | None = None


class UserBodyRequest(DataModel):
    email: str
    username: str
    full_name: str
    role_id: UUID | None = None


class UserBodyResponse(UserBodyRequest):
    id: UUID | None = None
    user_photo: str | None = None


class RoleSchema(DataModel):
    role_name: str
    permissions: Optional[List] = None


class UserInformation(UserBodyResponse):
    role: Optional[RoleSchema] = None


class AppointmentCreate(DataModel):
    user_id: UUID
    doctor_id: UUID
    appointment_date: datetime
    reason: str


class ReportCreate(DataModel):
    user_id: UUID
    report_name: str
    report_display_name: str


class ReportResponse(ReportCreate):
    id: UUID
    user: UserInformation
