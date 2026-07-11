from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
import logging

from app.db.models import User, RefreshToken
from app.auth.password import verify_password
from app.auth.tokens import create_access_token, generate_refresh_token
from app.auth.exceptions import CredentialsException
from app.core.config import settings

logger = logging.getLogger(__name__)

# In-memory store for tracking failed login attempts
# Format: {username_or_email: {"attempts": int, "lockout_until": datetime}}
FAILED_LOGINS = {}

class AuthService:
    @staticmethod
    def authenticate_user(db: Session, username_or_email: str, password: str) -> Optional[User]:
        now = datetime.now(timezone.utc)
        
        # Check lockout
        lockout_info = FAILED_LOGINS.get(username_or_email)
        if lockout_info and lockout_info["lockout_until"]:
            # Convert to UTC-aware if needed
            lock_until = lockout_info["lockout_until"]
            if lock_until.tzinfo is None:
                lock_until = lock_until.replace(tzinfo=timezone.utc)
            if now < lock_until:
                minutes_left = int((lock_until - now).total_seconds() / 60) + 1
                raise CredentialsException(f"Account locked out. Try again in {minutes_left} minutes.")
        
        user = db.query(User).filter(
            (User.username == username_or_email) | (User.email == username_or_email)
        ).first()
        
        if not user or not verify_password(password, user.hashed_password):
            # Increment failed attempts
            if username_or_email not in FAILED_LOGINS:
                FAILED_LOGINS[username_or_email] = {"attempts": 0, "lockout_until": None}
            
            FAILED_LOGINS[username_or_email]["attempts"] += 1
            if FAILED_LOGINS[username_or_email]["attempts"] >= 5:
                FAILED_LOGINS[username_or_email]["lockout_until"] = now + timedelta(minutes=15)
                logger.warning(f"User '{username_or_email}' locked out due to too many failed attempts")
                raise CredentialsException("Account locked out due to too many failed attempts. Try again in 15 minutes.")
                
            if not user:
                logger.warning(f"Failed login attempt: user '{username_or_email}' not found")
            else:
                logger.warning(f"Failed login attempt: incorrect password for '{username_or_email}'")
            return None
            
        # Reset failed attempts on success
        if username_or_email in FAILED_LOGINS:
            FAILED_LOGINS.pop(username_or_email)
            
        return user

    @staticmethod
    def create_auth_session(db: Session, user: User) -> Tuple[str, str]:
        # Generate access token
        # Include user info and permissions list in access token payload
        permissions = set()
        for role in user.roles:
            for perm in role.permissions:
                permissions.add(perm.name)
        
        access_token_data = {
            "sub": str(user.id),
            "username": user.username,
            "permissions": list(permissions)
        }
        access_token = create_access_token(access_token_data)

        # Generate refresh token
        token_str = generate_refresh_token()
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        
        db_refresh_token = RefreshToken(
            user_id=user.id,
            token=token_str,
            expires_at=expires_at,
            is_revoked=False
        )
        db.add(db_refresh_token)
        db.commit()
        
        return access_token, token_str

    @staticmethod
    def rotate_refresh_token(db: Session, refresh_token_str: str) -> Tuple[str, str]:
        db_token = db.query(RefreshToken).filter(RefreshToken.token == refresh_token_str).first()
        if not db_token:
            raise CredentialsException("Invalid refresh token")
        
        # Token reuse or revocation check
        if db_token.is_revoked:
            # Revoke all tokens for this user as a safety precaution against theft
            db.query(RefreshToken).filter(RefreshToken.user_id == db_token.user_id).update({"is_revoked": True})
            db.commit()
            raise CredentialsException("Refresh token has been revoked previously")
            
        if db_token.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
            raise CredentialsException("Refresh token has expired")

        # Mark current token as revoked (used)
        db_token.is_revoked = True
        db.commit()

        # Create new session
        user = db.query(User).filter(User.id == db_token.user_id).first()
        if not user or not user.is_active:
            raise CredentialsException("User account is inactive or deleted")

        return AuthService.create_auth_session(db, user)

    @staticmethod
    def revoke_refresh_token(db: Session, refresh_token_str: str) -> None:
        db_token = db.query(RefreshToken).filter(RefreshToken.token == refresh_token_str).first()
        if db_token:
            db_token.is_revoked = True
            db.commit()
