import asyncio
from aiogram import Dispatcher
from config import bot
from bot import router
from db import init_db
from schedule import setup_scheduler

async def main():
    await init_db()
    setup_scheduler(bot)

    dp = Dispatcher()
    dp.include_router(router)

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main()) 