import aiosqlite
import logging
from datetime import datetime, timedelta
from config import DB_NAME
from typing import List, Tuple, Optional

# Инициализация базы данных (user_settings: добавлено remind_before)
async def init_db() -> None:
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
async def get_events_for_reminder() -> List[Tuple[int, str]]:
    try:
        now = datetime.now()
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
            # Собираем события для напоминания
            result = []
            for user_id, remind_before in user_remind.items():
                target_time = now + timedelta(minutes=remind_before)
                date_str = target_time.strftime("%Y-%m-%d")
                time_from = (target_time - timedelta(minutes=1)).strftime("%H:%M")
                time_to = (target_time + timedelta(minutes=1)).strftime("%H:%M")
                cursor = await db.execute(
                    "SELECT title FROM events WHERE user_id=? AND date=? AND time BETWEEN ? AND ?",
                    (user_id, date_str, time_from, time_to)
                )
                for row in await cursor.fetchall():
                    result.append((user_id, row[0]))
            return result
    except Exception as e:
        logging.error(f"Ошибка получения событий для напоминания: {e}")
        return []

# Получить все события пользователя на дату (теперь возвращает tag)
async def get_events_for_date(date: str, user_id: int) -> List[Tuple[str, str, str]]:
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

# Получить все события пользователя на дату (с id)
async def get_events_for_date_with_id(date: str, user_id: int) -> List[Tuple[int, str, str, str]]:
    try:
        async with aiosqlite.connect(DB_NAME) as db:
            cursor = await db.execute(
                "SELECT id, title, time, tag FROM events WHERE date=? AND user_id=? ORDER BY time",
                (date, user_id)
            )
            rows = await cursor.fetchall()
            return list(map(tuple, rows))
    except Exception as e:
        logging.error(f"Ошибка получения событий на дату: {e}")
        return []

# Удалить событие по id
async def delete_event(event_id: int, user_id: int) -> bool:
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