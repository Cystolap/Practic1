
import pytest
from pydantic import ValidationError

from app.auth import hash_password, verify_password
from app.models import User
from app.schemas.user import UserCreate
from app.services.auth_service import register_user, authenticate_user


def test_password_is_hashed_not_plain():
    raw = "secret123"
    hashed = hash_password(raw)
    assert hashed != raw
    assert hashed.startswith("$2")  


def test_verify_password_success():
    raw = "myPassword1"
    hashed = hash_password(raw)
    assert verify_password(raw, hashed) is True


def test_verify_password_wrong():
    hashed = hash_password("correct")
    assert verify_password("wrong", hashed) is False


def test_user_create_requires_min_password_length():
    with pytest.raises(ValidationError):
        UserCreate(email="a@b.com", password="12345", role="client")


def test_user_create_accepts_valid_client():
    data = UserCreate(email="new@test.com", password="123456", role="client")
    assert data.role == "client"
    assert data.password == "123456"


def test_user_create_default_role_is_client():
    data = UserCreate(email="x@y.com", password="123456")
    assert data.role == "client"


def test_register_user_success(db):
    data = UserCreate(email="reg@test.com", password="pass1234", role="client")
    user = register_user(db, data)
    assert user is not None
    assert user.email == "reg@test.com"
    assert user.role == "client"
    assert user.password_hash != "pass1234"
    assert verify_password("pass1234", user.password_hash)


def test_register_duplicate_email_returns_none(db):
    data = UserCreate(email="dup@test.com", password="pass1234", role="client")
    assert register_user(db, data) is not None
    assert register_user(db, data) is None


def test_authenticate_success(db, client_user):
    user = authenticate_user(db, "client@test.local", "client123")
    assert user is not None
    assert user.id == client_user.id
    assert user.role == "client"


def test_authenticate_wrong_password(db, client_user):
    assert authenticate_user(db, "client@test.local", "bad") is None


def test_authenticate_unknown_email(db):
    assert authenticate_user(db, "nobody@test.local", "any") is None


def test_roles_stored_correctly(db, admin_user, master_user, client_user):
    assert admin_user.role == "admin"
    assert master_user.role == "master"
    assert client_user.role == "client"
