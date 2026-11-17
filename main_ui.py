"""
Kanban доска-Ремонтная мастерская
Откроется http://localhost:8080
"""
from pathlib import Path
from nicegui import ui, app
from app.database import Base, engine, migrate_schema, ensure_default_admin
from app import models

Base.metadata.create_all(bind=engine)
migrate_schema()
ensure_default_admin()

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
app.add_static_files("/uploads", str(UPLOAD_DIR.resolve()))

from app.ui import login, register, projects, board, cabinet, admin_users


@ui.page("/")
def index():
    from app.ui import state
    if state.current_user():
        ui.navigate.to("/projects")
    else:
        ui.navigate.to("/login")


ui.run(
    title="Ремонтная мастерская — Kanban",
    host="127.0.0.1",
    port=8080,
    reload=True,
    storage_secret="repair-workshop-secret-change-in-prod",
    favicon="🔧",
)
