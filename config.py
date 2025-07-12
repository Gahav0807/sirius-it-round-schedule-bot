import logging
import os
from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

BOT_TOKEN = "8168734935:AAGH8q96wBmgDqk_UdtTwETRCwQnJyVb-QQ"
DB_NAME = "events.db"  # Имя файла базы данных

# Создать папку logs, если нет
os.makedirs("logs", exist_ok=True)

# Настройка логгирования: в файл и в консоль
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("logs/bot.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

# Экземпляр Telegram-бота
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)