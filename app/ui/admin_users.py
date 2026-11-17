
from datetime import datetime, timedelta
from nicegui import ui
from sqlalchemy import func
from app.database import SessionLocal
from app.models import User, Card, Project, History, Comment
from app.ui import state
from app.auth import hash_password


@ui.page("/admin/users")
def admin_users_page():
    user = state.current_user()
    if not user:
        ui.navigate.to("/login")
        return
    if user["role"] != "admin":
        ui.label("Доступ только для администратора").classes("p-8 text-xl")
        ui.button("Назад", on_click=lambda: ui.navigate.to("/projects"))
        return

    ui.query("body").classes(
        "bg-gradient-to-br from-sky-50 via-blue-50 to-indigo-50 min-h-screen"
    )

    with ui.header().classes(
        "bg-white/90 backdrop-blur shadow-sm items-center px-6 py-3 gap-2"
    ):
        ui.label("🔧 Ремонтная мастерская").classes("text-xl font-bold text-indigo-700")
        ui.space()
        ui.label(f"{user['email']} (admin)").classes("text-sm text-gray-600")
        ui.button("Доски", on_click=lambda: ui.navigate.to("/projects")).props("flat dense")
        ui.button(
            "Выйти",
            on_click=lambda: (state.clear_user(), ui.navigate.to("/login")),
        ).props("flat dense")

    with ui.column().classes("w-full max-w-5xl mx-auto p-6 gap-6"):
        ui.label("Панель администратора").classes("text-2xl font-bold text-gray-800")

        # Статистика на админ панели
        stats_box = ui.column().classes("w-full gap-3")

        def load_stats():
            stats_box.clear()
            db = SessionLocal()
            try:
                total_users = db.query(User).count()
                n_client = db.query(User).filter(User.role == "client").count()
                n_master = db.query(User).filter(User.role == "master").count()
                n_admin = db.query(User).filter(User.role == "admin").count()
                total_cards = db.query(Card).count()
                total_projects = db.query(Project).count()
                total_comments = db.query(Comment).count()

                
                now = datetime.utcnow()
                day_ago = now - timedelta(hours=24)
                week_ago = now - timedelta(days=7)
                hist_24 = (
                    db.query(History).filter(History.created_at >= day_ago).count()
                )
                hist_7 = (
                    db.query(History).filter(History.created_at >= week_ago).count()
                )

                # Активные пользователи
                active_ids = [
                    r[0]
                    for r in db.query(History.user_id)
                    .filter(History.created_at >= day_ago)
                    .distinct()
                    .all()
                ]
                active_users = []
                if active_ids:
                    active_users = (
                        db.query(User).filter(User.id.in_(active_ids)).all()
                    )

                # Последние действия
                recent = (
                    db.query(History)
                    .order_by(History.created_at.desc())
                    .limit(8)
                    .all()
                )
                users_map = {u.id: u for u in db.query(User).all()}

                with stats_box:
                    ui.label("Статистика приложения").classes(
                        "text-lg font-semibold text-gray-700"
                    )
                    with ui.row().classes("w-full gap-3 flex-wrap"):
                        def metric(title, value, color="bg-white"):
                            with ui.card().classes(
                                f"p-4 min-w-[9rem] rounded-xl border border-gray-100 {color}"
                            ):
                                ui.label(str(value)).classes(
                                    "text-2xl font-bold text-gray-800"
                                )
                                ui.label(title).classes("text-xs text-gray-500")

                        metric("Всего пользователей", total_users, "bg-indigo-50")
                        metric("Клиенты", n_client, "bg-sky-50")
                        metric("Мастера", n_master, "bg-violet-50")
                        metric("Админы", n_admin, "bg-rose-50")
                        metric("Заявок / карточек", total_cards, "bg-emerald-50")
                        metric("Досок", total_projects, "bg-amber-50")
                        metric("Действий за 24ч", hist_24, "bg-orange-50")
                        metric("Действий за 7 дней", hist_7, "bg-slate-50")

                    with ui.row().classes("w-full gap-4 flex-wrap mt-2"):
                        with ui.card().classes(
                            "p-4 flex-1 min-w-[16rem] rounded-xl border border-gray-100"
                        ):
                            ui.label("Активны за последние 24 часа").classes(
                                "font-semibold text-gray-700 mb-2"
                            )
                            if not active_users:
                                ui.label("Пока нет активности").classes(
                                    "text-sm text-gray-400"
                                )
                            else:
                                for u in active_users:
                                    role_ru = {
                                        "client": "клиент",
                                        "master": "мастер",
                                        "admin": "админ",
                                    }.get(u.role, u.role)
                                    ui.label(f"• {u.email} ({role_ru})").classes(
                                        "text-sm text-gray-700"
                                    )

                        with ui.card().classes(
                            "p-4 flex-1 min-w-[16rem] rounded-xl border border-gray-100"
                        ):
                            ui.label("Последние действия").classes(
                                "font-semibold text-gray-700 mb-2"
                            )
                            if not recent:
                                ui.label("Пусто").classes("text-sm text-gray-400")
                            else:
                                for h in recent:
                                    u = users_map.get(h.user_id)
                                    email = u.email if u else f"id:{h.user_id}"
                                    ts = (
                                        h.created_at.strftime("%d.%m %H:%M")
                                        if h.created_at
                                        else "—"
                                    )
                                    ui.label(
                                        f"{ts} — {email}: {h.action[:60]}"
                                    ).classes("text-xs text-gray-600")
            finally:
                db.close()

        load_stats()
        ui.button("Обновить статистику", icon="refresh", on_click=load_stats).props(
            "flat"
        ).classes("text-indigo-600")

        ui.separator()

        # Профили
        with ui.row().classes("w-full items-center justify-between"):
            ui.label("Профили пользователей").classes(
                "text-lg font-semibold text-gray-700"
            )
            ui.button(
                "Добавить пользователя",
                icon="person_add",
                on_click=lambda: create_dialog.open(),
            ).classes("bg-indigo-600 text-white").props("unelevated")

        table_area = ui.column().classes("w-full gap-2")

        def load():
            table_area.clear()
            db = SessionLocal()
            try:
                users = db.query(User).order_by(User.id).all()
                role_badge = {
                    "admin": "bg-rose-100 text-rose-800",
                    "master": "bg-indigo-100 text-indigo-800",
                    "client": "bg-sky-100 text-sky-800",
                }
                role_label = {
                    "admin": "Администратор",
                    "master": "Мастер",
                    "client": "Клиент",
                }
                with table_area:
                    if not users:
                        ui.label("Пользователей пока нет").classes("text-gray-500 py-6")
                        return
                    for u in users:
                        with ui.card().classes(
                            "w-full p-4 rounded-xl border border-gray-100"
                        ):
                            with ui.row().classes(
                                "w-full items-center justify-between gap-3 flex-wrap"
                            ):
                                with ui.column().classes("gap-0"):
                                    ui.label(u.email).classes(
                                        "font-semibold text-gray-800"
                                    )
                                    fio = getattr(u, "full_name", "") or ""
                                    phone = getattr(u, "phone", "") or ""
                                    extra = " · ".join(x for x in [fio, phone] if x)
                                    if extra:
                                        ui.label(extra).classes("text-sm text-gray-600")
                                    ui.label(f"ID: {u.id}").classes(
                                        "text-xs text-gray-400"
                                    )
                                ui.badge(role_label.get(u.role, u.role)).classes(
                                    f"{role_badge.get(u.role, 'bg-gray-100')} text-sm px-3"
                                )
                                with ui.row().classes("gap-1"):
                                    ui.button(
                                        "Профиль",
                                        icon="badge",
                                        on_click=lambda e, uid=u.id: open_profile(uid),
                                    ).props("flat dense")
                                    ui.button(
                                        "Роль",
                                        icon="edit",
                                        on_click=lambda e, uid=u.id, r=u.role: open_role(
                                            uid, r
                                        ),
                                    ).props("flat dense")
                                    ui.button(
                                        "Пароль",
                                        icon="lock",
                                        on_click=lambda e, uid=u.id: open_password(uid),
                                    ).props("flat dense")
                                    if u.id != user["id"]:
                                        ui.button(
                                            icon="delete",
                                            on_click=lambda e, uid=u.id: do_delete(uid),
                                        ).props("flat dense round color=negative")
            finally:
                db.close()

        def do_delete(uid: int):
            db = SessionLocal()
            try:
                u = db.query(User).filter(User.id == uid).first()
                if u:
                    db.delete(u)
                    db.commit()
                    ui.notify("Пользователь удалён", type="positive")
                    load()
                    load_stats()
            except Exception as ex:
                ui.notify(f"Ошибка: {ex}", type="negative")
            finally:
                db.close()

        def open_profile(uid: int):
            db = SessionLocal()
            try:
                u = db.query(User).filter(User.id == uid).first()
                if not u:
                    return
                cur_fio = u.full_name or ""
                cur_phone = u.phone or ""
            finally:
                db.close()
            with ui.dialog() as dlg, ui.card().classes("w-80 p-4 gap-2"):
                ui.label("Профиль пользователя").classes("font-bold mb-1")
                fio = ui.input("ФИО", value=cur_fio).classes("w-full").props("outlined dense")
                phone = ui.input("Телефон", value=cur_phone).classes("w-full").props(
                    "outlined dense"
                )

                def save():
                    db = SessionLocal()
                    try:
                        u = db.query(User).filter(User.id == uid).first()
                        if u:
                            u.full_name = (fio.value or "").strip()
                            u.phone = (phone.value or "").strip()
                            db.commit()
                            ui.notify("Профиль сохранён", type="positive")
                            dlg.close()
                            load()
                    finally:
                        db.close()

                ui.button("Сохранить", on_click=save).classes(
                    "w-full mt-2 bg-indigo-600 text-white"
                ).props("unelevated")
            dlg.open()

        def open_role(uid: int, current: str):
            with ui.dialog() as dlg, ui.card().classes("w-80 p-4"):
                ui.label("Сменить роль").classes("font-bold mb-2")
                sel = ui.select(
                    {
                        "client": "Клиент",
                        "master": "Мастер",
                        "admin": "Администратор",
                    },
                    value=current if current in ("client", "master", "admin") else "client",
                    label="Роль",
                ).classes("w-full")

                def save():
                    db = SessionLocal()
                    try:
                        u = db.query(User).filter(User.id == uid).first()
                        if u:
                            u.role = sel.value
                            db.commit()
                            ui.notify("Роль обновлена", type="positive")
                            dlg.close()
                            load()
                            load_stats()
                    finally:
                        db.close()

                ui.button("Сохранить", on_click=save).classes(
                    "w-full mt-3 bg-indigo-600 text-white"
                ).props("unelevated")
            dlg.open()

        def open_password(uid: int):
            with ui.dialog() as dlg, ui.card().classes("w-80 p-4"):
                ui.label("Новый пароль").classes("font-bold mb-2")
                pwd = ui.input(
                    "Пароль", password=True, password_toggle_button=True
                ).classes("w-full")

                def save():
                    if not pwd.value or len(pwd.value) < 6:
                        ui.notify("Минимум 6 символов", type="negative")
                        return
                    db = SessionLocal()
                    try:
                        u = db.query(User).filter(User.id == uid).first()
                        if u:
                            u.password_hash = hash_password(pwd.value)
                            db.commit()
                            ui.notify("Пароль обновлён", type="positive")
                            dlg.close()
                    finally:
                        db.close()

                ui.button("Сохранить", on_click=save).classes(
                    "w-full mt-3 bg-indigo-600 text-white"
                ).props("unelevated")
            dlg.open()

        with ui.dialog() as create_dialog, ui.card().classes("w-96 p-5 gap-2"):
            ui.label("Новый пользователь").classes("text-xl font-bold")
            email_in = ui.input("Email").classes("w-full").props("outlined dense")
            pwd_in = ui.input(
                "Пароль", password=True, password_toggle_button=True
            ).classes("w-full").props("outlined dense")
            fio_in = ui.input("ФИО").classes("w-full").props("outlined dense")
            phone_in = ui.input("Телефон").classes("w-full").props("outlined dense")
            role_in = ui.select(
                {
                    "client": "Клиент",
                    "master": "Мастер",
                    "admin": "Администратор",
                },
                value="master",
                label="Роль",
            ).classes("w-full").props("outlined dense")
            ui.label(
                "Для мастера заполните ФИО и телефон — клиент увидит их в заявке."
            ).classes("text-xs text-gray-400")

            def do_create():
                if not email_in.value or not pwd_in.value:
                    ui.notify("Заполните email и пароль", type="negative")
                    return
                if len(pwd_in.value) < 6:
                    ui.notify("Пароль минимум 6 символов", type="negative")
                    return
                db = SessionLocal()
                try:
                    if (
                        db.query(User)
                        .filter(User.email == email_in.value.strip())
                        .first()
                    ):
                        ui.notify("Email уже занят", type="negative")
                        return
                    db.add(
                        User(
                            email=email_in.value.strip(),
                            password_hash=hash_password(pwd_in.value),
                            role=role_in.value,
                            full_name=(fio_in.value or "").strip(),
                            phone=(phone_in.value or "").strip(),
                        )
                    )
                    db.commit()
                    ui.notify("Пользователь создан", type="positive")
                    create_dialog.close()
                    email_in.value = ""
                    pwd_in.value = ""
                    fio_in.value = ""
                    phone_in.value = ""
                    load()
                    load_stats()
                except Exception as ex:
                    ui.notify(f"Ошибка: {ex}", type="negative")
                finally:
                    db.close()

            ui.button("Создать", on_click=do_create).classes(
                "w-full mt-2 bg-indigo-600 text-white"
            ).props("unelevated")

        load()
