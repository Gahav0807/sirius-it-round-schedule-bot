import aiosqlite
import logging
from datetime import datetime, timedelta
import zoneinfo
from config import DB_NAME
from typing import List, Tuple, Optional

# Инициализация базы данных (user_settings: добавлено remind_before)
async def init_db() -> None:
    """
    Инициализирует базу данных и необходимые таблицы.
    """
    try:
        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    title TEXT,
                    date TEXT,
                    time TEXT,
                    tag TEXT DEFAULT ''
                )
                """
            )
            try:
                await db.execute("ALTER TABLE events ADD COLUMN tag TEXT DEFAULT ''")
            except Exception:
                pass
            # user_settings с remind_before
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS user_settings (
                    user_id INTEGER PRIMARY KEY,
                    notifications_enabled INTEGER DEFAULT 1,
                    remind_before INTEGER DEFAULT 60
                )
                """
            )
            try:
                await db.execute("ALTER TABLE user_settings ADD COLUMN remind_before INTEGER DEFAULT 60")
            except Exception:
                pass
            await db.commit()
        logging.info("База данных инициализирована.")
    except Exception as e:
        logging.error(f"Ошибка инициализации базы данных: {e}")

# Включить/отключить напоминания для пользователя
async def set_notifications_enabled(user_id: int, enabled: bool) -> None:
    """
    Включает или отключает напоминания для пользователя.
    """
    try:
        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute(
                "INSERT INTO user_settings (user_id, notifications_enabled) VALUES (?, ?) "
                "ON CONFLICT(user_id) DO UPDATE SET notifications_enabled=excluded.notifications_enabled",
                (user_id, int(enabled))
            )
            await db.commit()
    except Exception as e:
        logging.error(f"Ошибка обновления статуса напоминаний: {e}")

# Получить статус напоминаний пользователя
async def get_notifications_enabled(user_id: int) -> bool:
    """
    Получает статус напоминаний пользователя.
    """
    try:
        async with aiosqlite.connect(DB_NAME) as db:
            cursor = await db.execute(
                "SELECT notifications_enabled FROM user_settings WHERE user_id=?",
                (user_id,)
            )
            row = await cursor.fetchone()
            return bool(row[0]) if row else True  # По умолчанию True
    except Exception as e:
        logging.error(f"Ошибка получения статуса напоминаний: {e}")
        return True

# Установить время напоминания (в минутах)
async def set_remind_before(user_id: int, minutes: int) -> None:
    """
    Устанавливает время напоминания (в минутах) для пользователя.
    """
    try:
        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute(
                "INSERT INTO user_settings (user_id, remind_before) VALUES (?, ?) "
                "ON CONFLICT(user_id) DO UPDATE SET remind_before=excluded.remind_before",
                (user_id, minutes)
            )
            await db.commit()
    except Exception as e:
        logging.error(f"Ошибка обновления времени напоминания: {e}")

# Получить время напоминания пользователя (в минутах)
async def get_remind_before(user_id: int) -> int:
    """
    Получает время напоминания пользователя (в минутах).
    """
    try:
        async with aiosqlite.connect(DB_NAME) as db:
            cursor = await db.execute(
                "SELECT remind_before FROM user_settings WHERE user_id=?",
                (user_id,)
            )
            row = await cursor.fetchone()
            return int(row[0]) if row and row[0] is not None else 60
    except Exception as e:
        logging.error(f"Ошибка получения времени напоминания: {e}")
        return 60

# Добавить событие в базу (с поддержкой тега)
async def add_event(user_id: int, title: str, date: str, time: str, tag: str = "") -> None:
    """
    Добавляет событие в базу данных.
    """
    try:
        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute(
                "INSERT INTO events (user_id, title, date, time, tag) VALUES (?, ?, ?, ?, ?)",
                (user_id, title, date, time, tag)
            )
            await db.commit()
    except Exception as e:
        logging.error(f"Ошибка добавления события: {e}")

# Получить события, пользователей которых надо напомнить о них (гибко по remind_before)
async def get_events_for_reminder() -> List[Tuple[int, int, str]]:
    """
    Получает события, по которым нужно отправить напоминание (только один раз).
    Возвращает: (user_id, event_id, title)
    """
    try:
        now = datetime.now(zoneinfo.ZoneInfo("Europe/Moscow"))
        async with aiosqlite.connect(DB_NAME) as db:
            # Получаем всех пользователей с напоминаниями
            cursor = await db.execute(
                "SELECT user_id, remind_before FROM user_settings WHERE notifications_enabled = 1"
            )
            users = await cursor.fetchall()
            user_remind = {user_id: remind_before for user_id, remind_before in users}
            # Для пользователей без user_settings — по умолчанию 60 минут
            cursor = await db.execute(
                "SELECT DISTINCT user_id FROM events"
            )
            all_users = {row[0] for row in await cursor.fetchall()}
            for user_id in all_users:
                if user_id not in user_remind:
                    user_remind[user_id] = 60
            # Собираем события для напоминания (только те, у которых status='active')
            result = []
            for user_id, remind_before in user_remind.items():
                target_time = now + timedelta(minutes=remind_before)
                date_str = target_time.strftime("%Y-%m-%d")
                time_from = (target_time - timedelta(minutes=1)).strftime("%H:%M")
                time_to = (target_time + timedelta(minutes=1)).strftime("%H:%M")
                cursor = await db.execute(
                    "SELECT id, title FROM events WHERE user_id=? AND date=? AND time BETWEEN ? AND ? AND (status IS NULL OR status='active')",
                    (user_id, date_str, time_from, time_to)
                )
                for row in await cursor.fetchall():
                    event_id, title = row
                    result.append((user_id, event_id, title))
            return result
    except Exception as e:
        logging.error(f"Ошибка получения событий для напоминания: {e}")
        return []

# Массово обновить статус событий на 'reminded'
async def set_events_reminded(event_ids: list[int], user_id: int) -> None:
    """
    Устанавливает статус 'reminded' для списка событий пользователя.
    """
    if not event_ids:
        return
    try:
        async with aiosqlite.connect(DB_NAME) as db:
            await db.executemany(
                "UPDATE events SET status='reminded' WHERE id=? AND user_id=?",
                [(eid, user_id) for eid in event_ids]
            )
            await db.commit()
    except Exception as e:
        logging.error(f"Ошибка массового обновления статуса событий: {e}")

# Получить все события пользователя на дату (теперь возвращает tag)
async def get_events_for_date(date: str, user_id: int) -> List[Tuple[str, str, str]]:
    """
    Получает события пользователя на определённую дату.
    """
    try:
        async with aiosqlite.connect(DB_NAME) as db:
            cursor = await db.execute(
                "SELECT title, time, tag FROM events WHERE date=? AND user_id=? ORDER BY time",
                (date, user_id)
            )
            rows = await cursor.fetchall()
            return list(map(tuple, rows))
    except Exception as e:
        logging.error(f"Ошибка получения событий на дату: {e}")
        return []

# --- ДОБАВЛЯЕМ ПОЛЕ status В ТАБЛИЦУ events ---
async def migrate_add_status_to_events():
    """
    Добавляет поле status в таблицу events, если его нет.
    """
    try:
        async with aiosqlite.connect(DB_NAME) as db:
            try:
                await db.execute("ALTER TABLE events ADD COLUMN status TEXT DEFAULT 'active'")
                await db.commit()
                logging.info("Поле status добавлено в таблицу events.")
            except Exception:
                pass  # Уже добавлено
    except Exception as e:
        logging.error(f"Ошибка миграции поля status: {e}")

# --- УСТАНОВИТЬ СТАТУС ЗАДАЧИ ---
async def set_event_status(event_id: int, user_id: int, status: str) -> bool:
    """
    Устанавливает статус задачи.
    """
    try:
        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute(
                "UPDATE events SET status=? WHERE id=? AND user_id=?",
                (status, event_id, user_id)
            )
            await db.commit()
            return True
    except Exception as e:
        logging.error(f"Ошибка установки статуса задачи: {e}")
        return False

# --- ПОЛУЧИТЬ СТАТУС ЗАДАЧИ ---
async def get_event_status(event_id: int, user_id: int) -> str:
    """
    Получает статус задачи.
    """
    try:
        async with aiosqlite.connect(DB_NAME) as db:
            cursor = await db.execute(
                "SELECT status FROM events WHERE id=? AND user_id=?",
                (event_id, user_id)
            )
            row = await cursor.fetchone()
            return row[0] if row else 'active'
    except Exception as e:
        logging.error(f"Ошибка получения статуса задачи: {e}")
        return 'active'

# --- ОБНОВЛЯЕМ ВЫБОРКИ: ДОБАВЛЯЕМ status ---
# Получить все события пользователя на дату (с id)
async def get_events_for_date_with_id(date: str, user_id: int) -> List[Tuple[int, str, str, str, str]]:
    """
    Получает события пользователя на дату с id и статусом.
    """
    try:
        async with aiosqlite.connect(DB_NAME) as db:
            cursor = await db.execute(
                "SELECT id, title, time, tag, status FROM events WHERE date=? AND user_id=? ORDER BY time",
                (date, user_id)
            )
            rows = await cursor.fetchall()
            return list(map(tuple, rows))
    except Exception as e:
        logging.error(f"Ошибка получения событий на дату: {e}")
        return []

# Удалить событие по id
async def delete_event(event_id: int, user_id: int) -> bool:
    """
    Удаляет событие по id.
    """
    try:
        async with aiosqlite.connect(DB_NAME) as db:
            cursor = await db.execute(
                "DELETE FROM events WHERE id=? AND user_id=?",
                (event_id, user_id)
            )
            await db.commit()
            return cursor.rowcount > 0
    except Exception as e:
        logging.error(f"Ошибка удаления события: {e}")
        return False

# Получить все события пользователя за всё время (с id)
async def get_all_events_for_user(user_id: int) -> List[Tuple[int, str, str, str, str, str]]:
    """
    Получает все события пользователя за всё время.
    """
    try:
        async with aiosqlite.connect(DB_NAME) as db:
            cursor = await db.execute(
                "SELECT id, title, date, time, tag, status FROM events WHERE user_id=? ORDER BY date, time",
                (user_id,)
            )
            rows = await cursor.fetchall()
            return list(map(tuple, rows))
    except Exception as e:
        logging.error(f"Ошибка получения всех событий пользователя: {e}")
        return []