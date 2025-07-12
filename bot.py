import asyncio
from aiogram import Router, types
from aiogram.filters.command import Command
from datetime import datetime, timedelta
from db import add_event, get_events_for_date
from typing import Final
import logging

router = Router()

# Сообщения-ответы
ABOUT_TEXT: Final[str] = (
    "Бот для ведения личного расписания и напоминаний. Разработан для учебного проекта IT-Round.\n"
    "Исходный код с инструкцией по запуску: https://github.com/Gahav0807/sirius-it-round-schedule-bot\n\n"
    "Для получения списка команд: /help"
)
HELP_TEXT: Final[str] = (
    "🧭 Доступные команды:\n"
    "/today — расписание на сегодня\n"
    "/tomorrow — на завтра\n"
    "/week — на неделю\n"
    "/add Название Дата Время — добавить событие\n"
    "/schedule — пример добавления события\n"
)
SCHEDULE_EXAMPLE: Final[str] = "Пример: /add Контрольная 2025-07-11 14:00"
ADD_FORMAT_ERROR: Final[str] = (
    "❗ Формат команды: /add Название 2025-07-11 14:00\nПример: /add Контрольная 2025-07-11 14:00"
)
NO_EVENTS_TODAY: Final[str] = "📭 Сегодня у вас нет событий."
NO_EVENTS_TOMORROW: Final[str] = "📭 Завтра у вас нет событий."
NO_EVENTS_WEEK: Final[str] = "📭 На этой неделе у вас нет событий."
UNKNOWN_COMMAND: Final[str] = "❓ Неизвестная команда. Используйте /help для списка команд."
ONLY_COMMANDS: Final[str] = "Я понимаю только команды. Для справки — /help."

# Ответ на команду /start
@router.message(Command("start"))
async def about_cmd(message: types.Message) -> None:
    await message.answer(ABOUT_TEXT)

# Ответ на команду /help
@router.message(Command("help"))
async def help_cmd(message: types.Message) -> None:
    await message.answer(HELP_TEXT)

# Пример добавления события
@router.message(Command("schedule"))
async def schedule_info(message: types.Message) -> None:
    await message.answer(SCHEDULE_EXAMPLE)

# Добавление события через /add
@router.message(Command("add"))
async def add_cmd(message: types.Message) -> None:
    try:
        _, content = message.text.split(maxsplit=1)
        title, date_str, time_str = content.rsplit(" ", 2)
        if not title.strip():
            raise ValueError("Укажите название события.")

        # Преобразуем дату и время в datetime-объект
        event_datetime = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        now = datetime.now()

        # Проверка: нельзя добавлять событие в прошлом
        if event_datetime < now:
            raise ValueError("Нельзя добавлять событие в прошлом.")

    except ValueError as e:
        logging.warning(f"Ошибка валидации команды /add: {e}")
        return await message.answer(
            f"❗ Формат команды: /add Название 2025-07-11 14:00\nОшибка: {e}" if str(e) else ADD_FORMAT_ERROR
        )
    except Exception as e:
        logging.error(f"Неизвестная ошибка в команде /add: {e}")
        return await message.answer(ADD_FORMAT_ERROR)

    await add_event(message.from_user.id, title.strip(), date_str, time_str)
    logging.info(f"Пользователь {message.from_user.id} добавил событие '{title.strip()}' на {date_str} {time_str}")
    await message.answer(f"✅ Событие «{title.strip()}» добавлено на {date_str} в {time_str}.")
    
# События на сегодня
@router.message(Command("today"))
async def today_cmd(message: types.Message) -> None:
    try:
        date_str = datetime.now().strftime("%Y-%m-%d")
        events = await get_events_for_date(date_str, message.from_user.id)
        if not events:
            await message.answer(NO_EVENTS_TODAY)
        else:
            text = f"📅 Сегодня ({date_str}):\n" + "\n".join([f"🕒 {t} — {title}" for title, t in events])
            await message.answer(text)
    except Exception as e:
        logging.error(f"Ошибка в команде /today: {e}")

# События на завтра
@router.message(Command("tomorrow"))
async def tomorrow_cmd(message: types.Message) -> None:
    try:
        date_str = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        events = await get_events_for_date(date_str, message.from_user.id)
        if not events:
            await message.answer(NO_EVENTS_TOMORROW)
        else:
            text = f"📅 Завтра ({date_str}):\n" + "\n".join([f"🕒 {t} — {title}" for title, t in events])
            await message.answer(text)
    except Exception as e:
        logging.error(f"Ошибка в команде /tomorrow: {e}")

# События на неделю
@router.message(Command("week"))
async def week_cmd(message: types.Message) -> None:
    try:
        today = datetime.now()
        text = "📆 События на неделю:\n"
        found = False
        for i in range(7):
            d = today + timedelta(days=i)
            date_str = d.strftime("%Y-%m-%d")
            events = await get_events_for_date(date_str, message.from_user.id)
            if events:
                found = True
                text += f"\n📅 {d.strftime('%A %d.%m')}:\n"
                text += "\n".join([f"  🕒 {t} — {title}" for title, t in events]) + "\n"
        if not found:
            await message.answer(NO_EVENTS_WEEK)
        else:
            await message.answer(text)
    except Exception as e:
        logging.error(f"Ошибка в команде /week: {e}")

# Ответ на неизвестную команду или текст
@router.message()
async def unknown_cmd(message: types.Message) -> None:
    if message.text and message.text.startswith("/"):
        logging.info(f"Неизвестная команда: {message.text}")
        await message.answer(UNKNOWN_COMMAND)
    else:
        await message.answer(ONLY_COMMANDS)
