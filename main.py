import asyncio
import logging
from aiogram import Dispatcher
from config import bot
from bot import router
from db import init_db
from schedule import setup_scheduler

# Точка входа: инициализация БД, запуск планировщика и бота
async def main() -> None:
    await init_db()
    setup_scheduler(bot)
    dp = Dispatcher()
    dp.include_router(router)
    logging.info("Бот запущен и ожидает команды.")
    await dp.start_polling(bot)
    logging.info("Бот остановлен.")

if __name__ == "__main__":
    asyncio.run(main()) 