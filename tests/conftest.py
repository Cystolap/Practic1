
import os


os.environ["DATABASE_URL"] = "sqlite://"
os.environ["JWT_SECRET"] = "test-secret-for-unit-tests"

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import User
from app.auth import hash_password


@pytest.fixture()
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def admin_user(db):
    u = User(
        email="admin@test.local",
        password_hash=hash_password("admin123"),
        role="admin",
        full_name="Админ Тест",
        phone="+70000000000",
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@pytest.fixture()
def master_user(db):
    u = User(
        email="master@test.local",
        password_hash=hash_password("master123"),
        role="master",
        full_name="Иванов Иван",
        phone="+71111111111",
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@pytest.fixture()
def client_user(db):
    u = User(
        email="client@test.local",
        password_hash=hash_password("client123"),
        role="client",
        full_name="Петров Пётр",
        phone="+72222222222",
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u