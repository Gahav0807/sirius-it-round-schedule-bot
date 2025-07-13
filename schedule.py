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
    Отправляет напоминания пользователям о предстоящих событиях.
    """
    events = await get_events_for_reminder()
    for user_id, title in events:
        try:
            await bot.send_message(user_id, f"🔔 Напоминание: {title} через час!")
        except Exception as e:
            logging.error(f"Ошибка отправки напоминания пользователю {user_id}: {e}")

# Запуск планировщика напоминаний
def setup_scheduler(bot: Bot) -> None:
    """
    Запускает планировщик напоминаний для Telegram-бота.
    """
    scheduler.add_job(partial(send_reminders, bot), 'interval', minutes=1)
    scheduler.start()
    logging.info("Планировщик напоминаний запущен.")
