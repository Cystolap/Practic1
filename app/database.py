from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def migrate_schema():
    #Добавляет новые колонки, если таблицы уже существовали
    alters = [
        "ALTER TABLE cards ADD COLUMN IF NOT EXISTS creator_id INTEGER",
        "ALTER TABLE cards ADD COLUMN IF NOT EXISTS photo_url TEXT DEFAULT ''",
        "ALTER TABLE cards ADD COLUMN IF NOT EXISTS master_notes TEXT DEFAULT ''",
        "ALTER TABLE cards ADD COLUMN IF NOT EXISTS estimated_price NUMERIC(10,2)",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS board_type VARCHAR(20) DEFAULT 'ordinary'",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS labels VARCHAR(255) DEFAULT ''",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS master_id INTEGER",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS full_name VARCHAR(255) DEFAULT ''",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS phone VARCHAR(50) DEFAULT ''",
    ]
    with engine.begin() as conn:
        for sql in alters:
            try:
                conn.execute(text(sql))
            except Exception as e:
                print(f"migrate skip: {e}")


def ensure_default_admin():
    #Создаёт администратора, если его ещё нет
    from app.models import User
    from app.auth import hash_password

    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.email == "admin@repair.local").first()
        if admin:
            if admin.role != "admin":
                admin.role = "admin"
                db.commit()
            return
        #Поиск админа
        any_admin = db.query(User).filter(User.role == "admin").first()
        if any_admin:
            return
        db.add(
            User(
                email="admin@repair.local",
                password_hash=hash_password("admin123"),
                role="admin",
                full_name="Администратор системы",
                phone="",
            )
        )
        db.commit()
        print("Создан встроенный админ: admin@repair.local / admin123")
    except Exception as e:
        print(f"ensure_default_admin: {e}")
        db.rollback()
    finally:
        db.close()
