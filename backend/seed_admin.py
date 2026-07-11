import asyncio
from app.db.database import SessionLocal
from app.auth.password import get_password_hash
from app.db.models import User, Role

def seed():
    session = SessionLocal()
    try:
        admin_role = session.query(Role).filter_by(name='ADMIN').first()
        if not admin_role:
            admin_role = Role(name='ADMIN')
            session.add(admin_role)
            session.commit()
            
        admin_user = session.query(User).filter_by(username='admin').first()
        if not admin_user:
            admin_user = User(
                username='admin',
                email='admin@bondguard.com',
                hashed_password=get_password_hash('admin123'),
                is_active=True
            )
            admin_user.roles.append(admin_role)
            session.add(admin_user)
            session.commit()
            print("Admin user created successfully.")
        else:
            admin_user.hashed_password = get_password_hash('admin123')
            if admin_role not in admin_user.roles:
                admin_user.roles.append(admin_role)
            admin_user.is_active = True
            session.commit()
            print("Admin user updated successfully.")
    except Exception as e:
        print("Error:", e)
    finally:
        session.close()

if __name__ == "__main__":
    seed()
