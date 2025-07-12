from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.client.bot import DefaultBotProperties

BOT_TOKEN = "8168734935:AAGH8q96wBmgDqk_UdtTwETRCwQnJyVb-QQ"

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)