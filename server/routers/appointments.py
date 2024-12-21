from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from models.models import (
    User,
    Appointment,
    DoctorAvailability,
)
from sqlalchemy.orm import Session
from sqlalchemy.sql import and_
from components.dependencies import (
    get_db,
    get_current_active_user,
)
from schema.schema import AppointmentCreate

# APIRouter Instance
router = APIRouter()


@router.post("/create-appointment")
async def create_appointment(
    appointment_data: AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    # Map the weekday index to the day name
    weekday_names = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]
    appointment_day = weekday_names[
        appointment_data.appointment_date.weekday()
    ]

    # Get doctor availability for the specified day
    doctor_availability = (
        db.query(DoctorAvailability)
        .filter(DoctorAvailability.doctor_id == appointment_data.doctor_id)
        .first()
    )

    if not doctor_availability:
        raise HTTPException(
            status_code=400,
            detail="Doctor availability data not found",
        )

    # Check if doctor is available on the appointment day
    availability_for_day = doctor_availability.availability.get(
        appointment_day
    )

    if not availability_for_day:
        raise HTTPException(
            status_code=400,
            detail="Doctor is not available on the selected day",
        )

    # Check if the appointment time falls within the available time range
    from datetime import time

    appointment_time = appointment_data.appointment_date.time()
    start_time = time.fromisoformat(availability_for_day["start_time"])
    end_time = time.fromisoformat(availability_for_day["end_time"])

    if not (start_time <= appointment_time <= end_time):
        raise HTTPException(
            status_code=400,
            detail="Doctor is not available at the selected time",
        )

    # Create appointment
    appointment = Appointment(**appointment_data.model_dump())
    try:
        db.add(appointment)
        db.commit()
        db.refresh(appointment)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500, detail="Failed to create appointment"
        )
    return {"message": "Appointment created successfully"}


@router.get("/get-user-all-appointments")
async def get_all_appointments(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    appointments = (
        db.query(Appointment).filter(Appointment.user_id == user_id).all()
    )
    return appointments


@router.get("/get-doctor-appointments")
async def get_doctor_appointments(
    doctor_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    appointments = (
        db.query(Appointment).filter(Appointment.doctor_id == doctor_id).all()
    )
    return appointments


@router.get("/check-doctor-availability")
async def check_doctor_availability(
    doctor_id: UUID,
    date: str,
    time: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    from datetime import datetime, time

    # Parse date and time
    try:
        appointment_date = datetime.strptime(date, "%Y-%m-%d")
        appointment_time = datetime.strptime(time, "%H:%M").time()
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid date or time format",
        )

    # Map the weekday index to the day name
    weekday_names = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]
    appointment_day = weekday_names[appointment_date.weekday()]

    # Get doctor availability
    doctor_availability = (
        db.query(DoctorAvailability)
        .filter(DoctorAvailability.doctor_id == doctor_id)
        .first()
    )

    if not doctor_availability:
        raise HTTPException(
            status_code=400,
            detail="Doctor availability data not found",
        )

    # Check if doctor is available on the appointment day
    availability_for_day = doctor_availability.availability.get(
        appointment_day
    )

    if not availability_for_day:
        return {"available": False}

    # Check if the appointment time is within the doctor's available time
    start_time = time.fromisoformat(availability_for_day["start_time"])
    end_time = time.fromisoformat(availability_for_day["end_time"])

    if start_time <= appointment_time <= end_time:
        return {"available": True}
    else:
        return {"available": False}


@router.delete("/cancel-appointment/{appointment_id}")
async def cancel_appointment(
    appointment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    appointment = (
        db.query(Appointment).filter(Appointment.id == appointment_id).first()
    )

    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    try:
        db.delete(appointment)
        db.commit()
    except Exception:
        raise HTTPException(
            status_code=500, detail="Failed to cancel appointment"
        )
    return {"message": "Appointment canceled successfully"}


@router.post("/update-doctor-availability")
async def update_doctor_availability(
    doctor_id: UUID,
    day_of_week: str,  # Day of the week (e.g., "Monday", "Tuesday")
    start_time: str,  # New start time (format: "HH:MM")
    end_time: str,  # New end time (format: "HH:MM")
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    # Validate if the doctor exists
    doctor_availability = (
        db.query(DoctorAvailability)
        .filter(DoctorAvailability.doctor_id == doctor_id)
        .first()
    )

    if not doctor_availability:
        raise HTTPException(
            status_code=404, detail="Doctor not found or availability not set"
        )

    # Check if the provided day is valid
    valid_days = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]
    if day_of_week not in valid_days:
        raise HTTPException(status_code=400, detail="Invalid day of the week")

    # Update the availability for the provided day
    doctor_availability.availability[day_of_week] = {
        "start_time": start_time,
        "end_time": end_time,
    }

    try:
        db.commit()  # Save the changes to the database
        db.refresh(doctor_availability)
    except Exception:
        db.rollback()  # Rollback if an error occurs
        raise HTTPException(
            status_code=500, detail="Failed to update doctor availability"
        )

    return {
        "message": f"Doctor availability for {day_of_week} updated successfully"
    }
