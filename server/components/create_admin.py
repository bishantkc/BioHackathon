from fastapi import HTTPException
from models.models import User, Role


async def create_admin_user(db):
    # Check if the "admin" role already exists
    admin_role = db.query(Role).filter_by(role_name="admin").first()

    if not admin_role:
        # If the "admin" role doesn't exist, create it
        admin_role = Role(role_name="admin", permissions=["admin"])
        db.add(admin_role)
        db.commit()
        db.refresh(admin_role)

    # Check if the admin user already exists
    admin_user = db.query(User).filter_by(username="admin").first()

    if not admin_user:
        # If the admin user doesn't exist, create it
        admin_user_data = {
            "username": "admin",
            "email": "admin@brocoders.com",
            "full_name": "Admin",
            "role_id": admin_role.id,
        }

        admin_user = User(**admin_user_data)
        try:
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Unable to create admin user: {e}"
            )
