import asyncio
from aiogram import Router, types
from aiogram.filters.command import Command
from datetime import datetime, timedelta
from dateparser.search import search_dates
from db import add_event, get_events_for_date

router = Router()

# Команда /start — информация о проекте
@router.message(Command("start"))
async def about_cmd(message: types.Message):
    await message.answer(
        "Бот для ведения личного расписания и напоминаний. Разработан для учебного проекта IT-Round.\n"
        "Исходный код с инструкцией по установке: https://github.com/Gahav0807/sirius-it-round-schedule-bot\n"
        "Для справки используйте команду /help"
    )

# Команда /help — подробная справка
@router.message(Command("help"))
async def help_cmd(message: types.Message):
    await message.answer(
        """🧭 Доступные команды:\n"
        "/today — расписание на сегодня\n"
        "/tomorrow — на завтра\n"
        "/week — на неделю\n"
        "/add Название Дата Время — добавить событие\n"
        "/schedule — пример добавления события\n"
        "/about — информация о проекте\n"
        """
    )

# Команда /schedule — пример добавления события
@router.message(Command("schedule"))
async def schedule_info(message: types.Message):
    await message.answer("Пример: /add Контрольная 2025-07-11 14:00")

# Команда /add — строгое добавление события
@router.message(Command("add"))
async def add_cmd(message: types.Message):
    """
    Добавляет событие. Ожидает формат: /add Название 2025-07-11 14:00
    """
    args = message.text.split(maxsplit=1)
    if len(args) < 2 or not args[1].strip():
        return await message.answer(
            "❗ Формат команды: /add Название 2025-07-11 14:00\n"
            "Пример: /add Контрольная 2025-07-11 14:00"
        )

    content = args[1].strip()
    # Разделяем с конца: название может содержать пробелы
    parts = content.rsplit(" ", 2)
    if len(parts) != 3:
        return await message.answer(
            "❗ Формат команды: /add Название 2025-07-11 14:00\n"
            "Пример: /add Контрольная 2025-07-11 14:00"
        )
    title, date_str, time_str = parts

    # Проверка названия
    if not title.strip():
        return await message.answer("❗ Укажите название события (не пустое).")

    # Проверка формата даты
    from datetime import datetime
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return await message.answer(
            "❗ Дата должна быть в формате ГГГГ-ММ-ДД (например, 2025-07-11)."
        )

    # Проверка формата времени
    try:
        datetime.strptime(time_str, "%H:%M")
    except ValueError:
        return await message.answer(
            "❗ Время должно быть в формате ЧЧ:ММ (например, 14:00)."
        )

    # Всё ок — добавляем событие
    await add_event(message.from_user.id, title.strip(), date_str, time_str)
    await message.answer(
        f"✅ Событие «{title.strip()}» добавлено на {date_str} в {time_str}."
    )

# Команда /today — события на сегодня
@router.message(Command("today"))
async def today_cmd(message: types.Message):
    """Показывает события на сегодня."""
    date_str = datetime.now().strftime("%Y-%m-%d")
    events = await get_events_for_date(date_str, message.from_user.id)
    if not events:
        await message.answer("📭 Сегодня у вас нет событий.")
    else:
        text = f"📅 Сегодня ({date_str}):\n" + "\n".join([f"🕒 {t} — {title}" for title, t in events])
        await message.answer(text)

# Команда /tomorrow — события на завтра
@router.message(Command("tomorrow"))
async def tomorrow_cmd(message: types.Message):
    """Показывает события на завтра."""
    date_str = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    events = await get_events_for_date(date_str, message.from_user.id)
    if not events:
        await message.answer("📭 Завтра у вас нет событий.")
    else:
        text = f"📅 Завтра ({date_str}):\n" + "\n".join([f"🕒 {t} — {title}" for title, t in events])
        await message.answer(text)

# Команда /week — события на неделю
@router.message(Command("week"))
async def week_cmd(message: types.Message):
    """Показывает события на неделю."""
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
        await message.answer("📭 На этой неделе у вас нет событий.")
    else:
        await message.answer(text)

# Обработка неизвестных команд и сообщений
@router.message()
async def unknown_cmd(message: types.Message):
    if message.text and message.text.startswith("/"):
        await message.answer("❓ Неизвестная команда. Используйте /help для списка команд.")
    else:
        await message.answer("Я понимаю только команды. Для справки — /help.")
