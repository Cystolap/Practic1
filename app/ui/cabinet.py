#Личный кабинет клиента
from nicegui import ui
from sqlalchemy.orm import joinedload

from app.database import SessionLocal
from app.models import Card, BoardColumn, Board, Project, User
from app.ui import state


@ui.page("/cabinet")
def cabinet_page():
    user = state.current_user()
    if not user:
        ui.navigate.to("/login")
        return

    ui.query("body").classes(
        "bg-gradient-to-br from-sky-50 via-blue-50 to-indigo-50 min-h-screen"
    )

    with ui.header().classes("bg-white/90 backdrop-blur shadow-sm items-center px-6 py-3 gap-3"):
        ui.label("🔧 Ремонтная мастерская").classes("text-xl font-bold text-indigo-700")
        ui.space()
        ui.label(f"{user['email']} ({user['role']})").classes("text-sm text-gray-600")
        ui.button("Доски", on_click=lambda: ui.navigate.to("/projects")).props("flat dense")
        ui.button(
            "Выйти",
            on_click=lambda: (state.clear_user(), ui.navigate.to("/login")),
        ).props("flat dense").classes("text-gray-600")

    with ui.column().classes("w-full max-w-4xl mx-auto p-6 gap-4"):
        ui.label("Личный кабинет").classes("text-2xl font-bold text-gray-800")
        ui.label("Ваши заявки на ремонт и текущий статус").classes("text-gray-500 mb-2")

        container = ui.column().classes("w-full gap-3")

        def load():
            container.clear()
            db = SessionLocal()
            try:
                # Заявки пользователя
                cards = (
                    db.query(Card)
                    .options(joinedload(Card.comments))
                    .filter(Card.creator_id == user["id"])
                    .order_by(Card.created_at.desc())
                    .all()
                )
                if not cards:
                    with container:
                        ui.label(
                            "У вас пока нет заявок. Откройте доску и создайте заявку в колонке «Новая заявка»."
                        ).classes("text-gray-500 text-lg py-8")
                    return

                
                col_ids = {c.column_id for c in cards}
                columns = {
                    col.id: col
                    for col in db.query(BoardColumn).filter(BoardColumn.id.in_(col_ids)).all()
                }
                board_ids = {col.board_id for col in columns.values()}
                boards = {
                    b.id: b for b in db.query(Board).filter(Board.id.in_(board_ids)).all()
                }
                project_ids = {b.project_id for b in boards.values()}
                projects = {
                    p.id: p
                    for p in db.query(Project).filter(Project.id.in_(project_ids)).all()
                }
                staff = {
                    u.id: u.email
                    for u in db.query(User).filter(User.role.in_(["master", "admin"])).all()
                }

                with container:
                    for card in cards:
                        col = columns.get(card.column_id)
                        status = col.name if col else "—"
                        board = boards.get(col.board_id) if col else None
                        project = projects.get(board.project_id) if board else None
                        project_name = project.name if project else "—"

                        status_colors = {
                            "Новая заявка": "bg-orange-100 text-orange-800",
                            "Принята": "bg-sky-100 text-sky-800",
                            "Диагностика": "bg-violet-100 text-violet-800",
                            "В ремонте": "bg-amber-100 text-amber-800",
                            "Готова к выдаче": "bg-emerald-100 text-emerald-800",
                            "Выдана": "bg-green-100 text-green-800",
                        }
                        badge_cls = status_colors.get(status, "bg-gray-100 text-gray-700")

                        with ui.card().classes(
                            "w-full p-4 rounded-xl border border-gray-100 shadow-sm"
                        ):
                            with ui.row().classes("w-full items-start justify-between gap-3"):
                                with ui.column().classes("gap-1 flex-1"):
                                    ui.label(card.title).classes(
                                        "text-lg font-semibold text-gray-800"
                                    )
                                    if card.description:
                                        ui.label(card.description[:200]).classes(
                                            "text-sm text-gray-600"
                                        )
                                    meta_parts = [
                                        f"Доска: {project_name}",
                                        f"Создана: {card.created_at.strftime('%d.%m.%Y %H:%M') if card.created_at else '—'}",
                                    ]
                                    if card.deadline:
                                        meta_parts.append(
                                            f"Желаемый срок: {card.deadline.strftime('%d.%m.%Y')}"
                                        )
                                    if card.assignee_id and card.assignee_id in staff:
                                        meta_parts.append(
                                            f"Мастер: {staff[card.assignee_id].split('@')[0]}"
                                        )
                                    if card.estimated_price is not None:
                                        meta_parts.append(f"Стоимость: {card.estimated_price} ₽")
                                    ui.label(" · ".join(meta_parts)).classes(
                                        "text-xs text-gray-400"
                                    )
                                    if card.master_notes:
                                        ui.label(f"Комментарий мастера: {card.master_notes}").classes(
                                            "text-sm text-indigo-700 mt-1"
                                        )
                                ui.badge(status).classes(
                                    f"{badge_cls} text-sm font-medium px-3 py-1"
                                )

                            if card.photo_url:
                                with ui.row().classes("mt-2"):
                                    ui.image(card.photo_url).classes(
                                        "w-32 h-24 object-cover rounded-lg border"
                                    )

                            if board and project:
                                ui.button(
                                    "Открыть на доске",
                                    on_click=lambda pid=project.id: ui.navigate.to(
                                        f"/board/{pid}"
                                    ),
                                ).props("flat dense").classes("text-indigo-600 mt-1")
            finally:
                db.close()

        load()
        ui.button("Обновить", icon="refresh", on_click=load).props("flat").classes(
            "text-indigo-600"
        )
