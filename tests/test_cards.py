
from datetime import datetime

from app.models import Project, Board, BoardColumn, Card, Comment, History
from app.schemas.project import ProjectCreate
from app.services.project_service import create_new_project, is_request_column


def _first_board_and_columns(db, admin_user):
    p = create_new_project(
        db, ProjectCreate(name="Тест", description=""), owner_id=admin_user.id
    )
    board = db.query(Board).filter(Board.project_id == p.id).first()
    cols = {
        c.name: c
        for c in db.query(BoardColumn).filter(BoardColumn.board_id == board.id).all()
    }
    return p, board, cols


def test_create_repair_request_card(db, admin_user, client_user):
    _, _, cols = _first_board_and_columns(db, admin_user)
    col = cols["Новая заявка"]
    assert is_request_column(col.name)

    card = Card(
        column_id=col.id,
        title="Не включается смартфон",
        description="После падения не реагирует на кнопку",
        creator_id=client_user.id,
        deadline=datetime(2026, 12, 1),
        photo_url="/uploads/test.jpg",
        priority="Средний",
        position=0,
    )
    db.add(card)
    db.commit()
    db.refresh(card)

    assert card.id is not None
    assert card.creator_id == client_user.id
    assert card.photo_url.endswith(".jpg")
    assert card.column_id == col.id


def test_master_changes_status_and_sets_price(db, admin_user, master_user, client_user):
    _, _, cols = _first_board_and_columns(db, admin_user)
    card = Card(
        column_id=cols["Новая заявка"].id,
        title="Ремонт ноутбука",
        description="Не заряжается",
        creator_id=client_user.id,
        position=0,
    )
    db.add(card)
    db.commit()
    db.refresh(card)

    card.column_id = cols["Принята"].id
    card.assignee_id = master_user.id
    card.estimated_price = 4500
    card.master_notes = "Нужна замена разъёма"
    db.add(
        History(
            card_id=card.id,
            user_id=master_user.id,
            action="Смена статуса: Принята",
        )
    )
    db.commit()
    db.refresh(card)

    assert card.column_id == cols["Принята"].id
    assert card.assignee_id == master_user.id
    assert float(card.estimated_price) == 4500.0
    assert card.master_notes != ""
    assert db.query(History).filter(History.card_id == card.id).count() >= 1


def test_status_flow_columns_exist(db, admin_user):
    _, _, cols = _first_board_and_columns(db, admin_user)
    for name in [
        "Новая заявка",
        "Принята",
        "Диагностика",
        "В ремонте",
        "Готова к выдаче",
        "Выдана",
    ]:
        assert name in cols


def test_master_adds_comment(db, admin_user, master_user, client_user):
    _, _, cols = _first_board_and_columns(db, admin_user)
    card = Card(
        column_id=cols["Диагностика"].id,
        title="Планшет",
        description="Треснул экран",
        creator_id=client_user.id,
        assignee_id=master_user.id,
        position=0,
    )
    db.add(card)
    db.commit()
    db.refresh(card)

    db.add(
        Comment(
            card_id=card.id,
            user_id=master_user.id,
            text="Нужен заказ экрана, срок 3 дня",
        )
    )
    db.commit()

    comments = db.query(Comment).filter(Comment.card_id == card.id).all()
    assert len(comments) == 1
    assert "экран" in comments[0].text.lower()


def test_parts_card_on_warehouse_board(db, admin_user):
    create_new_project(
        db, ProjectCreate(name="X", description=""), owner_id=admin_user.id
    )
    parts_proj = db.query(Project).filter(Project.board_type == "parts").first()
    board = db.query(Board).filter(Board.project_id == parts_proj.id).first()
    col = (
        db.query(BoardColumn)
        .filter(BoardColumn.board_id == board.id, BoardColumn.name == "В наличии")
        .first()
    )
    card = Card(
        column_id=col.id,
        title="Экран iPhone 13",
        description="Оригинал",
        labels="SKU:SCR-13; qty:10",
        priority="10",
        estimated_price=3200,
        position=0,
    )
    db.add(card)
    db.commit()
    db.refresh(card)
    assert "SKU:" in card.labels
    assert float(card.estimated_price) == 3200


def test_price_list_service_card(db, admin_user):
    create_new_project(
        db, ProjectCreate(name="Y", description=""), owner_id=admin_user.id
    )
    price_proj = db.query(Project).filter(Project.board_type == "price").first()
    board = db.query(Board).filter(Board.project_id == price_proj.id).first()
    col = (
        db.query(BoardColumn)
        .filter(BoardColumn.board_id == board.id, BoardColumn.name == "Услуги")
        .first()
    )
    card = Card(
        column_id=col.id,
        title="Замена экрана",
        description="Смартфоны",
        labels="Экраны",
        estimated_price=5000,
        position=0,
    )
    db.add(card)
    db.commit()
    db.refresh(card)
    assert float(card.estimated_price) == 5000
    assert card.labels == "Экраны"




