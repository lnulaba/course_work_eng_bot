from aiogram import types, Router
from aiogram.filters import Command

from keyboards.reply import kb_start

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message, db):
    """Обробник команди /start"""
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    username = message.from_user.username
    language_code = message.from_user.language_code
    is_premium = message.from_user.is_premium
    
    # Перевірити чи користувач є в базі даних
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
        await message.answer(
            f"Привіт, {first_name}!\nВаш профіль було створено в базі даних.",
            reply_markup=kb_start
        )
    else:
        await message.answer(
            f"Вітаємо знову, {first_name}!\nВаш профіль вже існує в базі даних.",
            reply_markup=kb_start
        )

@router.message(lambda message: message.text in ["A0", "A1", "A2", "B1", "B2", "C1", "C2"])
async def select_level(message: types.Message, db):
    """Обробник вибору рівня"""
    level = message.text
    user_id = message.from_user.id
    
    # Отримати прогрес користувача
    progress = await db.get_user_progress(user_id)
    
    if progress:
        await message.answer(
            f"Ви обрали рівень {level}.\n\n"
            f"📊 <b>Ваша статистика:</b>\n"
            f"🎓 Поточний рівень: {progress.level_english}\n"
            f"📝 Всього питань: {progress.total_questions_answered}\n"
            f"✅ Правильних відповідей: {progress.correct_answers}\n"
            f"📈 Точність: {progress.accuracy:.1f}%", 
            parse_mode="HTML"
        )
    else:
        await message.answer(
            f"Ви обрали рівень {level}.\n\n"
            f"Пройдіть тестування, щоб визначити ваш поточний рівень!"
        )

@router.message(lambda message: message.text == "Інформація про курс")
async def course_info(message: types.Message):
    """Обробник інформації про курс"""
    await message.answer(
        "Інформація про курс:\n"
        "Цей курс допоможе вам покращити ваш рівень англійської мови за допомогою тестів та вправ."
    )

@router.message(lambda message: message.text == "Допомога")
async def help_info(message: types.Message):
    """Обробник допомоги"""
    await message.answer("Якщо вам потрібна допомога, зверніться до розробника бота.")

@router.message(lambda message: message.text == "Підтримати розробника")
async def support_developer(message: types.Message):
    """Обробник підтримки розробника"""
    await message.answer("Якщо ви хочете підтримати розробника, будь ласка, поділіться цим ботом з друзями!")
    await message.answer(
        "Також ви можете зробити донат на наступну адресу:\n"
        "https://www.buymeacoffee.com/developer"
    )
