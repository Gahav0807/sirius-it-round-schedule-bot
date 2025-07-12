import aiosqlite
import logging
from datetime import datetime, timedelta
from config import DB_NAME
from typing import List, Tuple

# Инициализация базы данных
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
                    time TEXT
                )
                """
            )
            await db.commit()
        logging.info("База данных инициализирована.")
    except Exception as e:
        logging.error(f"Ошибка инициализации базы данных: {e}")

# Добавить событие в базу
async def add_event(user_id: int, title: str, date: str, time: str) -> None:
    try:
        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute(
                "INSERT INTO events (user_id, title, date, time) VALUES (?, ?, ?, ?)",
                (user_id, title, date, time)
            )
            await db.commit()
    except Exception as e:
        logging.error(f"Ошибка добавления события: {e}")

# Получить события, пользователей которых надо напомнить о них (за час)
async def get_events_for_reminder() -> List[Tuple[int, str]]:
    try:
        now = datetime.now()
        now_plus_hour = now + timedelta(hours=1)
        target_date = now_plus_hour.strftime("%Y-%m-%d")
        time_from = (now_plus_hour - timedelta(minutes=1)).strftime("%H:%M")
        time_to = (now_plus_hour + timedelta(minutes=1)).strftime("%H:%M")
        async with aiosqlite.connect(DB_NAME) as db:
            cursor = await db.execute(
                """
                SELECT user_id, title FROM events 
                WHERE date = ? AND time BETWEEN ? AND ?
                """,
                (target_date, time_from, time_to)
            )
            rows = await cursor.fetchall()
            return list(map(tuple, rows))
    except Exception as e:
        logging.error(f"Ошибка получения событий для напоминания: {e}")
        return []

# Получить все события пользователя на дату
async def get_events_for_date(date: str, user_id: int) -> List[Tuple[str, str]]:
    try:
        async with aiosqlite.connect(DB_NAME) as db:
            cursor = await db.execute(
                "SELECT title, time FROM events WHERE date=? AND user_id=? ORDER BY time",
                (date, user_id)
            )
            rows = await cursor.fetchall()
            return list(map(tuple, rows))
    except Exception as e:
        logging.error(f"Ошибка получения событий на дату: {e}")
        return []