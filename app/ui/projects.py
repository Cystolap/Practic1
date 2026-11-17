from nicegui import ui
from app.database import SessionLocal
from app.models import Project, User, Board, BoardColumn, Card, Comment, History
from app.ui import state
from app.services.project_service import (
    create_new_project,
    get_user_projects,
    ensure_special_boards,
    BOARD_LABEL_OPTIONS,
    get_masters,
)
from app.schemas.project import ProjectCreate


@ui.page("/projects")
def projects_page():
    user = state.current_user()
    if not user:
        ui.navigate.to("/login")
        return

    can_manage = user["role"] in ("admin", "master")
    is_client = user["role"] == "client"

    ui.query("body").classes(
        "bg-gradient-to-br from-sky-50 via-blue-50 to-indigo-50 min-h-screen"
    )

    with ui.header().classes(
        "bg-white/80 backdrop-blur shadow-sm items-center px-6 py-3 gap-2"
    ):
        ui.label("🔧 Ремонтная мастерская").classes("text-xl font-bold text-indigo-700")
        ui.space()
        ui.label(f"{user['email']} ({user['role']})").classes("text-sm text-gray-600")
        if is_client:
            ui.button(
                "Мой кабинет",
                icon="person",
                on_click=lambda: ui.navigate.to("/cabinet"),
            ).props("flat dense")
        if user["role"] == "admin":
            ui.button(
                "Профили",
                icon="group",
                on_click=lambda: ui.navigate.to("/admin/users"),
            ).props("flat dense")
        ui.button(
            "Выйти",
            on_click=lambda: (state.clear_user(), ui.navigate.to("/login")),
        ).props("flat dense").classes("text-gray-600")

    # Фильтры
    filters = {"label": "Все", "master": "Все"}

    with ui.column().classes("w-full max-w-5xl mx-auto p-6 gap-4"):
        with ui.row().classes("w-full items-center justify-between flex-wrap gap-2"):
            ui.label("Доски").classes("text-2xl font-bold text-gray-800")
            if can_manage:
                ui.button(
                    "Создать доску заявок",
                    icon="add",
                    on_click=lambda: create_dialog.open(),
                ).classes("bg-indigo-600 text-white").props("unelevated")

        with ui.card().classes("w-full p-4 rounded-xl border border-gray-100 gap-2"):
            ui.label("Фильтры досок").classes("font-semibold text-gray-700")
            with ui.row().classes("w-full gap-3 flex-wrap items-end"):
                f_label = ui.select(
                    ["Все"] + BOARD_LABEL_OPTIONS,
                    value="Все",
                    label="Метка (тип устройств)",
                ).classes("w-56").props("outlined dense")
                
                db0 = SessionLocal()
                try:
                    master_opts = ["Все"] + [m.email for m in get_masters(db0)]
                finally:
                    db0.close()
                f_master = ui.select(
                    master_opts, value="Все", label="Email мастера"
                ).classes("w-64").props("outlined dense")

                def apply_f():
                    filters["label"] = f_label.value or "Все"
                    filters["master"] = f_master.value or "Все"
                    load_projects()

                def reset_f():
                    f_label.value = "Все"
                    f_master.value = "Все"
                    filters["label"] = "Все"
                    filters["master"] = "Все"
                    load_projects()

                ui.button("Применить", on_click=apply_f).classes(
                    "bg-indigo-600 text-white"
                ).props("unelevated dense")
                ui.button("Сбросить", on_click=reset_f).props("flat dense")

        projects_container = ui.column().classes("w-full gap-3")

        def load_projects():
            projects_container.clear()
            db = SessionLocal()
            try:
                if can_manage:
                    ensure_special_boards(db, user["id"])
                projects = get_user_projects(db, user["id"], user["role"])
                masters_map = {
                    m.id: m for m in db.query(User).filter(User.role.in_(["master", "admin"])).all()
                }

                # Фильтры
                if filters["label"] != "Все":
                    projects = [
                        p
                        for p in projects
                        if filters["label"] in (getattr(p, "labels", None) or "")
                    ]
                if filters["master"] != "Все":
                    projects = [
                        p
                        for p in projects
                        if p.master_id
                        and masters_map.get(p.master_id)
                        and masters_map[p.master_id].email == filters["master"]
                    ]

                if not projects:
                    with projects_container:
                        ui.label(
                            "Нет досок по выбранному фильтру (или админ ещё не создал доску заявок)."
                        ).classes("text-gray-500 text-lg py-12")
                    return

                type_badge = {
                    "ordinary": ("Заявки", "bg-sky-100 text-sky-800"),
                    "price": ("Прайс", "bg-indigo-100 text-indigo-800"),
                    "parts": ("Склад", "bg-amber-100 text-amber-800"),
                }

                for p in projects:
                    btype = getattr(p, "board_type", "ordinary") or "ordinary"
                    badge_text, badge_cls = type_badge.get(
                        btype, ("Доска", "bg-gray-100 text-gray-700")
                    )
                    master = masters_map.get(p.master_id) if p.master_id else None
                    labels = [
                        x.strip()
                        for x in (getattr(p, "labels", None) or "").split(",")
                        if x.strip()
                    ]

                    with projects_container:
                        with ui.card().classes(
                            "w-full p-4 hover:shadow-md transition-shadow rounded-xl border border-gray-100"
                        ):
                            with ui.row().classes(
                                "w-full items-center justify-between"
                            ):
                                with ui.column().classes("gap-1 cursor-pointer flex-1").on(
                                    "click",
                                    lambda e, pid=p.id: ui.navigate.to(f"/board/{pid}"),
                                ):
                                    with ui.row().classes("items-center gap-2 flex-wrap"):
                                        ui.label(p.name).classes(
                                            "text-lg font-semibold text-gray-800"
                                        )
                                        ui.badge(badge_text).classes(
                                            f"{badge_cls} text-xs"
                                        )
                                    if p.description:
                                        ui.label(p.description[:120]).classes(
                                            "text-sm text-gray-500"
                                        )
                                    with ui.row().classes("gap-1 flex-wrap"):
                                        for lab in labels:
                                            ui.badge(lab).classes(
                                                "bg-gray-100 text-gray-700 text-xs"
                                            )
                                    if master:
                                        ui.label(
                                            f"Мастер: {master.full_name or master.email}"
                                        ).classes("text-xs text-indigo-600")
                                with ui.row().classes("gap-1"):
                                    if can_manage and btype == "ordinary":
                                        ui.button(
                                            icon="edit",
                                            on_click=lambda e, proj=p: open_edit(proj),
                                        ).props("flat dense round")
                                        ui.button(
                                            icon="delete",
                                            on_click=lambda e, pid=p.id: do_delete(pid),
                                        ).props("flat dense round color=negative")
                                    ui.button(
                                        icon="chevron_right",
                                        on_click=lambda e, pid=p.id: ui.navigate.to(
                                            f"/board/{pid}"
                                        ),
                                    ).props("flat dense round")
            finally:
                db.close()

        def do_delete(project_id: int):
            #Удаляет доску и все связанные с ней данные
            db = SessionLocal()
            try:
                p = db.query(Project).filter(Project.id == project_id).first()
                if not p:
                    ui.notify("Доска не найдена", type="warning")
                    return
                if getattr(p, "board_type", "ordinary") != "ordinary":
                    ui.notify("Служебные доски удалять нельзя", type="warning")
                    return

                
                board_ids = [
                    b.id for b in db.query(Board).filter(Board.project_id == project_id).all()
                ]
                col_ids = []
                if board_ids:
                    col_ids = [
                        c.id
                        for c in db.query(BoardColumn)
                        .filter(BoardColumn.board_id.in_(board_ids))
                        .all()
                    ]
                card_ids = []
                if col_ids:
                    card_ids = [
                        c.id
                        for c in db.query(Card).filter(Card.column_id.in_(col_ids)).all()
                    ]

                
                if card_ids:
                    db.query(History).filter(History.card_id.in_(card_ids)).delete(
                        synchronize_session=False
                    )
                    db.query(Comment).filter(Comment.card_id.in_(card_ids)).delete(
                        synchronize_session=False
                    )
                    db.query(Card).filter(Card.id.in_(card_ids)).delete(
                        synchronize_session=False
                    )
                if col_ids:
                    db.query(BoardColumn).filter(BoardColumn.id.in_(col_ids)).delete(
                        synchronize_session=False
                    )
                if board_ids:
                    db.query(Board).filter(Board.id.in_(board_ids)).delete(
                        synchronize_session=False
                    )

                db.delete(p)
                db.commit()
                ui.notify("Доска и все заявки удалены", type="positive")
                load_projects()
            except Exception as ex:
                db.rollback()
                ui.notify(f"Ошибка удаления: {ex}", type="negative")
            finally:
                db.close()

        edit_state = {"id": None}
        with ui.dialog() as edit_dialog, ui.card().classes("w-96 p-6 gap-2"):
            ui.label("Редактировать доску").classes("text-xl font-bold mb-2")
            edit_name = ui.input("Название").classes("w-full").props("outlined dense")
            edit_desc = ui.textarea("Описание").classes("w-full").props("outlined dense")
            edit_labels = ui.select(
                BOARD_LABEL_OPTIONS,
                multiple=True,
                label="Метки устройств",
            ).classes("w-full").props("outlined dense")
            edit_master = ui.select(
                {}, value=None, label="Ответственный мастер"
            ).classes("w-full").props("outlined dense")

            def do_edit():
                if not edit_name.value or not edit_state["id"]:
                    return
                db = SessionLocal()
                try:
                    p = db.query(Project).filter(Project.id == edit_state["id"]).first()
                    if p:
                        p.name = edit_name.value.strip()
                        p.description = edit_desc.value or ""
                        labs = edit_labels.value or []
                        if isinstance(labs, str):
                            labs = [labs]
                        p.labels = ",".join(labs)
                        mid = edit_master.value
                        p.master_id = int(mid) if mid not in (None, "", "—") else None
                        db.commit()
                        ui.notify("Сохранено", type="positive")
                        edit_dialog.close()
                        load_projects()
                finally:
                    db.close()

            ui.button("Сохранить", on_click=do_edit).classes(
                "w-full mt-2 bg-indigo-600 text-white"
            ).props("unelevated")
            ui.button("Отмена", on_click=edit_dialog.close).classes(
                "w-full"
            ).props("flat")

        def open_edit(proj):
            edit_state["id"] = proj.id
            edit_name.value = proj.name
            edit_desc.value = proj.description or ""
            labs = [
                x.strip()
                for x in (getattr(proj, "labels", None) or "").split(",")
                if x.strip()
            ]
            edit_labels.value = labs
            db = SessionLocal()
            try:
                opts = {"—": "—"}
                opts.update(
                    {
                        str(m.id): f"{m.full_name or m.email} ({m.email})"
                        for m in get_masters(db)
                    }
                )
                edit_master.set_options(opts)
                edit_master.value = (
                    str(proj.master_id) if proj.master_id else "—"
                )
            finally:
                db.close()
            edit_dialog.open()

        load_projects()

        with ui.dialog() as create_dialog, ui.card().classes("w-96 p-6 gap-2"):
            ui.label("Новая доска заявок").classes("text-xl font-bold mb-2")
            name_in = ui.input("Название").classes("w-full").props("outlined dense")
            desc_in = ui.textarea("Описание").classes("w-full").props("outlined dense")
            labels_in = ui.select(
                BOARD_LABEL_OPTIONS,
                multiple=True,
                label="Метки устройств (можно несколько)",
            ).classes("w-full").props("outlined dense")
            master_in = ui.select(
                {"—": "—"}, value="—", label="Ответственный мастер"
            ).classes("w-full").props("outlined dense")

            def refresh_masters():
                db = SessionLocal()
                try:
                    opts = {"—": "—"}
                    opts.update(
                        {
                            str(m.id): f"{m.full_name or m.email} ({m.email})"
                            for m in get_masters(db)
                        }
                    )
                    master_in.set_options(opts)
                    master_in.value = "—"
                finally:
                    db.close()

            def do_create():
                if not name_in.value or not name_in.value.strip():
                    ui.notify("Введите название", type="negative")
                    return
                db = SessionLocal()
                try:
                    labs = labels_in.value or []
                    if isinstance(labs, str):
                        labs = [labs]
                    mid = master_in.value
                    master_id = int(mid) if mid not in (None, "", "—") else None
                    create_new_project(
                        db,
                        ProjectCreate(
                            name=name_in.value.strip(),
                            description=desc_in.value or "",
                        ),
                        user["id"],
                        labels=",".join(labs),
                        master_id=master_id,
                    )
                    ui.notify("Доска создана", type="positive")
                    create_dialog.close()
                    name_in.value = ""
                    desc_in.value = ""
                    labels_in.value = []
                    load_projects()
                except Exception as ex:
                    ui.notify(f"Ошибка: {ex}", type="negative")
                finally:
                    db.close()

            ui.button("Создать", on_click=do_create).classes(
                "w-full mt-2 bg-indigo-600 text-white"
            ).props("unelevated")
            ui.button("Отмена", on_click=create_dialog.close).classes(
                "w-full"
            ).props("flat")

            
            try:
                create_dialog.on("show", lambda: refresh_masters())
            except Exception:
                pass
            refresh_masters()
