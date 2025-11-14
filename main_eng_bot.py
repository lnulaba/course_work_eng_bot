import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.types import TelegramObject

from db import Connection, DB
from handlers import basic, testing, daily_learning, admin
from scheduler import ReminderScheduler

logging.basicConfig(level=logging.INFO)
bot = Bot(token="7365678598:AAHAMFBVPRR5etj4Fdt3TTLnmWJSDNbrWFQ")
dp = Dispatcher()

# Initialize the database connection
connection = Connection()
db = None
scheduler = None

async def setup_database():
    """Налаштувати з'єднання з базою даних"""
    await connection.connect()
    global db, scheduler
    db = DB(connection.session_maker)
    scheduler = ReminderScheduler(bot, db)

# Middleware для передачі db у handlers
async def db_middleware(handler, event: TelegramObject, data: dict):
    """Додати db до контексту обробників"""
    data['db'] = db
    return await handler(event, data)

# Підключити роутери
dp.include_router(basic.router)
dp.include_router(testing.router)
dp.include_router(daily_learning.router)
dp.include_router(admin.router)

# Додати middleware
dp.update.middleware(db_middleware)

async def main():
    """Головна функція запуску бота"""
    await setup_database()
    
    # Запустити планувальник в окремій задачі
    scheduler_task = asyncio.create_task(scheduler.start())
    
    try:
        await dp.start_polling(bot)
    finally:
        # Зупинити планувальник при виході
        scheduler.stop()
        await scheduler_task

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Bot stopped by user (Ctrl+C)")


