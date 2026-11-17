from nicegui import ui
from app.database import SessionLocal
from app.models import User
from app.auth import verify_password
from app.ui import state


@ui.page("/login")
def login_page():
    if state.current_user():
        ui.navigate.to("/projects")
        return

    ui.query("body").classes("bg-gradient-to-br from-sky-100 via-indigo-50 to-purple-100 min-h-screen")

    with ui.card().classes("absolute-center w-96 p-8 shadow-xl rounded-2xl"):
        ui.label("🔧 Ремонтная мастерская").classes("text-2xl font-bold text-indigo-700 mb-1")
        ui.label("Вход в систему").classes("text-lg text-gray-600 mb-6")

        email = ui.input("Email").classes("w-full").props("outlined dense")
        password = ui.input("Пароль", password=True, password_toggle_button=True).classes("w-full").props("outlined dense")

        def do_login():
            if not email.value or not password.value:
                ui.notify("Заполните email и пароль", type="negative")
                return
            db = SessionLocal()
            try:
                user = db.query(User).filter(User.email == email.value.strip()).first()
                if not user or not verify_password(password.value, user.password_hash):
                    ui.notify("Неверный email или пароль", type="negative")
                    return
                state.set_user({"id": user.id, "email": user.email, "role": user.role})
                ui.notify(f"Добро пожаловать, {user.email}!", type="positive")
                ui.navigate.to("/projects")
            finally:
                db.close()

        ui.button("Войти", on_click=do_login).classes("w-full mt-4 bg-indigo-600 text-white").props("unelevated")
        ui.button("Регистрация", on_click=lambda: ui.navigate.to("/register")).classes("w-full mt-2").props("flat")
