from sqlalchemy.orm import Session
from app.models import Project, Board, BoardColumn, User
from app.schemas.project import ProjectCreate

PRICE_BOARD_NAME = "Прайс-лист"
PARTS_BOARD_NAME = "Склад запчастей"

REQUEST_COLUMN_NAMES = {"Новая заявка", "Заявка", "Заявки"}

BOARD_LABEL_OPTIONS = [
    "Смартфоны",
    "Ноутбуки",
    "Планшеты",
    "ПК",
    "Бытовая техника",
    "Другое",
]

REPAIR_COLUMNS = [
    "Новая заявка",
    "Принята",
    "Диагностика",
    "В ремонте",
    "Готова к выдаче",
    "Выдана",
]

PRICE_COLUMNS = ["Услуги", "Архив"]
PARTS_COLUMNS = ["В наличии", "Заканчивается", "Нет в наличии"]


def is_request_column(name: str) -> bool:
    if not name:
        return False
    n = name.strip().lower()
    if name.strip() in REQUEST_COLUMN_NAMES:
        return True
    return "заявк" in n


def _make_board_with_columns(db: Session, project: Project, board_name: str, columns: list[str]):
    board = Board(project_id=project.id, name=board_name)
    db.add(board)
    db.commit()
    db.refresh(board)
    for i, name in enumerate(columns):
        db.add(BoardColumn(board_id=board.id, name=name, position=i))
    db.commit()
    return board


def create_new_project(
    db: Session,
    project_data: ProjectCreate,
    owner_id: int,
    labels: str = "",
    master_id: int | None = None,
):
    new_project = Project(
        name=project_data.name,
        description=project_data.description,
        owner_id=owner_id,
        board_type="ordinary",
        labels=labels or "",
        master_id=master_id,
    )
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    _make_board_with_columns(db, new_project, "Доска заявок", REPAIR_COLUMNS)
    ensure_special_boards(db, owner_id)
    return new_project


def ensure_special_boards(db: Session, owner_id: int):
    for name, btype, cols in [
        (PRICE_BOARD_NAME, "price", PRICE_COLUMNS),
        (PARTS_BOARD_NAME, "parts", PARTS_COLUMNS),
    ]:
        existing = db.query(Project).filter(Project.name == name).first()
        if existing:
            if not getattr(existing, "board_type", None) or existing.board_type == "ordinary":
                existing.board_type = btype
                db.commit()
            continue
        p = Project(
            name=name,
            description="Служебная доска",
            owner_id=owner_id,
            board_type=btype,
            labels="",
        )
        db.add(p)
        db.commit()
        db.refresh(p)
        _make_board_with_columns(db, p, name, cols)


def get_user_projects(db: Session, user_id: int, role: str):
    try:
        q = db.query(Project).order_by(Project.created_at.desc())
        if role == "client":
            q = q.filter(Project.board_type.in_(["ordinary", "price"]))
        return q.all()
    except Exception as e:
        print(f"Ошибка при получении проектов: {e}")
        raise e


def get_staff_emails(db: Session) -> list[str]:
    users = (
        db.query(User)
        .filter(User.role.in_(["master", "admin"]))
        .order_by(User.email)
        .all()
    )
    return [u.email for u in users]


def get_masters(db: Session) -> list[User]:
    return (
        db.query(User)
        .filter(User.role.in_(["master", "admin"]))
        .order_by(User.email)
        .all()
    )
