from datetime import datetime
from pathlib import Path
from nicegui import ui, app
from sqlalchemy.orm import joinedload

from app.database import SessionLocal
from app.models import Project, Board, BoardColumn, Card, User, Comment, History
from app.ui import state
from app.services.project_service import get_staff_emails, is_request_column

LABEL_COLORS = {
    "Смартфон": "bg-blue-500 text-white",
    "Ноутбук": "bg-indigo-500 text-white",
    "Планшет": "bg-violet-500 text-white",
    "ПК": "bg-slate-600 text-white",
    "Бытовая техника": "bg-amber-500 text-white",
    "Экран": "bg-red-400 text-white",
    "Батарея": "bg-orange-400 text-white",
    "ПО": "bg-emerald-500 text-white",
    "Срочно": "bg-rose-600 text-white",
}

COLUMN_HEADER_STYLES = {
    "Новая заявка": "bg-orange-100 text-orange-800 border-orange-200",
    "Заявка": "bg-orange-100 text-orange-800 border-orange-200",
    "Заявки": "bg-orange-100 text-orange-800 border-orange-200",
    "Принята": "bg-sky-100 text-sky-800 border-sky-200",
    "Диагностика": "bg-violet-100 text-violet-800 border-violet-200",
    "В ремонте": "bg-amber-50 text-amber-800 border-amber-200",
    "Готова к выдаче": "bg-emerald-50 text-emerald-800 border-emerald-200",
    "Выдана": "bg-green-100 text-green-800 border-green-200",
    "Отменена": "bg-slate-100 text-slate-700 border-slate-200",
    "Услуги": "bg-indigo-100 text-indigo-800 border-indigo-200",
    "Архив": "bg-slate-100 text-slate-600 border-slate-200",
    "В наличии": "bg-emerald-50 text-emerald-800 border-emerald-200",
    "Заканчивается": "bg-amber-50 text-amber-800 border-amber-200",
    "Нет в наличии": "bg-rose-50 text-rose-800 border-rose-200",
}

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


def _label_chip(label: str):
    cls = LABEL_COLORS.get(label.strip(), "bg-gray-200 text-gray-700")
    return ui.badge(label.strip()).classes(f"{cls} text-xs font-medium px-2 py-0.5 rounded-md")


@ui.page("/board/{project_id}")
def board_page(project_id: int):
    user = state.current_user()
    if not user:
        ui.navigate.to("/login")
        return

    role = user["role"]
    is_client = role == "client"
    is_staff = role in ("admin", "master")
    can_manage = is_staff

    ui.query("body").classes(
        "bg-gradient-to-b from-sky-100 via-blue-50 to-indigo-100 min-h-screen"
    )

    db = SessionLocal()
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        board = (
            db.query(Board)
            .options(joinedload(Board.columns).joinedload(BoardColumn.cards))
            .filter(Board.project_id == project_id)
            .first()
        )
        if not project or not board:
            ui.label("Проект или доска не найдены").classes("p-8 text-xl")
            return

        board_type = getattr(project, "board_type", "ordinary") or "ordinary"
        
        if is_client and board_type == "parts":
            ui.label("Склад доступен только мастерам и администратору").classes("p-8 text-xl")
            ui.button("Назад", on_click=lambda: ui.navigate.to("/projects"))
            return

        board_id = board.id
        project_name = project.name
        is_price = board_type == "price"
        is_special = board_type in ("price", "parts")
        
        client_readonly = is_client and is_price

        all_users = {u.id: u.email for u in db.query(User).all()}
        staff_emails = get_staff_emails(db)
        staff_map = {
            u.id: u.email
            for u in db.query(User).filter(User.role.in_(["master", "admin"])).all()
        }
    finally:
        db.close()

    filters = {"text": "", "priority": "Все", "assignee": "Все", "label": "Все"}
    pending_photo = {"path": ""}

    with ui.header().classes(
        "bg-white/90 backdrop-blur-md shadow-sm items-center px-4 py-2 gap-3 flex-wrap"
    ):
        ui.label("🔧 Ремонтная мастерская").classes("text-lg font-semibold text-indigo-700")
        ui.button("Доски", icon="view_column", on_click=lambda: ui.navigate.to("/projects")).props(
            "flat dense color=primary"
        )
        if is_client:
            ui.button("Мой кабинет", icon="person", on_click=lambda: ui.navigate.to("/cabinet")).props(
                "flat dense"
            )
        if role == "admin":
            ui.button(
                "Профили", icon="group", on_click=lambda: ui.navigate.to("/admin/users")
            ).props("flat dense")
        ui.space()
        search_input = ui.input(placeholder="Поиск").props("dense outlined").classes("w-44")
        ui.button(icon="filter_list", on_click=lambda: filter_dialog.open()).props(
            "flat dense round"
        ).tooltip("Фильтры")
        ui.button(
            icon="logout",
            on_click=lambda: (state.clear_user(), ui.navigate.to("/login")),
        ).props("flat dense round").tooltip("Выйти")

    with ui.row().classes("w-full items-center px-4 py-2 gap-3"):
        ui.button(icon="arrow_back", on_click=lambda: ui.navigate.to("/projects")).props(
            "flat dense round"
        )
        ui.label(project_name).classes("text-xl font-bold text-gray-800")
        if is_price and is_client:
            ui.badge("только просмотр").classes("bg-indigo-100 text-indigo-700")
        ui.space()
        if can_manage and not is_special:
            ui.button(
                "Добавить колонку", icon="add", on_click=lambda: add_col_dialog.open()
            ).props("flat dense").classes("text-indigo-600")

    with ui.dialog() as filter_dialog, ui.card().classes("w-80 p-4 gap-2"):
        ui.label("Фильтры").classes("text-lg font-bold")
        f_priority = ui.select(
            ["Все", "Низкий", "Средний", "Высокий"], value="Все", label="Приоритет"
        ).classes("w-full")
        f_assignee = ui.select(
            ["Все"] + staff_emails, value="Все", label="Исполнитель"
        ).classes("w-full")
        f_label = ui.select(
            ["Все", "Смартфон", "Ноутбук", "Планшет", "ПК", "Бытовая техника", "Экран", "Батарея", "ПО", "Срочно"],
            value="Все",
            label="Метка",
        ).classes("w-full")

        def apply_filters():
            filters["priority"] = f_priority.value
            filters["assignee"] = f_assignee.value
            filters["label"] = f_label.value
            board_area.refresh()
            filter_dialog.close()

        def reset_filters():
            f_priority.value = "Все"
            f_assignee.value = "Все"
            f_label.value = "Все"
            filters.update(priority="Все", assignee="Все", label="Все")
            board_area.refresh()
            filter_dialog.close()

        with ui.row().classes("w-full gap-2 mt-2"):
            ui.button("Применить", on_click=apply_filters).classes(
                "bg-indigo-600 text-white flex-1"
            ).props("unelevated")
            ui.button("Сбросить", on_click=reset_filters).props("flat")

    dlg = {"card_id": None, "column_id": None}

    with ui.dialog() as card_dialog, ui.card().classes("w-[34rem] max-w-[95vw] p-5 gap-3"):
        title_label = ui.label("Заявка").classes("text-xl font-bold")

        # Общие поля
        f_title = ui.input("Название").classes("w-full").props("outlined dense")
        f_desc = ui.textarea("Описание").classes("w-full").props("outlined dense")

        # Специальные поля для заявки на ремонт
        repair_fields = ui.column().classes("w-full gap-2")
        with repair_fields:
            f_deadline = ui.input("Желаемый дедлайн (ГГГГ-ММ-ДД)").classes("w-full").props(
                "outlined dense"
            )
            staff_fields = ui.column().classes("w-full gap-2")
            with staff_fields:
                with ui.row().classes("w-full gap-2"):
                    f_priority_card = ui.select(
                        ["Низкий", "Средний", "Высокий"], value="Средний", label="Приоритет"
                    ).classes("flex-1").props("outlined dense")
                    f_assignee_card = ui.select(
                        ["—"] + staff_emails, value="—", label="Исполнитель (мастер)"
                    ).classes("flex-1").props("outlined dense")
                f_labels = ui.input("Метки (Смартфон, Экран…)").classes("w-full").props(
                    "outlined dense"
                )
                f_price = ui.input("Стоимость (₽)").classes("w-full").props("outlined dense")
                f_master_notes = ui.textarea("Место мастера (заметки мастера)").classes(
                    "w-full"
                ).props("outlined dense")

        # Итоговая цена
        client_price_box = ui.column().classes("w-full gap-1")
        with client_price_box:
            f_client_price = ui.input("Итоговая стоимость (₽)").classes("w-full").props(
                "outlined dense readonly"
            )
            ui.label("Цену указывает мастер или администратор").classes(
                "text-xs text-gray-400"
            )

        # Информация о назначенном мастере (только чтение)
        master_info_box = ui.column().classes("w-full gap-1")
        with master_info_box:
            ui.label("Назначенный мастер").classes("text-sm font-medium text-gray-700")
            f_master_fio = ui.input("ФИО мастера").classes("w-full").props(
                "outlined dense readonly"
            )
            f_master_phone = ui.input("Телефон мастера").classes("w-full").props(
                "outlined dense readonly"
            )
            f_master_email = ui.input("Email мастера").classes("w-full").props(
                "outlined dense readonly"
            )

        # Прайс лист
        price_fields = ui.column().classes("w-full gap-2")
        with price_fields:
            f_service_price = ui.input("Цена услуги (₽)").classes("w-full").props(
                "outlined dense"
            )
            f_service_category = ui.input(
                "Категория (например: Экраны, ПО, Диагностика)"
            ).classes("w-full").props("outlined dense")

        # Склад запчастей
        parts_fields = ui.column().classes("w-full gap-2")
        with parts_fields:
            f_part_sku = ui.input("Артикул / SKU").classes("w-full").props("outlined dense")
            f_part_qty = ui.input("Количество на складе").classes("w-full").props(
                "outlined dense"
            )
            f_part_price = ui.input("Цена за единицу (₽)").classes("w-full").props(
                "outlined dense"
            )

        photo_block = ui.column().classes("w-full gap-1")
        with photo_block:
            photo_preview = ui.column().classes("w-full")
            ui.label("Фото устройства").classes("text-sm text-gray-600")

        async def on_upload(e):
            """NiceGUI может отдавать async read() — обязательно await."""
            try:
                data = None
                name = getattr(e, "name", None) or "photo.jpg"

                
                content = getattr(e, "content", None)
                if content is not None:
                    if hasattr(content, "read"):
                        raw = content.read()
                        if hasattr(raw, "__await__"):
                            raw = await raw
                        data = raw
                    elif isinstance(content, (bytes, bytearray, memoryview)):
                        data = bytes(content)

                
                if data is None:
                    fobj = getattr(e, "file", None)
                    if fobj is not None and hasattr(fobj, "read"):
                        raw = fobj.read()
                        if hasattr(raw, "__await__"):
                            raw = await raw
                        data = raw

                if not data:
                    ui.notify("Не удалось прочитать файл", type="negative")
                    return
                if isinstance(data, memoryview):
                    data = data.tobytes()
                if isinstance(data, str):
                    data = data.encode("latin-1")

                ext = Path(str(name)).suffix.lower() or ".jpg"
                if ext not in (".jpg", ".jpeg", ".png", ".webp", ".heic", ".gif"):
                    ui.notify("Только изображения (jpg, png, webp)", type="negative")
                    return

                fname = f"{user['id']}_{int(datetime.utcnow().timestamp())}{ext}"
                path = UPLOAD_DIR / fname
                path.write_bytes(data)
                pending_photo["path"] = f"/uploads/{fname}"
                photo_preview.clear()
                with photo_preview:
                    ui.image(pending_photo["path"]).classes(
                        "w-40 h-28 object-cover rounded border"
                    )
                ui.notify("Фото загружено", type="positive")
            except Exception as ex:
                ui.notify(f"Ошибка загрузки: {ex}", type="negative")

        upload_widget = ui.upload(
            on_upload=on_upload,
            auto_upload=True,
            max_files=1,
            label="Прикрепить фото",
        ).props('accept=".jpg,.jpeg,.png,.webp,image/*"').classes("w-full")

        comments_area = ui.column().classes("w-full gap-1 max-h-40 overflow-auto")

        def load_comments():
            comments_area.clear()
            if not dlg["card_id"]:
                return
            d = SessionLocal()
            try:
                comments = (
                    d.query(Comment)
                    .filter(Comment.card_id == dlg["card_id"])
                    .order_by(Comment.created_at.desc())
                    .all()
                )
                with comments_area:
                    if not comments:
                        ui.label("Комментариев нет").classes("text-sm text-gray-400")
                    for cm in comments:
                        author = all_users.get(cm.user_id, "?")
                        with ui.row().classes("items-start gap-2 text-sm"):
                            ui.label(f"{author}:").classes("font-medium text-indigo-600")
                            ui.label(cm.text).classes("text-gray-700")
            finally:
                d.close()

        def save_card():
            if client_readonly:
                ui.notify("Прайс-лист только для просмотра", type="warning")
                return
            if not f_title.value or not f_title.value.strip():
                ui.notify("Название обязательно", type="negative")
                return
            d = SessionLocal()
            try:
                
                assignee_id = None
                deadline = None
                price_val = None
                priority = "Средний"
                labels = ""
                master_notes = ""
                photo = pending_photo["path"] or ""

                if board_type == "price":
                    labels = (f_service_category.value or "").strip()
                    if f_service_price.value:
                        try:
                            price_val = float(str(f_service_price.value).replace(",", ".").strip())
                        except ValueError:
                            ui.notify("Цена — число", type="negative")
                            return
                elif board_type == "parts":
                    sku = (f_part_sku.value or "").strip()
                    qty = (f_part_qty.value or "").strip()
                    labels = f"SKU:{sku}" if sku else ""
                    if qty:
                        labels = (labels + f"; qty:{qty}").strip("; ")
                        priority = qty  
                    if f_part_price.value:
                        try:
                            price_val = float(str(f_part_price.value).replace(",", ".").strip())
                        except ValueError:
                            ui.notify("Цена — число", type="negative")
                            return
                else:
                    
                    if is_staff and f_assignee_card.value and f_assignee_card.value != "—":
                        for uid, em in staff_map.items():
                            if em == f_assignee_card.value:
                                assignee_id = uid
                                break
                    if f_deadline.value:
                        try:
                            deadline = datetime.strptime(f_deadline.value.strip(), "%Y-%m-%d")
                        except ValueError:
                            ui.notify("Дата в формате ГГГГ-ММ-ДД", type="negative")
                            return
                    if is_staff:
                        priority = f_priority_card.value or "Средний"
                        labels = f_labels.value or ""
                        master_notes = f_master_notes.value or ""
                        if f_price.value:
                            try:
                                price_val = float(str(f_price.value).replace(",", ".").strip())
                            except ValueError:
                                ui.notify("Стоимость — число", type="negative")
                                return

                if dlg["card_id"]:
                    c = d.query(Card).filter(Card.id == dlg["card_id"]).first()
                    if not c:
                        ui.notify("Карточка не найдена", type="negative")
                        return
                    if is_client and c.creator_id != user["id"]:
                        ui.notify("Нельзя редактировать чужую заявку", type="negative")
                        return
                    c.title = f_title.value.strip()
                    c.description = f_desc.value or ""
                    if board_type == "ordinary":
                        c.deadline = deadline
                        if photo:
                            c.photo_url = photo
                    if is_staff or board_type in ("price", "parts"):
                        c.priority = priority
                        c.assignee_id = assignee_id
                        c.labels = labels
                        c.master_notes = master_notes
                        c.estimated_price = price_val
                    d.add(History(card_id=c.id, user_id=user["id"], action=f"Обновлена: {c.title}"))
                else:
                    if is_client and board_type == "ordinary":
                        col = d.query(BoardColumn).filter(BoardColumn.id == dlg["column_id"]).first()
                        if not col or not is_request_column(col.name):
                            ui.notify(
                                "Клиент может создавать заявки только в колонке «Новая заявка» / «Заявки»",
                                type="negative",
                            )
                            return
                    max_pos = d.query(Card).filter(Card.column_id == dlg["column_id"]).count()
                    c = Card(
                        column_id=dlg["column_id"],
                        title=f_title.value.strip(),
                        description=f_desc.value or "",
                        priority=priority,
                        assignee_id=assignee_id,
                        creator_id=user["id"],
                        deadline=deadline,
                        labels=labels,
                        photo_url=photo if board_type == "ordinary" else "",
                        master_notes=master_notes,
                        estimated_price=price_val,
                        position=max_pos,
                    )
                    d.add(c)
                    d.flush()
                    d.add(History(card_id=c.id, user_id=user["id"], action=f"Создана: {c.title}"))
                d.commit()
                card_dialog.close()
                board_area.refresh()
                ui.notify("Сохранено", type="positive")
            except Exception as ex:
                ui.notify(f"Ошибка: {ex}", type="negative")
            finally:
                d.close()

        def add_comment():
            if not dlg["card_id"]:
                ui.notify("Сначала сохраните заявку", type="warning")
                return
            with ui.dialog() as cd, ui.card().classes("w-80 p-4"):
                ui.label("Комментарий").classes("font-bold")
                txt = ui.textarea().classes("w-full")

                def do():
                    if not txt.value or not txt.value.strip():
                        return
                    d = SessionLocal()
                    try:
                        d.add(
                            Comment(
                                card_id=dlg["card_id"],
                                user_id=user["id"],
                                text=txt.value.strip(),
                            )
                        )
                        d.commit()
                        cd.close()
                        load_comments()
                        ui.notify("Комментарий добавлен", type="positive")
                    finally:
                        d.close()

                ui.button("Отправить", on_click=do).classes(
                    "bg-indigo-600 text-white w-full mt-2"
                ).props("unelevated")
            cd.open()

        with ui.row().classes("w-full gap-2 mt-2"):
            if not client_readonly:
                ui.button("Сохранить", on_click=save_card).classes(
                    "bg-indigo-600 text-white flex-1"
                ).props("unelevated")
            if is_staff:
                ui.button("Комментарий", on_click=add_comment).props("flat")
            ui.button("Закрыть", on_click=card_dialog.close).props("flat")

    def configure_form_for_role():
        # Меняем набор полей под тип доски(Склад,Прайс,Обычные заявки)
        if board_type == "price":
            repair_fields.set_visibility(False)
            price_fields.set_visibility(True)
            parts_fields.set_visibility(False)
            photo_block.set_visibility(False)
            upload_widget.set_visibility(False)
            client_price_box.set_visibility(False)
            master_info_box.set_visibility(False)
            f_title.props('label="Название услуги"')
            f_desc.props('label="Описание услуги"')
        elif board_type == "parts":
            repair_fields.set_visibility(False)
            price_fields.set_visibility(False)
            parts_fields.set_visibility(True)
            photo_block.set_visibility(False)
            upload_widget.set_visibility(False)
            client_price_box.set_visibility(False)
            master_info_box.set_visibility(False)
            f_title.props('label="Название запчасти"')
            f_desc.props('label="Примечание"')
        else:
            repair_fields.set_visibility(True)
            price_fields.set_visibility(False)
            parts_fields.set_visibility(False)
            photo_block.set_visibility(True)
            client_price_box.set_visibility(True)
            master_info_box.set_visibility(True)
            f_title.props('label="Название"')
            f_desc.props('label="Описание неисправности"')
            if is_client:
                staff_fields.set_visibility(False)
                
                f_client_price.props("readonly")
                upload_widget.set_visibility(not client_readonly)
            else:
                staff_fields.set_visibility(True)
                
                upload_widget.set_visibility(True)

    def open_create_card(column_id: int, column_name: str):
        if client_readonly:
            ui.notify("Прайс-лист только для просмотра", type="warning")
            return
        if is_client and not is_request_column(column_name):
            ui.notify(
                "Создавать заявки можно только в колонке «Новая заявка» / «Заявки»",
                type="warning",
            )
            return
        if is_client and is_special:
            ui.notify("Нет доступа", type="negative")
            return

        dlg["card_id"] = None
        dlg["column_id"] = column_id
        pending_photo["path"] = ""
        if board_type == "price":
            title_label.set_text("Новая услуга")
        elif board_type == "parts":
            title_label.set_text("Новая запчасть")
        else:
            title_label.set_text("Новая заявка")
        f_title.value = ""
        f_desc.value = ""
        f_priority_card.value = "Средний"
        f_assignee_card.value = "—"
        f_deadline.value = ""
        f_labels.value = ""
        f_price.value = ""
        f_master_notes.value = ""
        f_client_price.value = ""
        f_master_fio.value = ""
        f_master_phone.value = ""
        f_master_email.value = ""
        f_service_price.value = ""
        f_service_category.value = ""
        f_part_sku.value = ""
        f_part_qty.value = ""
        f_part_price.value = ""
        photo_preview.clear()
        comments_area.clear()
        configure_form_for_role()
        card_dialog.open()

    def open_edit_card(card_id: int, column_id: int):
        dlg["card_id"] = card_id
        dlg["column_id"] = column_id
        pending_photo["path"] = ""
        d = SessionLocal()
        try:
            c = d.query(Card).filter(Card.id == card_id).first()
            if not c:
                return
            if board_type == "price":
                title_label.set_text("Услуга")
            elif board_type == "parts":
                title_label.set_text("Запчасть")
            else:
                title_label.set_text("Заявка")
            f_title.value = c.title or ""
            f_desc.value = c.description or ""
            f_priority_card.value = c.priority or "Средний"
            f_assignee_card.value = (
                staff_map.get(c.assignee_id, "—") if c.assignee_id else "—"
            )
            f_deadline.value = c.deadline.strftime("%Y-%m-%d") if c.deadline else ""
            f_labels.value = c.labels or ""
            f_price.value = str(c.estimated_price) if c.estimated_price is not None else ""
            f_master_notes.value = c.master_notes or ""
            f_client_price.value = (
                str(c.estimated_price) if c.estimated_price is not None else "ещё не указана"
            )
            # Данные мастера
            f_master_fio.value = ""
            f_master_phone.value = ""
            f_master_email.value = ""
            if c.assignee_id:
                mu = d.query(User).filter(User.id == c.assignee_id).first()
                if mu:
                    f_master_fio.value = mu.full_name or "—"
                    f_master_phone.value = mu.phone or "—"
                    f_master_email.value = mu.email or "—"
            # Прайс
            f_service_price.value = str(c.estimated_price) if c.estimated_price is not None else ""
            f_service_category.value = c.labels or ""
            # Склад
            labels = c.labels or ""
            sku = ""
            qty = c.priority if c.priority and c.priority not in ("Низкий", "Средний", "Высокий") else ""
            if "SKU:" in labels:
                for part in labels.split(";"):
                    part = part.strip()
                    if part.startswith("SKU:"):
                        sku = part[4:].strip()
                    if part.startswith("qty:"):
                        qty = part[4:].strip()
            f_part_sku.value = sku
            f_part_qty.value = qty
            f_part_price.value = str(c.estimated_price) if c.estimated_price is not None else ""
            photo_preview.clear()
            if c.photo_url:
                with photo_preview:
                    ui.image(c.photo_url).classes("w-40 h-28 object-cover rounded border")
            load_comments()
            configure_form_for_role()
            card_dialog.open()
        finally:
            d.close()

    def move_card(card_id: int, target_column_id: int):
        if is_client:
            ui.notify("Переносить заявки могут только мастер и администратор", type="warning")
            return
        d = SessionLocal()
        try:
            c = d.query(Card).filter(Card.id == card_id).first()
            if c:
                c.column_id = target_column_id
                d.add(
                    History(card_id=c.id, user_id=user["id"], action="Смена статуса")
                )
                d.commit()
                board_area.refresh()
                ui.notify("Статус изменён", type="positive")
        finally:
            d.close()

    def delete_card(card_id: int):
        if is_client:
            ui.notify("Удалять заявки могут только мастер и администратор", type="warning")
            return
        d = SessionLocal()
        try:
            d.query(Comment).filter(Comment.card_id == card_id).delete(
                synchronize_session=False
            )
            d.query(History).filter(History.card_id == card_id).delete(
                synchronize_session=False
            )
            d.query(Card).filter(Card.id == card_id).delete(synchronize_session=False)
            d.commit()
            board_area.refresh()
            ui.notify("Карточка удалена", type="positive")
        except Exception as ex:
            d.rollback()
            ui.notify(f"Ошибка удаления: {ex}", type="negative")
        finally:
            d.close()

    with ui.dialog() as add_col_dialog, ui.card().classes("w-80 p-4"):
        ui.label("Новая колонка").classes("text-lg font-bold")
        col_name_in = ui.input("Название").classes("w-full").props("outlined dense")

        def do_add_col():
            if not col_name_in.value or not col_name_in.value.strip():
                return
            d = SessionLocal()
            try:
                pos = d.query(BoardColumn).filter(BoardColumn.board_id == board_id).count()
                d.add(
                    BoardColumn(
                        board_id=board_id,
                        name=col_name_in.value.strip(),
                        position=pos,
                    )
                )
                d.commit()
                add_col_dialog.close()
                board_area.refresh()
            finally:
                d.close()

        ui.button("Создать", on_click=do_add_col).classes(
            "w-full mt-3 bg-indigo-600 text-white"
        ).props("unelevated")

    def move_column(col_id: int, direction: int):
        if not can_manage:
            return
        d = SessionLocal()
        try:
            cols = (
                d.query(BoardColumn)
                .filter(BoardColumn.board_id == board_id)
                .order_by(BoardColumn.position)
                .all()
            )
            idx = next((i for i, c in enumerate(cols) if c.id == col_id), None)
            if idx is None:
                return
            new_idx = idx + direction
            if new_idx < 0 or new_idx >= len(cols):
                return
            cols[idx].position, cols[new_idx].position = (
                cols[new_idx].position,
                cols[idx].position,
            )
            d.commit()
            board_area.refresh()
        finally:
            d.close()

    def open_edit_column(col_id: int, name: str, wip):
        with ui.dialog() as ed, ui.card().classes("w-80 p-4"):
            ui.label("Колонка").classes("font-bold")
            n = ui.input("Название", value=name).classes("w-full")

            def save():
                d = SessionLocal()
                try:
                    col = d.query(BoardColumn).filter(BoardColumn.id == col_id).first()
                    if col and n.value:
                        col.name = n.value.strip()
                        d.commit()
                        ed.close()
                        board_area.refresh()
                finally:
                    d.close()

            ui.button("Сохранить", on_click=save).classes(
                "w-full mt-2 bg-indigo-600 text-white"
            ).props("unelevated")
        ed.open()

    @ui.refreshable
    def board_area():
        d = SessionLocal()
        try:
            board_obj = (
                d.query(Board)
                .options(joinedload(Board.columns).joinedload(BoardColumn.cards))
                .filter(Board.id == board_id)
                .first()
            )
            if not board_obj:
                return
            cols = sorted(board_obj.columns, key=lambda c: c.position)
            users_map = all_users
            q = (search_input.value or "").strip().lower()

            with ui.row().classes(
                "w-full overflow-x-auto px-4 pb-8 gap-3 items-start flex-nowrap"
            ):
                for col in cols:
                    cards = sorted(col.cards, key=lambda c: c.position)
                    if filters["priority"] != "Все":
                        cards = [c for c in cards if c.priority == filters["priority"]]
                    if filters["assignee"] != "Все":
                        cards = [
                            c
                            for c in cards
                            if c.assignee_id
                            and users_map.get(c.assignee_id) == filters["assignee"]
                        ]
                    if filters["label"] != "Все":
                        cards = [
                            c for c in cards if filters["label"] in (c.labels or "")
                        ]
                    if q:
                        cards = [
                            c
                            for c in cards
                            if q in (c.title or "").lower()
                            or q in (c.description or "").lower()
                        ]

                    header_cls = COLUMN_HEADER_STYLES.get(
                        col.name, "bg-white text-gray-700 border-gray-200"
                    )
                    
                    if is_request_column(col.name) and col.name not in COLUMN_HEADER_STYLES:
                        header_cls = "bg-orange-100 text-orange-800 border-orange-200"

                    with ui.column().classes(
                        "w-72 min-w-[18rem] bg-white/70 rounded-xl shadow-sm border border-gray-100"
                    ):
                        with ui.row().classes(
                            f"w-full items-center justify-between px-2 py-2 rounded-t-xl border-b {header_cls}"
                        ):
                            with ui.row().classes("items-center gap-1"):
                                ui.label(col.name).classes("font-semibold text-sm")
                                ui.badge(str(len(cards))).classes(
                                    "bg-white/80 text-gray-700 text-xs"
                                )
                            with ui.row().classes("gap-0"):
                                if can_manage:
                                    ui.button(
                                        icon="chevron_left",
                                        on_click=lambda cid=col.id: move_column(cid, -1),
                                    ).props("flat dense round size=xs")
                                    ui.button(
                                        icon="chevron_right",
                                        on_click=lambda cid=col.id: move_column(cid, 1),
                                    ).props("flat dense round size=xs")
                                    ui.button(
                                        icon="edit",
                                        on_click=lambda cid=col.id, n=col.name, w=col.wip_limit: open_edit_column(
                                            cid, n, w
                                        ),
                                    ).props("flat dense round size=xs")

                                
                                can_add = False
                                if is_staff:
                                    can_add = True
                                elif is_client and not client_readonly and is_request_column(col.name):
                                    can_add = True

                                if can_add:
                                    ui.button(
                                        icon="add",
                                        on_click=lambda cid=col.id, cn=col.name: open_create_card(
                                            cid, cn
                                        ),
                                    ).props("flat dense round size=sm")

                        with ui.column().classes("w-full p-2 gap-2 min-h-[120px]"):
                            for card in cards:
                                with ui.card().classes(
                                    "w-full p-3 cursor-pointer hover:shadow-md transition-shadow rounded-lg border border-gray-100 bg-white gap-1"
                                ).on(
                                    "click",
                                    lambda e, cid=card.id, colid=col.id: open_edit_card(
                                        cid, colid
                                    ),
                                ):
                                    if card.labels:
                                        with ui.row().classes("gap-1 flex-wrap"):
                                            for lab in (card.labels or "").split(","):
                                                lab = lab.strip()
                                                if lab:
                                                    _label_chip(lab)
                                    ui.label(card.title).classes(
                                        "font-medium text-gray-800 text-sm leading-snug"
                                    )
                                    if card.description:
                                        desc = card.description
                                        ui.label(
                                            (desc[:80] + "…") if len(desc) > 80 else desc
                                        ).classes("text-xs text-gray-500")
                                    if card.photo_url:
                                        ui.image(card.photo_url).classes(
                                            "w-full h-20 object-cover rounded mt-1"
                                        )
                                    with ui.row().classes(
                                        "w-full items-center justify-between mt-1 text-xs text-gray-400"
                                    ):
                                        meta = []
                                        if card.deadline:
                                            meta.append(
                                                "до " + card.deadline.strftime("%d.%m")
                                            )
                                        if is_staff and card.priority:
                                            meta.append(card.priority)
                                        if card.assignee_id and card.assignee_id in staff_map:
                                            meta.append(
                                                staff_map[card.assignee_id].split("@")[0]
                                            )
                                        if is_staff and card.estimated_price is not None:
                                            meta.append(f"{card.estimated_price} ₽")
                                        ui.label(" · ".join(meta) if meta else "")
                                        if is_staff:
                                            with ui.row().classes("gap-0"):
                                                other_cols = [
                                                    c for c in cols if c.id != col.id
                                                ]
                                                if other_cols:
                                                    with ui.button(
                                                        icon="drive_file_move"
                                                    ).props("flat dense round size=xs"):
                                                        with ui.menu():
                                                            for oc in other_cols:
                                                                ui.menu_item(
                                                                    oc.name,
                                                                    on_click=lambda ocid=oc.id, cid=card.id: move_card(
                                                                        cid, ocid
                                                                    ),
                                                                )
                                                ui.button(
                                                    icon="delete",
                                                    on_click=lambda cid=card.id: delete_card(
                                                        cid
                                                    ),
                                                ).props(
                                                    "flat dense round size=xs color=negative"
                                                )
                            if not cards:
                                ui.label("Нет заявок").classes(
                                    "text-xs text-gray-400 text-center py-4 w-full"
                                )
        finally:
            d.close()

    board_area()
    search_input.on("update:model-value", lambda: board_area.refresh())
