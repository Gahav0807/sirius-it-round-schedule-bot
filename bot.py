import logging
from datetime import datetime, timedelta
from typing import Final
from aiogram import Router, types
from aiogram.filters.command import Command
from db import (
    add_event, set_notifications_enabled, get_notifications_enabled,
    set_remind_before, get_remind_before, delete_event, get_events_for_date_with_id
)

router = Router()

TAG_COLORS = {
    "учеба": "🟦",
    "досуг": "🟩",
    "спорт": "🟧",
    "важное": "🟥",
}
TAG_LABELS = {
    "учеба": "учёба",
    "досуг": "досуг",
    "спорт": "спорт",
    "важное": "важное",
}

ABOUT_TEXT: Final[str] = (
    "Бот для ведения личного расписания и напоминаний. Разработан для учебного проекта IT-Round.\n"
    "Исходный код с инструкцией по запуску: https://github.com/Gahav0807/sirius-it-round-schedule-bot\n"
    "Для справки используйте команду /help"
)
NO_EVENTS_TODAY: Final[str] = "📭 Сегодня у вас нет событий."
NO_EVENTS_TOMORROW: Final[str] = "📭 Завтра у вас нет событий."
NO_EVENTS_WEEK: Final[str] = "📭 На этой неделе у вас нет событий."
UNKNOWN_COMMAND: Final[str] = "❓ Неизвестная команда. Используйте /help для списка команд."
ONLY_COMMANDS: Final[str] = "Я понимаю только команды. Для справки — /help."
DELETE_HINT: Final[str] = "<b>Чтобы удалить событие, используйте: /delete [id] (например: /delete 12)</b>"
DELETE_USAGE: Final[str] = "Используйте: /delete [id] (id можно узнать в списке событий)"
DELETE_OK: Final[str] = "🗑️ Событие #{id} удалено."
DELETE_FAIL: Final[str] = "Ошибка удаления или нет доступа к событию."
NOTIFY_ON: Final[str] = "🔔 Напоминания включены. Чтобы отключить — /notify off"
NOTIFY_OFF: Final[str] = "🔕 Напоминания отключены. Чтобы включить — /notify on"
NOTIFY_USAGE: Final[str] = "Используйте /notify on или /notify off"
REMIND_STATUS: Final[str] = "⏰ Сейчас напоминания приходят за {minutes} мин. до события.\nИзменить: /remind N"
REMIND_OK: Final[str] = "⏰ Теперь напоминания будут приходить за {minutes} мин. до события."
REMIND_FAIL: Final[str] = "Введите число минут от 1 до 1440. Пример: /remind 30"
ADD_FORMAT_ERROR: Final[str] = "❗ Формат команды: /add Название YYYY-MM-DD HH:MM [тег]\nОшибка: {error}"
ADD_UNKNOWN_ERROR: Final[str] = "❗ Ошибка. Проверьте формат команды."
ADD_PAST_ERROR: Final[str] = "Нельзя добавлять событие в прошлом."
ADD_TITLE_ERROR: Final[str] = "Укажите название события."
ADD_DATA_ERROR: Final[str] = "Недостаточно данных"

@router.message(Command("help"))
async def help_cmd(message: types.Message) -> None:
    today = datetime.now().strftime("%Y-%m-%d")
    help_text = (
        "🧭 Доступные команды:\n"
        "/today — расписание на сегодня\n"
        "/tomorrow — на завтра\n"
        "/week — на неделю\n"
        f"/add Название Дата Время [тег] — добавить событие (например: /add Встреча {today} 18:00 досуг)\n"
        "/schedule — пример добавления события\n"
        "/notify on|off — включить/отключить напоминания\n"
        "/remind N — за сколько минут до события напоминать\n"
        "/about — информация о проекте"
        "\n\n🎨 Поддерживаются теги: учеба, досуг, спорт, важное (цветовая маркировка)."
    )
    await message.answer(help_text)

@router.message(Command("start"))
async def about_cmd(message: types.Message) -> None:
    await message.answer(ABOUT_TEXT)

@router.message(Command("schedule"))
async def schedule_info(message: types.Message) -> None:
    today = datetime.now().strftime("%Y-%m-%d")
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    after_tomorrow = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
    schedule_text = (
        "Пример добавления события:\n"
        f"/add Встреча {today} 18:00 досуг\n\n"
    )
    await message.answer(schedule_text)

@router.message(Command("add"))
async def add_cmd(message: types.Message) -> None:
    user_id = message.from_user.id
    text = message.text
    try:
        _, content = text.split(maxsplit=1)
        parts = content.strip().split()
        if len(parts) < 3:
            raise ValueError(ADD_DATA_ERROR)
        tag = ""
        if len(parts) >= 4 and parts[-1].lower() in TAG_COLORS:
            tag = parts[-1].lower()
            time_str = parts[-2]
            date_str = parts[-3]
            title = " ".join(parts[:-3])
        else:
            time_str = parts[-1]
            date_str = parts[-2]
            title = " ".join(parts[:-2])
        if not title.strip():
            raise ValueError(ADD_TITLE_ERROR)
        dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        if dt < datetime.now():
            raise ValueError(ADD_PAST_ERROR)
    except ValueError as e:
        logging.warning(f"Ошибка валидации команды /add: {e}")
        return await message.answer(ADD_FORMAT_ERROR.format(error=e))
    except Exception as e:
        logging.error(f"Неизвестная ошибка в команде /add: {e}")
        return await message.answer(ADD_UNKNOWN_ERROR)
    await add_event(user_id, title.strip(), date_str, time_str, tag)
    color = TAG_COLORS.get(tag, "")
    tag_label = f" [{TAG_LABELS[tag]}]" if tag else ""
    await message.answer(f"{color} {title.strip()} — {dt.strftime('%d.%m.%Y')}, {time_str}{tag_label}")

@router.message(Command("today"))
async def today_cmd(message: types.Message) -> None:
    try:
        date_str = datetime.now().strftime("%Y-%m-%d")
        events = await get_events_for_date_with_id(date_str, message.from_user.id)
        if not events:
            await message.answer(NO_EVENTS_TODAY)
        else:
            text = "\n".join([
                f"#{event_id} {TAG_COLORS.get(tag, '')} {t} — {title}{f' [{TAG_LABELS[tag]}]' if tag else ''}" for event_id, title, t, tag in events
            ])
            text += f"\n\n{DELETE_HINT}"
            await message.answer(f"📅 Сегодня ({date_str}):\n" + text, parse_mode="HTML")
    except Exception as e:
        logging.error(f"Ошибка в команде /today: {e}")

@router.message(Command("tomorrow"))
async def tomorrow_cmd(message: types.Message) -> None:
    try:
        date_str = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        events = await get_events_for_date_with_id(date_str, message.from_user.id)
        if not events:
            await message.answer(NO_EVENTS_TOMORROW)
        else:
            text = "\n".join([
                f"#{event_id} {TAG_COLORS.get(tag, '')} {t} — {title}{f' [{TAG_LABELS[tag]}]' if tag else ''}" for event_id, title, t, tag in events
            ])
            text += f"\n\n{DELETE_HINT}"
            await message.answer(f"📅 Завтра ({date_str}):\n" + text, parse_mode="HTML")
    except Exception as e:
        logging.error(f"Ошибка в команде /tomorrow: {e}")

@router.message(Command("week"))
async def week_cmd(message: types.Message) -> None:
    try:
        today = datetime.now()
        found = False
        week_text = "📆 События на неделю:\n"
        for i in range(7):
            d = today + timedelta(days=i)
            date_str = d.strftime("%Y-%m-%d")
            events = await get_events_for_date_with_id(date_str, message.from_user.id)
            if events:
                found = True
                day_text = f"\n📅 {d.strftime('%A %d.%m')}:\n" + "\n".join([
                    f"#{event_id} {TAG_COLORS.get(tag, '')} {t} — {title}{f' [{TAG_LABELS[tag]}]' if tag else ''}" for event_id, title, t, tag in events
                ])
                week_text += day_text + "\n"
        if not found:
            await message.answer(NO_EVENTS_WEEK)
        else:
            week_text += f"\n{DELETE_HINT}"
            await message.answer(week_text, parse_mode="HTML")
    except Exception as e:
        logging.error(f"Ошибка в команде /week: {e}")

@router.message(Command("delete"))
async def delete_cmd(message: types.Message) -> None:
    user_id = message.from_user.id
    args = message.text.split()
    if len(args) != 2 or not args[1].isdigit():
        await message.answer(DELETE_USAGE)
        return
    event_id = int(args[1])
    ok = await delete_event(event_id, user_id)
    if ok:
        await message.answer(DELETE_OK.format(id=event_id))
    else:
        await message.answer(DELETE_FAIL)

@router.message(Command("notify"))
async def notify_cmd(message: types.Message) -> None:
    user_id = message.from_user.id
    args = message.text.split()
    if len(args) == 1:
        enabled = await get_notifications_enabled(user_id)
        if enabled:
            await message.answer(NOTIFY_ON)
        else:
            await message.answer(NOTIFY_OFF)
        return
    if args[1].lower() == "on":
        await set_notifications_enabled(user_id, True)
        await message.answer(NOTIFY_ON)
    elif args[1].lower() == "off":
        await set_notifications_enabled(user_id, False)
        await message.answer(NOTIFY_OFF)
    else:
        await message.answer(NOTIFY_USAGE)

@router.message(Command("remind"))
async def remind_cmd(message: types.Message) -> None:
    user_id = message.from_user.id
    args = message.text.split()
    if len(args) == 1:
        minutes = await get_remind_before(user_id)
        await message.answer(REMIND_STATUS.format(minutes=minutes))
        return
    try:
        minutes = int(args[1])
        if not (1 <= minutes <= 1440):
            raise ValueError
        await set_remind_before(user_id, minutes)
        await message.answer(REMIND_OK.format(minutes=minutes))
    except Exception:
        await message.answer(REMIND_FAIL)

@router.message()
async def unknown_cmd(message: types.Message) -> None:
    if message.text and message.text.startswith("/"):
        logging.info(f"Неизвестная команда: {message.text}")
        await message.answer(UNKNOWN_COMMAND)
    else:
        await message.answer(ONLY_COMMANDS)
