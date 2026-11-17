
from app.models import Project, Board, BoardColumn
from app.schemas.project import ProjectCreate
from app.services.project_service import (
    create_new_project,
    ensure_special_boards,
    get_user_projects,
    is_request_column,
    REPAIR_COLUMNS,
    PRICE_BOARD_NAME,
    PARTS_BOARD_NAME,
)


def test_is_request_column_exact_names():
    assert is_request_column("Новая заявка") is True
    assert is_request_column("Заявка") is True
    assert is_request_column("Заявки") is True


def test_is_request_column_fuzzy():
    assert is_request_column("Мои заявки") is True
    assert is_request_column("  Новая заявка  ") is True


def test_is_request_column_rejects_other_statuses():
    assert is_request_column("Принята") is False
    assert is_request_column("В ремонте") is False
    assert is_request_column("Выдана") is False
    assert is_request_column("") is False
    assert is_request_column(None) is False


def test_create_project_has_repair_status_columns(db, admin_user):
    p = create_new_project(
        db,
        ProjectCreate(name="Основная мастерская", description="test"),
        owner_id=admin_user.id,
        labels="Смартфоны,Ноутбуки",
    )
    assert p.id is not None
    assert p.board_type == "ordinary"
    assert "Смартфоны" in p.labels

    board = db.query(Board).filter(Board.project_id == p.id).first()
    assert board is not None
    cols = (
        db.query(BoardColumn)
        .filter(BoardColumn.board_id == board.id)
        .order_by(BoardColumn.position)
        .all()
    )
    names = [c.name for c in cols]
    assert names == REPAIR_COLUMNS
    for status in ["Принята", "Диагностика", "В ремонте", "Готова к выдаче", "Выдана"]:
        assert status in names


def test_create_project_also_creates_price_and_parts(db, admin_user):
    create_new_project(
        db, ProjectCreate(name="Доска 1", description=""), owner_id=admin_user.id
    )
    names = {p.name for p in db.query(Project).all()}
    assert PRICE_BOARD_NAME in names
    assert PARTS_BOARD_NAME in names

    price = db.query(Project).filter(Project.name == PRICE_BOARD_NAME).first()
    parts = db.query(Project).filter(Project.name == PARTS_BOARD_NAME).first()
    assert price.board_type == "price"
    assert parts.board_type == "parts"


def test_ensure_special_boards_idempotent(db, admin_user):
    ensure_special_boards(db, admin_user.id)
    ensure_special_boards(db, admin_user.id)
    assert db.query(Project).filter(Project.name == PRICE_BOARD_NAME).count() == 1
    assert db.query(Project).filter(Project.name == PARTS_BOARD_NAME).count() == 1


def test_client_sees_ordinary_and_price_not_parts(db, admin_user, client_user):
    create_new_project(
        db, ProjectCreate(name="Заявки", description=""), owner_id=admin_user.id
    )
    projects = get_user_projects(db, client_user.id, "client")
    types = {p.board_type for p in projects}
    assert "ordinary" in types
    assert "price" in types
    assert "parts" not in types


def test_master_sees_all_board_types(db, admin_user, master_user):
    create_new_project(
        db, ProjectCreate(name="Заявки", description=""), owner_id=admin_user.id
    )
    projects = get_user_projects(db, master_user.id, "master")
    types = {p.board_type for p in projects}
    assert "ordinary" in types
    assert "price" in types
    assert "parts" in types


def test_admin_sees_all_board_types(db, admin_user):
    create_new_project(
        db, ProjectCreate(name="Заявки", description=""), owner_id=admin_user.id
    )
    projects = get_user_projects(db, admin_user.id, "admin")
    types = {p.board_type for p in projects}
    assert types >= {"ordinary", "price", "parts"}
