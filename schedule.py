from apscheduler.schedulers.asyncio import AsyncIOScheduler
from functools import partial
from db import get_events_for_reminder

scheduler = AsyncIOScheduler()

async def send_reminders(bot):
    events = await get_events_for_reminder()
    for user_id, title in events:
        try:
            await bot.send_message(user_id, f"🔔 Напоминание: {title} через час!")
        except Exception as e:
            print(f"Failed to send reminder to {user_id}: {e}")

def setup_scheduler(bot):
    scheduler.add_job(partial(send_reminders, bot), 'interval', minutes=1)
    scheduler.start()
    print("Scheduler started")
