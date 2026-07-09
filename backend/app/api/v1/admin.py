from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import List, Optional

from app.db.database import get_db
from app.db.models import User, Role
from app.auth.dependencies import PermissionChecker
from app.auth.password import get_password_hash
from app.auth.permissions import USER_MANAGE
from app.risk_control.audit_service import AuditService

router = APIRouter()

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    role_names: List[str]

class UserUpdate(BaseModel):
    email: Optional[str] = None
    is_active: Optional[bool] = None
    role_names: Optional[List[str]] = None

class RoleOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    permissions: List[str]

    class Config:
        from_attributes = True

class UserOut(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    roles: List[str]

    class Config:
        from_attributes = True

# Guard all routes in this router with USER_MANAGE permission
admin_dependency = Depends(PermissionChecker(USER_MANAGE))

@router.get("/users", response_model=List[UserOut], dependencies=[admin_dependency])
def list_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    out = []
    for u in users:
        out.append({
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "is_active": u.is_active,
            "roles": [r.name for r in u.roles]
        })
    return out

@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED, dependencies=[admin_dependency])
def create_user(user_in: UserCreate, db: Session = Depends(get_db)):
    # Check duplicate
    existing = db.query(User).filter((User.username == user_in.username) | (User.email == user_in.email)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username or email already exists")

    # Resolve roles
    db_roles = db.query(Role).filter(Role.name.in_(user_in.role_names)).all()
    if len(db_roles) != len(user_in.role_names):
        raise HTTPException(status_code=400, detail="One or more specified roles do not exist")

    hashed_pw = get_password_hash(user_in.password)
    db_user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=hashed_pw,
        is_active=True,
        roles=db_roles
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    AuditService.append_event(
        db, "USER_CREATED", "USER", db_user.id, "CREATE",
        new_state={"username": db_user.username, "roles": user_in.role_names}
    )
    db.commit()

    return {
        "id": db_user.id,
        "username": db_user.username,
        "email": db_user.email,
        "is_active": db_user.is_active,
        "roles": [r.name for r in db_user.roles]
    }

@router.patch("/users/{user_id}", response_model=UserOut, dependencies=[admin_dependency])
def update_user(user_id: int, user_up: UserUpdate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    prev_state = {
        "email": db_user.email,
        "is_active": db_user.is_active,
        "roles": [r.name for r in db_user.roles]
    }

    new_state = {}

    if user_up.email is not None:
        # Check duplicate email
        dup = db.query(User).filter(User.email == user_up.email, User.id != user_id).first()
        if dup:
            raise HTTPException(status_code=400, detail="Email already in use")
        db_user.email = user_up.email
        new_state["email"] = user_up.email

    if user_up.is_active is not None:
        db_user.is_active = user_up.is_active
        new_state["is_active"] = user_up.is_active

    if user_up.role_names is not None:
        db_roles = db.query(Role).filter(Role.name.in_(user_up.role_names)).all()
        if len(db_roles) != len(user_up.role_names):
            raise HTTPException(status_code=400, detail="One or more specified roles do not exist")
        db_user.roles = db_roles
        new_state["roles"] = user_up.role_names

    db.commit()
    db.refresh(db_user)

    AuditService.append_event(
        db, "USER_UPDATED", "USER", db_user.id, "UPDATE",
        previous_state=prev_state,
        new_state=new_state
    )
    db.commit()

    return {
        "id": db_user.id,
        "username": db_user.username,
        "email": db_user.email,
        "is_active": db_user.is_active,
        "roles": [r.name for r in db_user.roles]
    }

@router.get("/roles", response_model=List[RoleOut], dependencies=[admin_dependency])
def list_roles(db: Session = Depends(get_db)):
    roles = db.query(Role).all()
    out = []
    for r in roles:
        out.append({
            "id": r.id,
            "name": r.name,
            "description": r.description,
            "permissions": [p.name for p in r.permissions]
        })
    return out
