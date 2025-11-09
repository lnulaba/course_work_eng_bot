import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.types import TelegramObject

from db import Connection, DB
from handlers import basic, testing

logging.basicConfig(level=logging.INFO)
bot = Bot(token="7365678598:AAHAMFBVPRR5etj4Fdt3TTLnmWJSDNbrWFQ")
dp = Dispatcher()

# Initialize the database connection
connection = Connection()
db = None

async def setup_database():
    """Налаштувати з'єднання з базою даних"""
    await connection.connect()
    global db
    db = DB(connection.session_maker)

# Middleware для передачі db у handlers
async def db_middleware(handler, event: TelegramObject, data: dict):
    """Додати db до контексту обробників"""
    data['db'] = db
    return await handler(event, data)

# Підключити роутери
dp.include_router(basic.router)
dp.include_router(testing.router)

# Додати middleware
dp.update.middleware(db_middleware)

async def main():
    """Головна функція запуску бота"""
    await setup_database()
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Bot stopped by user (Ctrl+C)")


