from enum import Enum
from fastapi import APIRouter, Depends, Request, Body, HTTPException
from typing import Annotated
from sqlalchemy.orm import Session

from components.dependencies import (
    get_db,
    get_current_active_user,
    check_permissions,
)
from models.models import Role, User
from schema.schema import RoleSchema
from uuid import UUID


class RolePermissionsEnum(str, Enum):
    admin = "admin"
    doctor = "doctor"
    patient = "patient"


router = APIRouter()


@router.post("/add-roles")
@check_permissions([RolePermissionsEnum.admin.value])
async def add_roles(
    request: Request,
    role: RoleSchema = Body(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Add a new role with specified permissions to the system.

    Only users with `admin` role permission are allowed to access
    this endpoint, as enforced by the `@check_permissions` decorator.

    Args:
        request (Request): The HTTP request object.
        role (RoleSchema, optional): The role data to be added,
            including role name and permissions. Defaults to Body(...).
        current_user (User, optional): Currently authenticated user.
            Defaults to Depends(get_current_active_user).
        db (Session, optional): The database session dependency.
            Defaults to Depends(get_db).

    Raises:
        HTTPException 400: If any of the specified permissions are invalid.
        HTTPException 409: If a role with the given name already exists.
        HTTPException 500: If an error occurs while creating the role in the database.

    Returns:
        dict: A dictionary containing a success message and the created role data.
            - **message**: A string confirming the successful creation of the role.
            - **data**: An instance of the newly created role, including its attributes.
    """
    for permission in role.permissions:
        if permission not in RolePermissionsEnum._value2member_map_:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid role permissions: {permission}",
            )

    existing_role = (
        db.query(Role).filter(Role.role_name == role.role_name).first()
    )
    if existing_role:
        raise HTTPException(
            status_code=409, detail=f"Role {role.role_name} already exists."
        )

    new_role_data = {
        "role_name": role.role_name,
        "permissions": role.permissions,
    }
    role_create = RoleSchema(**new_role_data)
    new_role = Role(**role_create.model_dump())
    try:
        db.add(new_role)
        db.commit()
        db.refresh(new_role)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Error to create role: {e}"
        )
    return {
        "message": f"{role.role_name} role created successfully.",
        "data": new_role,
    }


# Assign role
@router.post("/assign-role")
@check_permissions([RolePermissionsEnum.admin.value])
async def assign_role(
    user_id: UUID,
    role_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Assign a specified role to specified user.

    Only users with `admin` role permission are allowed to access
    this endpoint, as enforced by the `@check_permissions` decorator.

    Args:
        user_id (UUID): The UUID of the user to whom the role
            will be assigned.
        role_id (UUID): The UUID of the role to be assigned
            to the user.
        current_user (User, optional): Currentlt authenticated user.
            Defaults to Depends(get_current_active_user).
        db (Session, optional): The database session dependency.
            Defaults to Depends(get_db).

    Raises:
        HTTPException:
            - **404 Not Found**:
                - Raised if the user with the given `user_id` is not found.
                - Raised if the role with the given `role_id` is not found.
            - **500 Internal Server Error**:
                - Raised if an error occurs while committing the role
                assignment to the database.

    Returns:
         dict: A dictionary containing a success message.
            - **message**: A string confirming the successful assignment
                of the role to the user.
    """
    user = db.query(User).filter(User.id == user_id).first()

    role = db.query(Role).filter(Role.id == role_id).first()

    if not user:
        raise HTTPException(status_code=404, detail=f"Error in finding user.")

    if not role:
        raise HTTPException(status_code=404, detail=f"Error in finding role.")

    user.role_id = role_id

    try:
        db.commit()
        db.refresh(user)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error to assign role: {e}"
        )

    return {
        "message": f"{role.role_name} role assigned to {user.username} successfully."
    }


# edit role function
@router.put("/edit-roles")
@check_permissions([RolePermissionsEnum.admin.value])
async def edit_roles(
    request: Request,
    roleId: UUID,
    role: RoleSchema = Body(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Edit an existing role's name and permissions.

    Only users with `admin` role permission are allowed to access
    this endpoint, as enforced by the `@check_permissions` decorator.

    Args:
        request (Request): The HTTP request object.
        roleId (UUID): The UUID of the role to be edited.
        role (RoleSchema, optional): The new role data including
            the role name and permissions. Defaults to Body(...).
        current_user (User, optional): Currently authenticated user.
            Defaults to Depends(get_current_active_user).
        db (Session, optional): The database session dependency.
            Defaults to Depends(get_db).

    Raises:
        HTTPException:
            - **404 Not Found**:
                - Raised if the role with the given `roleId` does not exist.
            - **500 Internal Server Error**:
                - Raised if an error occurs while updating the
                role in the database.

    Returns:
        dict: A dictionary containing a success message and the updated role data.
            - **Message**: A string confirming the successful editing of the role.
            - **data**: The updated role object.
    """
    for permission in role.permissions:
        if permission not in RolePermissionsEnum._value2member_map_:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid role permissions: '{permission}'",
            )

    existing_role = db.query(Role).filter(Role.id == roleId).first()
    if not existing_role:
        raise HTTPException(status_code=404, detail=f"Role doesn't exist.")

    existing_role.role_name = role.role_name
    existing_role.permissions = role.permissions

    try:
        db.commit()
        db.refresh(existing_role)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Error to create role: {e}"
        )
    return {
        "Message": f"{existing_role.role_name} role permissions {existing_role.permissions} updated successfully.",
        "data": existing_role,
    }


@router.get("/show-role-by-id")
async def show_role_by_id(
    roleId: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Session = Depends(get_db),
):
    """Retrieve a role by its ID.

    Args:
        roleId (UUID): The UUID of the role to be retrieved.
        current_user (Annotated[User, Depends): Currently authenticated user.
        db (Session, optional): The database session dependency.
            Defaults to Depends(get_db).

    Raises:
        HTTPException:
            - **404 Not Found**: Raised if the role with the given
                `roleId` does not exist.

    Returns:
        Role: The role object containing its details.
    """
    role = db.query(Role).filter(Role.id == roleId).first()
    if not role:
        raise HTTPException(
            status_code=404,
            detail="Role not found.",
        )

    return role


@router.get("/show_all_roles")
@check_permissions(
    [RolePermissionsEnum.admin.value,]
)
async def show_all_roles(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Session = Depends(get_db),
):
    """Retrieve all roles from the database.

    Only users with `admin` and `HR` role permission are allowed to access
    this endpoint, as enforced by the `@check_permissions` decorator.

    Args:
        current_user (Annotated[User, Depends): Currently authenticated user.
        db (Session, optional): The database session dependency.
            Defaults to Depends(get_db).

    Returns:
        List[Role]: A list of all roles in the database.
    """
    roles = db.query(Role).all()
    return roles


@router.get("/show-users-with-same-roles")
@check_permissions(
    [RolePermissionsEnum.admin.value]
)
async def get_users_with_same_roles(
    role_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Session = Depends(get_db),
):
    """Retrieve all users that have the same role as the specified role ID.

    Only users with `admin` and `HR` role permission are allowed to access
    this endpoint, as enforced by the `@check_permissions` decorator.

    Args:
        role_id (UUID): The UUID of the role to retrieve users with.
        current_user (Annotated[User, Depends): Currently authenticated user.
        db (Session, optional): The database session dependency. Defaults to Depends(get_db).

    Returns:
        List[User]: A list of users who have the specified role.
    """
    users = db.query(User).filter(User.role_id == role_id).all()

    return users


@router.delete("/delete-role")
@check_permissions([RolePermissionsEnum.admin.value])
async def delete_role(
    role_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Session = Depends(get_db),
):
    """Delete a role from the system.

    Args:
        role_id (UUID): The UUID of the role to be deleted.
        current_user (Annotated[User, Depends): Currently authenticated user.
        db (Session, optional): The database session dependency.
            Defaults to Depends(get_db).

    Raises:
        HTTPException:
            - **404 Not Found**:
                - Raised if the role with the given `roleId` does not exist.
            - **403 Forbidden**:
                - Raised if the role has associated users and cannot be deleted.
            - **500 Internal Server Error**:
                - Raised if an error occurs while deleting the role from the database.

    Returns:
        dict: A dictionary containing a success message indicating that the role has been deleted.
    """
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found.")

    users = db.query(User).filter(User.role_id == role_id).all()

    if users:
        raise HTTPException(
            status_code=403,
            detail="Can't delete role. There are still members with the selected role.",
        )

    try:
        db.delete(role)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Unable to delete role.")

    return {"message": f"{role.role_name} role deleted successfully."}
