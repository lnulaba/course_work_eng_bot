import logging
from aiogram import types, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardRemove

from keyboards.reply import kb_with_level  # Замість kb_start
from keyboards.inline import get_word_answer_keyboard
from utils import ask_ai_async

router = Router()

# FSM States
class TestingStates(StatesGroup):
    testing = State()
# Пройти заново тестування або Почати тестування
@router.message(lambda message: message.text == "Почати тестування" )
async def start_testing(message: types.Message, state: FSMContext, db):
    """Початок тестування"""
    await message.answer(
        "Ви обрали 'Почати тестування'.\n"
        "Оцініть ваше знання кожного слова.",
        reply_markup=ReplyKeyboardRemove()
    )
    
    # Отримати випадкові слова
    random_words = await db.get_random_words(total_count=14) # Наприклад, 35 слів кратно 7
    
    # Зберегти слова, результати та user_id в FSM
    await state.update_data(
        words=random_words,
        current_index=0,
        results=[],
        user_id=message.from_user.id
    )
    
    # Почати тестування
    await show_next_word(message, state, db)

async def show_next_word(message: types.Message, state: FSMContext, db):
    """Показати наступне слово з інлайн кнопками"""
    data = await state.get_data()
    words = data.get('words', [])
    current_index = data.get('current_index', 0)
    
    if current_index >= len(words):
        # Тестування завершено
        await finish_testing(message, state, db)
        return
    
    current_word = words[current_index]
    
    # Створити інлайн кнопки
    keyboard = get_word_answer_keyboard(current_index)
    
    # Відправити слово
    await message.answer(
        f"Слово {current_index + 1}/{len(words)}\n\n"
        f"🇬🇧 <b>{current_word.word}</b>\n"
        f"🇺🇦 <span class=\"tg-spoiler\">{current_word.translation}</span>\n\n"
        f"Рівень: {current_word.level_english}",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    
    await state.set_state(TestingStates.testing)

@router.callback_query(F.data.startswith("answer_"))
async def process_answer(callback: types.CallbackQuery, state: FSMContext, db):
    """Обробити відповідь користувача"""
    # Відповісти на callback ОДРАЗУ (до будь-яких довгих операцій)
    await callback.answer()
    
    data = await state.get_data()
    words = data.get('words', [])
    current_index = data.get('current_index', 0)
    results = data.get('results', [])
    
    # Отримати тип відповіді
    answer_type = callback.data.split('_')[1]  # know, forgot, dont
    
    # Зберегти результат
    current_word = words[current_index]
    results.append({
        'word': current_word.word,
        'translation': current_word.translation,
        'level': current_word.level_english,
        'answer': answer_type
    })
    
    # Оновити дані
    await state.update_data(
        current_index=current_index + 1,
        results=results
    )
    
    # Видалити попереднє повідомлення
    try:
        await callback.message.delete()
    except Exception as e:
        logging.warning(f"Could not delete message: {e}")
    
    # Показати наступне слово
    await show_next_word(callback.message, state, db)

async def finish_testing(message: types.Message, state: FSMContext, db):
    """Завершити тестування та визначити рівень"""
    # info logging
    logging.info(f"User level determination started.")

    data = await state.get_data()
    results = data.get('results', [])
    user_id = data.get('user_id')
    
    await message.answer("⏳ Тестування завершено! Обробляю результати...")
    
    # Визначити рівень через ChatGPT
    logging.info(f"Determining level for user {user_id} with {len(results)} results.")
    level = await determine_english_level(results)
    logging.info(f"Determined level for user {user_id}: {level}")
    
    # Підрахувати статистику
    know_count = sum(1 for r in results if r['answer'] == 'know')
    forgot_count = sum(1 for r in results if r['answer'] == 'forgot')
    dont_know_count = sum(1 for r in results if r['answer'] == 'dont')
    
    # Зберегти результати в базу даних
    total_questions = len(results)
    correct_answers = know_count + (forgot_count // 2)  # Частково враховуємо "не згадав"
    
    try:
        await db.update_user_progress(
            user_id=user_id,
            level_english=level,
            total_questions=total_questions,
            correct_answers=correct_answers
        )
        logging.info(f"User {user_id} progress saved: level={level}, correct={correct_answers}/{total_questions}")
    except Exception as e:
        logging.error(f"Error saving user progress: {e}")
    
    # Отримати відповідну клавіатуру
    from handlers.basic import get_appropriate_keyboard
    keyboard = await get_appropriate_keyboard(db, user_id)
    
    await message.answer(
        f"🎉 <b>Результати тестування:</b>\n\n"
        f"📊 Статистика:\n"
        f"✅ Знаю: {know_count}\n"
        f"🤔 Не згадав: {forgot_count}\n"
        f"❌ Не знаю: {dont_know_count}\n\n"
        f"🎓 <b>Ваш рівень англійської: {level}</b>\n\n"
        f"💾 Результати збережено у вашому профілі!",
        parse_mode="HTML",
        reply_markup=keyboard
    )
    
    # Очистити стан
    await state.clear()

async def determine_english_level(results: list) -> str:
    """Визначити рівень англійської через ChatGPT"""
    try:
        # Підготувати дані для аналізу
        analysis_data = []
        for result in results:
            status = {
                'know': 'знає',
                'forgot': 'не згадав',
                'dont': 'не знає'
            }.get(result['answer'], 'невідомо')
            
            analysis_data.append(
                f"Слово: {result['word']} (рівень {result['level']}) - {status}"
            )
        
        prompt = f"""Ти експерт з визначення рівня англійської мови.
Користувач пройшов тест на знання слів різних рівнів (A0, A1, A2, B1, B2, C1, C2).

Результати тесту:
{chr(10).join(analysis_data)}

Проаналізуй результати та визнач рівень англійської мови користувача.
ВАЖЛИВО: У відповіді напиши ТІЛЬКИ один рівень з цього списку: A0, A1, A2, B1, B2, C1, C2
Нічого більше не пиши, тільки рівень."""

        level = await ask_ai_async(prompt)
        print(f"Determined level from GPT: {level}")
        
        # Валідація рівня
        valid_levels = ["A0", "A1", "A2", "B1", "B2", "C1", "C2"]
        if level in valid_levels:
            return level
        else:
            # Якщо ChatGPT повернув щось інше, спробувати знайти рівень у тексті
            for valid_level in valid_levels:
                if valid_level in level:
                    return valid_level
            return "A1"  # За замовчуванням
            
    except Exception as e:
        logging.error(f"Error determining level: {e}")
        # Fallback: простий алгоритм
        know_count = sum(1 for r in results if r['answer'] == 'know')
        percentage = (know_count / len(results)) * 100
        
        if percentage >= 90:
            return "C2"
        elif percentage >= 80:
            return "C1"
        elif percentage >= 70:
            return "B2"
        elif percentage >= 60:
            return "B1"
        elif percentage >= 50:
            return "A2"
        elif percentage >= 30:
            return "A1"
        else:
            return "A0"
