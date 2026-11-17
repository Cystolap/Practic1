from nicegui import ui
from app.database import SessionLocal
from app.models import User
from app.auth import hash_password
from app.ui import state


@ui.page("/register")
def register_page():
    if state.current_user():
        ui.navigate.to("/projects")
        return

    ui.query("body").classes(
        "bg-gradient-to-br from-sky-100 via-indigo-50 to-purple-100 min-h-screen"
    )

    with ui.card().classes("absolute-center w-96 p-8 shadow-xl rounded-2xl"):
        ui.label("Регистрация").classes("text-2xl font-bold text-indigo-700 mb-2")
        ui.label("Ремонтная мастерская — кабинет клиента").classes(
            "text-sm text-gray-500 mb-6"
        )

        email = ui.input("Email").classes("w-full").props("outlined dense")
        password = ui.input(
            "Пароль", password=True, password_toggle_button=True
        ).classes("w-full").props("outlined dense")
        full_name = ui.input("ФИО (необязательно)").classes("w-full").props(
            "outlined dense"
        )
        phone = ui.input("Телефон (необязательно)").classes("w-full").props(
            "outlined dense"
        )

        ui.label(
            "Роль «Клиент» назначается автоматически. "
            "Мастеров и администраторов создаёт только администратор."
        ).classes("text-xs text-gray-400 mt-1")

        def do_register():
            if not email.value or not password.value:
                ui.notify("Заполните email и пароль", type="negative")
                return
            if len(password.value) < 6:
                ui.notify("Пароль минимум 6 символов", type="negative")
                return
            db = SessionLocal()
            try:
                if db.query(User).filter(User.email == email.value.strip()).first():
                    ui.notify("Email уже занят", type="negative")
                    return
                user = User(
                    email=email.value.strip(),
                    password_hash=hash_password(password.value),
                    role="client",
                    full_name=(full_name.value or "").strip(),
                    phone=(phone.value or "").strip(),
                )
                db.add(user)
                db.commit()
                ui.notify("Аккаунт клиента создан! Теперь войдите.", type="positive")
                ui.navigate.to("/login")
            finally:
                db.close()

        ui.button("Зарегистрироваться", on_click=do_register).classes(
            "w-full mt-4 bg-indigo-600 text-white"
        ).props("unelevated")
        ui.button(
            "Уже есть аккаунт", on_click=lambda: ui.navigate.to("/login")
        ).classes("w-full mt-2").props("flat")
