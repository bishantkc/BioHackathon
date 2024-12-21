import os
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from models.models import (
    Reports,
    User,
    Appointment,
    DoctorAvailability,
)
from sqlalchemy.orm import Session
from sqlalchemy.sql import and_
from components.dependencies import (
    check_permissions,
    get_db,
    get_current_active_user,
    validate_file_upload,
)
from schema.schema import AppointmentCreate, ReportCreate, ReportResponse
from dotenv import load_dotenv

load_dotenv()

# APIRouter Instance
router = APIRouter()


def filename_number(filename: str, name_check: str, ext: str) -> int:
    """
    Extracts a numeric identifier from a filename based on provided name_check and extension.

    Args:
        filename (str): The full filename including extension.
        name_check (str): User input file name to check for prefix removal.
        ext (str): The file extension to remove as suffix.

    Returns:
        int: The extracted numeric identifier if found or specific codes:
            - 0: If the filename is empty i.e file_name matches the name_check.
            - -1: If the filename doesn't match the expected format or an error occurs.
    """
    try:
        filename = filename.removesuffix(ext).removeprefix(name_check)
        if not filename:
            # filename: f"{name_check}{ext}"
            return 0
        # Example Correct:
        #   name_check: example_name
        #   filename: example_name(101).pdf
        return int(filename[1:-1]) if int(filename[1:-1]) else -1
    except Exception:
        # For files that are similar to provided names ignorable
        # Example Incorrect:
        #   name_check: example_name
        #   filename: example_name_123.jpg or
        #   filename: example_name_jpt.pdf
        return -1


async def available_filename(
    file_name: str, ext: str, db: Session = Depends(get_db)
) -> str:
    """
    Generates an available filename by appending a numeric index if a similar filename exists in the database.

    Args:
        file_name (str): The base filename to check other similar file names in database.
        ext (str): The file extension to append to the filename.
        db (Session, optional): SQLAlchemy database session. Defaults to Depends(get_db).

    Returns:
        str: A filename that is available and unique within the database.
    """
    new_file_name = f"{file_name}{ext}"
    existing_files = (
        db.query(Reports)
        .filter(Reports.report_display_name.like(f"%{file_name}%"))
        .all()
    )

    if existing_files:
        filtered_files = filter(
            lambda file: filename_number(
                filename=str(file.report_display_name),
                name_check=file_name,
                ext=ext,
            )
            >= 0,
            existing_files,
        )
        sorted_files = sorted(  # type: ignore
            filtered_files,
            key=lambda x: filename_number(
                filename=str(x.report_display_name),
                name_check=file_name,
                ext=ext,
            ),
        )
        for index, file_data in enumerate(sorted_files):
            file_numbering = filename_number(
                filename=file_data.report_display_name,
                name_check=file_name,
                ext=ext,
            )
            if file_numbering != index:
                new_file_name = (
                    f"{file_name}({index}){ext}"
                    if index
                    else f"{file_name}{ext}"
                )
                break
            new_file_name = f"{file_name}({index+1}){ext}"
    return new_file_name


@router.post("/upload-report")
@check_permissions(["admin"])
async def upload_report(
    user_id: UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Uploads a new file to the server.

    Args:
        file (UploadFile, optional): The file to be uploaded.
            Defaults to File(...).
        current_user (User, optional): The currently authenticated user.
            Defaults to Depends(get_current_active_user).
        db (Session, optional): The database session dependency.
            Defaults to Depends(get_db).

    Raises:
        HTTPException 403: If the current user does not have permission
            to upload file.
        HTTPException 400: If the file format is invalid(not PDF).
        HTTPException 500: If an error occurs during the renaming process.

    Returns:
        Files: The newly uploaded file's metadata.
    """
    if not validate_file_upload(file):
        raise HTTPException(
            status_code=400,
            detail="Invalid format.Please Upload in pdf format.",
        )

    file_path = os.getenv("FILE_PATH")
    file_id = uuid4()

    name, ext = os.path.splitext(file.filename)
    full_file_name = f"{file_id}{ext}"
    full_file_path = f"{file_path}/{full_file_name}"

    try:
        new_file_display_name = await available_filename(name, ext, db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error naming file: {e}")

    new_file_data = {
        "id": file_id,
        "report_name": full_file_name,
        "report_display_name": new_file_display_name,
        "user_id": user_id,
    }
    file_create = ReportCreate(**new_file_data)
    new_file = Reports(**file_create.model_dump())
    try:
        db.add(new_file)
        db.commit()
        db.refresh(new_file)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Error to upload file: {e}"
        )

    try:
        with open(full_file_path, "wb") as file_object:
            file_object.write(file.file.read())
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error while saving file: {e}"
        )

    return new_file


@router.get("/view-reports-of-user", response_model=ReportResponse)
async def view_reports_of_user(
    user_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    reports = db.query(Reports).filter(Reports.user_id == user_id).all()
    return reports


@router.delete("/delete-report/{report_id}")
@check_permissions(["admin"])
async def delete_report(
    report_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Deletes a report by its ID.

    Args:
        report_id (UUID): The ID of the report to be deleted.
        current_user (User, optional): The currently authenticated user.
            Defaults to Depends(get_current_active_user).
        db (Session, optional): The database session dependency.
            Defaults to Depends(get_db).

    Raises:
        HTTPException 404: If the report does not exist.
        HTTPException 500: If an error occurs during the deletion process.

    Returns:
        dict: A message indicating the success or failure of the deletion.
    """
    report = db.query(Reports).filter(Reports.id == report_id).first()

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    try:
        # Delete the file from the file system (assuming the file path is stored in `file_path`)
        file_path = os.getenv("FILE_PATH")
        full_file_path = os.path.join(file_path, report.report_name)
        if os.path.exists(full_file_path):
            os.remove(full_file_path)

        # Delete the record from the database
        db.delete(report)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Error deleting report: {e}"
        )

    return {"message": "Report deleted successfully"}
