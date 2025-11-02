import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

from db import *

logging.basicConfig(level=logging.INFO)
bot = Bot(token="7365678598:AAHAMFBVPRR5etj4Fdt3TTLnmWJSDNbrWFQ")
dp = Dispatcher()

kb_start = types.ReplyKeyboardMarkup(
    keyboard=[
        [
            types.KeyboardButton(text="Почати тестування"),
        ],
        [
            types.KeyboardButton(text="A0"),
            types.KeyboardButton(text="A1"),
            types.KeyboardButton(text="A2"),
            types.KeyboardButton(text="B1"),
        ],
        [
            types.KeyboardButton(text="B2"),
            types.KeyboardButton(text="C1"),
            types.KeyboardButton(text="C2"),
        ],
        [
            types.KeyboardButton(text="Інформація про курс"),
            types.KeyboardButton(text="Допомога"),
            types.KeyboardButton(text="Підтримати розробника"),
        ]
    ],
    resize_keyboard=True,
)

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    # show all info the user
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    username = message.from_user.username
    language_code = message.from_user.language_code
    is_premium = message.from_user.is_premium
    # перевірити чи користувач є в базі даних
    user = await db.get_user(user_id)
    if not user:
        await db.add_user(
            user_id=user_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            tg_id=message.from_user.id,
            tg_premium=is_premium,
            tg_lang=language_code
        )

        await message.answer(f"Привіт, {first_name}!\n Ваш профіль було створено в базі даних.")
    else:
        await message.answer(f"Вітаємо знову, {first_name}!\n Ваш профіль вже існує в базі даних.")


    


    # await message.answer("Привіт! Я бот для визначення вашого рівня англійської мови.")
    # # пояснити що за рівні
    # await message.answer("Рівні англійської мови:\n"
    #                     "A0 - Початковий\n"
    #                     "A1 - Елементарний\n"
    #                     "A2 - Базовий\n"
    #                     "B1 - Середній\n"
    #                     "B2 - Вище середнього\n"
    #                     "C1 - Просунутий\n"
    #                     "C2 - Вільне володіння")
    
    # await message.answer("Виберіть потрібну операцію: ", reply_markup=kb_start)

# Почати тестування
@dp.message(lambda message: message.text == "Почати тестування")
async def start_testing(message: types.Message):
    await message.answer("Ви обрали 'Почати тестування'.")
    # Додайте логіку для початку тестування тут
    # get_random_words
    random_words = await db.get_random_words(total_count=35) # кратно 7 (рівням)
    print(len(random_words))
    for index, word in enumerate(random_words, 1):
        print(f"{index}. {word.word} - {word.translation} - {word.level_english}")

    # await message.answer(f"Here are some random words for testing: {random_words}")

# A0, A1, A2, B1, B2, C1, C2
@dp.message(lambda message: message.text in ["A0", "A1", "A2", "B1", "B2", "C1", "C2"])
async def select_level(message: types.Message):
    level = message.text
    await message.answer(f"Ви обрали рівень {level}.")
    # Додайте логіку для вибору рівня тут

# Інформація про курс
@dp.message(lambda message: message.text == "Інформація про курс")
async def course_info(message: types.Message):
    await message.answer("Інформація про курс:\n"
                        "Цей курс допоможе вам покращити ваш рівень англійської мови за допомогою тестів та вправ.")
# Допомога
@dp.message(lambda message: message.text == "Допомога")
async def help_info(message: types.Message):
    await message.answer("Якщо вам потрібна допомога, зверніться до розробника бота.")

# Підтримати розробника
@dp.message(lambda message: message.text == "Підтримати розробника")
async def support_developer(message: types.Message):
    # Поділитися ботом, донат розробнику
    await message.answer("Якщо ви хочете підтримати розробника, будь ласка, поділіться цим ботом з друзями!")
    await message.answer("Також ви можете зробити донат на наступну адресу:\n"
                        "https://www.buymeacoffee.com/developer")

# Initialize the database connection
connection = Connection()

async def setup_database():
    await connection.connect()
    global db
    db = DB(connection.session_maker)

# Ensure the database is set up before starting the bot
async def main():
    await setup_database()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())


