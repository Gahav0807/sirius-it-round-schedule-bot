import asyncio
from aiogram import Router, types
from aiogram.filters.command import Command
from datetime import datetime, timedelta
from dateparser.search import search_dates
from db import add_event, get_events_for_date

router = Router()

@router.message(Command("start", "help"))
async def help_cmd(message: types.Message):
    await message.answer("""🧭 Доступные команды:
/today — расписание на сегодня
/tomorrow — на завтра
/week — на неделю
/add Название Дата Время — добавить событие
/schedule — как добавить событие
""")

@router.message(Command("schedule"))
async def schedule_info(message: types.Message):
    await message.answer("Пример: /add Контрольная 2025-07-11 14:00")

@router.message(Command("add"))
async def add_cmd(message: types.Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        return await message.answer("❗ Пример: /add Контрольная 2025-07-11 14:00")

    content = args[1]
    result = search_dates(content, languages=["ru"])

    if not result:
        return await message.answer("❌ Не удалось распознать дату и время.")

    date_text, parsed = result[-1]  # берём последнее совпадение
    title = content.replace(date_text, "").strip(" ,–—")

    date_str = parsed.strftime("%Y-%m-%d")
    time_str = parsed.strftime("%H:%M")

    if not title:
        title = "Событие"

    await add_event(message.from_user.id, title, date_str, time_str)
    await message.answer(f"✅ Событие «{title}» добавлено на {date_str} в {time_str}.")

@router.message(Command("today"))
async def today_cmd(message: types.Message):
    date_str = datetime.now().strftime("%Y-%m-%d")
    events = await get_events_for_date(date_str, message.from_user.id)
    if not events:
        await message.answer("📭 Сегодня у вас нет событий.")
    else:
        text = f"📅 Сегодня ({date_str}):\n" + "\n".join([f"🕒 {t} — {title}" for title, t in events])
        await message.answer(text)

@router.message(Command("tomorrow"))
async def tomorrow_cmd(message: types.Message):
    date_str = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    events = await get_events_for_date(date_str, message.from_user.id)
    if not events:
        await message.answer("📭 Завтра у вас нет событий.")
    else:
        text = f"📅 Завтра ({date_str}):\n" + "\n".join([f"🕒 {t} — {title}" for title, t in events])
        await message.answer(text)

@router.message(Command("week"))
async def week_cmd(message: types.Message):
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
