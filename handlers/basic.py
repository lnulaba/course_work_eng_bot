from aiogram import types, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from keyboards.reply import (
    kb_unregistered, 
    kb_no_level, 
    kb_with_level, 
    kb_select_level
)

router = Router()

# FSM для вибору рівня
class LevelSelection(StatesGroup):
    selecting_level = State()

async def get_appropriate_keyboard(db, user_id):
    """Отримати відповідну клавіатуру залежно від стану користувача"""
    user = await db.get_user(user_id)
    
    if not user:
        return kb_unregistered
    
    progress = await db.get_user_progress(user_id)
    
    if not progress:
        return kb_no_level
    
    return kb_with_level

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
    progress = await db.get_user_progress(user_id)
    
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
            f"Привіт, {first_name}! 👋\n\n"
            f"Вітаю в боті для вивчення англійської мови! 🇬🇧\n\n"
            f"Почніть з тестування, щоб визначити ваш рівень англійської.",
            reply_markup=kb_unregistered
        )
    else:
        keyboard = await get_appropriate_keyboard(db, user_id)
        
        if progress:
            await message.answer(
                f"Вітаємо знову, {first_name}! 👋\n\n"
                f"Ваш поточний рівень: <b>{progress.level_english}</b>\n"
                f"Точність: {progress.accuracy:.1f}%",
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        else:
            await message.answer(
                f"Вітаємо знову, {first_name}! 👋\n\n"
                f"Пройдіть тестування для визначення вашого рівня.",
                reply_markup=keyboard
            )

@router.message(lambda message: message.text == "Змінити рівень самому")
async def change_level_manually(message: types.Message, state: FSMContext):
    """Обробник ручної зміни рівня"""
    await state.set_state(LevelSelection.selecting_level)
    await message.answer(
        "Оберіть свій рівень англійської мови:",
        reply_markup=kb_select_level
    )

@router.message(LevelSelection.selecting_level, lambda message: message.text in ["A0", "A1", "A2", "B1", "B2", "C1", "C2"])
async def process_level_selection(message: types.Message, state: FSMContext, db):
    """Обробка вибору рівня"""
    selected_level = message.text
    user_id = message.from_user.id
    
    # Оновити або створити прогрес з вибраним рівнем
    try:
        await db.update_user_progress(
            user_id=user_id,
            level_english=selected_level,
            total_questions=0,
            correct_answers=0
        )
        
        await state.clear()
        keyboard = await get_appropriate_keyboard(db, user_id)
        
        await message.answer(
            f"✅ Ваш рівень встановлено на <b>{selected_level}</b>!\n\n"
            f"Ви можете пройти тестування для підтвердження рівня.",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    except Exception as e:
        await message.answer(
            f"❌ Помилка при збереженні рівня: {e}\n"
            f"Спробуйте ще раз.",
            reply_markup=kb_select_level
        )

@router.message(LevelSelection.selecting_level, lambda message: message.text == "Назад")
async def cancel_level_selection(message: types.Message, state: FSMContext, db):
    """Скасування вибору рівня"""
    await state.clear()
    user_id = message.from_user.id
    keyboard = await get_appropriate_keyboard(db, user_id)
    await message.answer(
        "Вибір рівня скасовано.",
        reply_markup=keyboard
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

@router.message(lambda message: message.text == "Статистика")
async def show_statistics(message: types.Message, db):
    """Обробник статистики"""
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    
    # Отримати інформацію про користувача
    user = await db.get_user(user_id)
    progress = await db.get_user_progress(user_id)
    
    # Отримати статистику питань та слів
    questions_stats = await db.get_questions_statistics()
    words_stats = await db.get_words_statistics()
    
    # Сформувати повідомлення
    message_text = f"📊 <b>СТАТИСТИКА</b>\n\n"
    
    # Інформація про користувача
    message_text += f"👤 <b>Ваш профіль:</b>\n"
    message_text += f"  Ім'я: {first_name}\n"
    if user:
        message_text += f"  Дата реєстрації: {user.registration_date.strftime('%d.%m.%Y')}\n"
    
    if progress:
        message_text += f"\n🎓 <b>Ваш прогрес:</b>\n"
        message_text += f"  Поточний рівень: <b>{progress.level_english}</b>\n"
        message_text += f"  Питань пройдено: {progress.total_questions_answered}\n"
        message_text += f"  Правильних відповідей: {progress.correct_answers}\n"
        message_text += f"  Точність: {progress.accuracy:.1f}%\n"
    else:
        message_text += f"\n🎓 <b>Ваш прогрес:</b>\n"
        message_text += f"  Пройдіть тестування для визначення рівня!\n"
    
    # Статистика слів
    message_text += f"\n📚 <b>Словниковий запас ({words_stats['total']} слів):</b>\n"
    for level in ["A0", "A1", "A2", "B1", "B2", "C1", "C2"]:
        count = words_stats['by_level'].get(level, 0)
        message_text += f"  {level}: {count} слів\n"
    
    # Статистика питань
    message_text += f"\n❓ <b>База питань ({questions_stats['total']} питань):</b>\n"
    
    message_text += f"\n<b>По рівнях:</b>\n"
    for level in ["A1", "A2", "B1", "B2", "C1", "C2"]:
        count = questions_stats['by_level'].get(level, 0)
        message_text += f"  {level}: {count} питань\n"
    
    message_text += f"\n<b>По темах:</b>\n"
    for topic, count in questions_stats['by_topic'].items():
        message_text += f"  {topic}: {count} питань\n"
    
    # Детальна статистика по рівнях і темах
    # if questions_stats['by_level_topic']:
    #     message_text += f"\n<b>📋 Детально по рівнях і темах:</b>\n"
    #     for level in ["A1", "A2", "B1", "B2", "C1", "C2"]:
    #         if level in questions_stats['by_level_topic']:
    #             message_text += f"\n  <b>{level}:</b>\n"
    #             for topic, count in questions_stats['by_level_topic'][level].items():
    #                 message_text += f"    • {topic}: {count}\n"
    
    await message.answer(message_text, parse_mode="HTML")
