from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List

from app.db.database import get_db
from app.auth.service import AuthService
from app.auth.dependencies import get_current_user
from app.db.models import User

router = APIRouter()

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    refresh_token: str

class RefreshRequest(BaseModel):
    refresh_token: str

class LogoutRequest(BaseModel):
    refresh_token: str

class UserRoleOut(BaseModel):
    name: str

class UserMeResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    roles: List[str]
    permissions: List[str]

@router.post("/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = AuthService.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
        
    access_token, refresh_token = AuthService.create_auth_session(db, user)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token
    }

@router.post("/refresh", response_model=TokenResponse)
def refresh(req: RefreshRequest, db: Session = Depends(get_db)):
    access_token, refresh_token = AuthService.rotate_refresh_token(db, req.refresh_token)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token
    }

@router.post("/logout")
def logout(req: LogoutRequest, db: Session = Depends(get_db)):
    AuthService.revoke_refresh_token(db, req.refresh_token)
    return {"detail": "Successfully logged out"}

@router.get("/me", response_model=UserMeResponse)
def get_me(current_user: User = Depends(get_current_user)):
    roles = [role.name for role in current_user.roles]
    permissions = set()
    for role in current_user.roles:
        for perm in role.permissions:
            permissions.add(perm.name)
            
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "is_active": current_user.is_active,
        "roles": roles,
        "permissions": list(permissions)
    }
