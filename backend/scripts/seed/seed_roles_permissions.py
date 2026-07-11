import os
import logging
from app.db.database import SessionLocal
from app.db.models import User, Role, Permission
from app.auth.password import get_password_hash
from app.auth.permissions import (
    PORTFOLIO_READ, PORTFOLIO_WRITE, RISK_READ, RISK_EXECUTE,
    STRESS_EXECUTE, LIQUIDITY_EXECUTE, BREACH_ACKNOWLEDGE,
    LIMIT_MANAGE, PIPELINE_RUN, QUALITY_RUN, ANALYTICS_RUN,
    REPORT_GENERATE, AUDIT_READ, USER_MANAGE,
    BREACH_READ, BREACH_ASSIGN, BREACH_REVIEW, BREACH_RESOLVE,
    NOTIFICATION_READ, NOTIFICATION_MANAGE
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_data(db=None):
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True
        
    try:
        # Define all permissions
        all_perms = [
            PORTFOLIO_READ, PORTFOLIO_WRITE, RISK_READ, RISK_EXECUTE,
            STRESS_EXECUTE, LIQUIDITY_EXECUTE, BREACH_ACKNOWLEDGE,
            LIMIT_MANAGE, PIPELINE_RUN, QUALITY_RUN, ANALYTICS_RUN,
            REPORT_GENERATE, AUDIT_READ, USER_MANAGE,
            BREACH_READ, BREACH_ASSIGN, BREACH_REVIEW, BREACH_RESOLVE,
            NOTIFICATION_READ, NOTIFICATION_MANAGE
        ]
        
        # Idempotently seed permissions
        db_perms = {}
        for p_name in all_perms:
            perm = db.query(Permission).filter(Permission.name == p_name).first()
            if not perm:
                perm = Permission(name=p_name, description=f"Permission for {p_name}")
                db.add(perm)
                db.flush()
                logger.info(f"Created permission: {p_name}")
            db_perms[p_name] = perm
            
        # Role definition mapping
        role_definitions = {
            "ANALYST": {
                "desc": "Read-only access to portfolios, risk, analytics, and generating reports",
                "perms": [PORTFOLIO_READ, RISK_READ, REPORT_GENERATE, BREACH_READ, NOTIFICATION_READ]
            },
            "PORTFOLIO_MANAGER": {
                "desc": "Analyst access plus portfolio modifications, stress test and liquidity revaluation execution",
                "perms": [PORTFOLIO_READ, RISK_READ, REPORT_GENERATE, PORTFOLIO_WRITE, STRESS_EXECUTE, LIQUIDITY_EXECUTE, BREACH_READ, NOTIFICATION_READ]
            },
            "RISK_MANAGER": {
                "desc": "Risk limits and breaches evaluation, limit modification, breach acknowledgement, and analytics run execution",
                "perms": [PORTFOLIO_READ, RISK_READ, REPORT_GENERATE, RISK_EXECUTE, LIMIT_MANAGE, BREACH_ACKNOWLEDGE, ANALYTICS_RUN, BREACH_READ, BREACH_ASSIGN, BREACH_REVIEW, BREACH_RESOLVE, NOTIFICATION_READ, NOTIFICATION_MANAGE]
            },
            "ADMIN": {
                "desc": "Identity administration, role controls, full pipeline run controls, and full system configuration access",
                "perms": all_perms
            }
        }
        
        # Idempotently seed roles
        db_roles = {}
        for r_name, r_def in role_definitions.items():
            role = db.query(Role).filter(Role.name == r_name).first()
            if not role:
                role = Role(name=r_name, description=r_def["desc"])
                db.add(role)
                db.flush()
                logger.info(f"Created role: {r_name}")
                
            # Update permissions mapping
            role.permissions = [db_perms[p] for p in r_def["perms"]]
            db.flush()
            db_roles[r_name] = role
            
        db.commit()
        logger.info("Roles and permissions seeded successfully.")
        
        # Admin bootstrap
        admin_username = os.getenv("ADMIN_USERNAME", "admin")
        admin_password = os.getenv("ADMIN_PASSWORD")
        admin_email = os.getenv("ADMIN_EMAIL", "admin@bondguard.com")
        
        if admin_password:
            admin_user = db.query(User).filter(User.username == admin_username).first()
            if not admin_user:
                admin_user = User(
                    username=admin_username,
                    email=admin_email,
                    hashed_password=get_password_hash(admin_password),
                    is_active=True,
                    roles=[db_roles["ADMIN"]]
                )
                db.add(admin_user)
                db.commit()
                logger.info(f"Created bootstrap admin user: '{admin_username}'")
            else:
                # Update password/email/roles to ensure idempotency and correct hash
                admin_user.hashed_password = get_password_hash(admin_password)
                admin_user.email = admin_email
                if db_roles["ADMIN"] not in admin_user.roles:
                    admin_user.roles.append(db_roles["ADMIN"])
                db.commit()
                logger.info(f"Bootstrap admin user '{admin_username}' credentials updated.")
        else:
            logger.warning("ADMIN_PASSWORD environment variable not set. Skipping admin user bootstrapping.")
            
    except Exception as e:
        db.rollback()
        logger.error(f"Seeding failed: {e}")
        raise
    finally:
        if close_db:
            db.close()

if __name__ == "__main__":
    seed_data()
