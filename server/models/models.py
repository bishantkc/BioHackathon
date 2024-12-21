from sqlalchemy import (
    JSON,
    Column,
    Integer,
    String,
    Sequence,
    Boolean,
    DateTime,
    ForeignKey,
    Enum,
    ARRAY,
    Text,
    Float,
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(
        UUID(as_uuid=False),
        primary_key=True,
        default=uuid.uuid4,
    )
    username = Column(String)
    email = Column(String(100), unique=True)
    full_name = Column(String(100))
    hashed_password = Column(String)
    disabled = Column(Boolean, default=False)
    role_id = Column(UUID(as_uuid=False), ForeignKey("role.id"))
    user_photo = Column(String)

    role = relationship("Role", back_populates="user")
    appointment = relationship(
        "Appointment",
        back_populates="user",
        foreign_keys="[Appointment.user_id]",
    )
    doctor_availability = relationship(
        "DoctorAvailability",
        back_populates="user",
        foreign_keys="[DoctorAvailability.doctor_id]",
    )
    reports = relationship(
        "Reports",
        back_populates="user",
        foreign_keys="[Reports.user_id]",
    )


class Role(Base):
    __tablename__ = "role"
    id = Column(
        UUID(as_uuid=False),
        primary_key=True,
        default=uuid.uuid4,
    )
    role_name = Column(String)
    permissions = Column(ARRAY(String))

    # relationship
    user = relationship("User", back_populates="role")


class Appointment(Base):
    __tablename__ = "appointments"
    id = Column(
        UUID(as_uuid=False),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"))
    doctor_id = Column(UUID(as_uuid=False), ForeignKey("users.id"))
    appointment_date = Column(DateTime)
    reason = Column(String)

    user = relationship(
        "User",
        back_populates="appointment",
        foreign_keys="[Appointment.user_id]",
    )


class Reports(Base):
    __tablename__ = "reports"
    id = Column(
        UUID(as_uuid=False),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"))
    report_name = Column(String)
    report_display_name = Column(String)

    user = relationship(
        "User", back_populates="reports", foreign_keys="[Reports.user_id]"
    )


class DoctorAvailability(Base):
    __tablename__ = "doctor_availability"
    id = Column(UUID(as_uuid=False), primary_key=True, default=uuid.uuid4)
    doctor_id = Column(UUID(as_uuid=False), ForeignKey("users.id"))
    availability = Column(JSON)

    user = relationship(
        "User",
        back_populates="doctor_availability",
        foreign_keys="[DoctorAvailability.doctor_id]",
    )
