import aiosqlite
from datetime import datetime, timedelta

DB_NAME = "events.db"

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                title TEXT,
                date TEXT,
                time TEXT
            )
        """)
        await db.commit()
        print("Database initialized")

async def add_event(user_id, title, date, time):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("INSERT INTO events (user_id, title, date, time) VALUES (?, ?, ?, ?)",
                         (user_id, title, date, time))
        await db.commit()

async def get_events_for_reminder():
    now_plus_hour = datetime.now() + timedelta(hours=1)
    target_date = now_plus_hour.strftime("%Y-%m-%d")
    target_time = now_plus_hour.strftime("%H:%M")
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT user_id, title FROM events WHERE date=? AND time=?", (target_date, target_time))
        return await cursor.fetchall()

async def get_events_for_date(date: str, user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT title, time FROM events WHERE date=? AND user_id=? ORDER BY time",
            (date, user_id)
        )
        return await cursor.fetchall()