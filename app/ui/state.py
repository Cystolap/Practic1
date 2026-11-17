from nicegui import app


def current_user() -> dict | None:
    return app.storage.user.get("user")


def set_user(user: dict):
    app.storage.user["user"] = user


def clear_user():
    app.storage.user.clear()
