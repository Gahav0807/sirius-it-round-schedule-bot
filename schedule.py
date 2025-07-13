from apscheduler.schedulers.asyncio import AsyncIOScheduler
from functools import partial
from aiogram import Bot
from db import get_events_for_reminder
from typing import Any
import logging

scheduler = AsyncIOScheduler()

# Отправка напоминаний пользователям
async def send_reminders(bot: Bot) -> None:
    """
    Отправляет напоминания пользователям о предстоящих событиях (только один раз).
    """
    from db import set_events_reminded  # импорт внутри функции, чтобы избежать циклических импортов
    events = await get_events_for_reminder()
    # Группируем по пользователю для массового обновления
    user_events = {}
    for user_id, event_id, title in events:
        try:
            await bot.send_message(user_id, f"🔔 Напоминание: {title} через час!")
        except Exception as e:
            logging.error(f"Ошибка отправки напоминания пользователю {user_id}: {e}")
        user_events.setdefault(user_id, []).append(event_id)
    # После отправки обновляем статус событий на 'reminded'
    for user_id, event_ids in user_events.items():
        await set_events_reminded(event_ids, user_id)

# Запуск планировщика напоминаний
def setup_scheduler(bot: Bot) -> None:
    """
    Запускает планировщик напоминаний для Telegram-бота.
    """
    scheduler.add_job(partial(send_reminders, bot), 'interval', minutes=1)
    scheduler.start()
    logging.info("Планировщик напоминаний запущен.")
