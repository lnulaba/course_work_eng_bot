import logging
from aiogram import types, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardRemove
import json

from keyboards.reply import kb_with_level
from keyboards.inline import get_word_answer_keyboard, get_question_answer_keyboard
from utils import ask_ai_async

router = Router()

# FSM States
class TestingStates(StatesGroup):
    testing_words = State()
    testing_questions = State()

@router.message(lambda message: message.text in ["Почати тестування", "Пройти заново тестування"])
async def start_testing(message: types.Message, state: FSMContext, db):
    """Початок тестування"""
    await message.answer(
        "Ви обрали 'Почати тестування'.\n"
        "Спочатку оцініть ваше знання слів, потім пройдете тест з питаннями.",
        reply_markup=ReplyKeyboardRemove()
    )
    
    # Отримати випадкові слова
    random_words = await db.get_random_words(total_count=7)
    
    # Зберегти слова, результати та user_id в FSM
    await state.update_data(
        words=random_words,
        current_word_index=0,
        word_results=[],
        user_id=message.from_user.id
    )
    
    # Почати тестування слів
    await show_next_word(message, state, db)

async def show_next_word(message: types.Message, state: FSMContext, db):
    """Показати наступне слово з інлайн кнопками"""
    data = await state.get_data()
    words = data.get('words', [])
    current_index = data.get('current_word_index', 0)
    
    if current_index >= len(words):
        # Перейти до питань
        await start_questions_phase(message, state, db)
        return
    
    current_word = words[current_index]
    
    keyboard = get_word_answer_keyboard(current_index)
    
    await message.answer(
        f"📝 Слово {current_index + 1}/{len(words)}\n\n"
        f"🇬🇧 <b>{current_word.word}</b>\n"
        f"🇺🇦 <span class=\"tg-spoiler\">{current_word.translation}</span>\n\n"
        f"Рівень: {current_word.level_english}",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    
    await state.set_state(TestingStates.testing_words)

@router.callback_query(F.data.startswith("answer_"))
async def process_word_answer(callback: types.CallbackQuery, state: FSMContext, db):
    """Обробити відповідь користувача на слово"""
    await callback.answer()
    
    data = await state.get_data()
    words = data.get('words', [])
    current_index = data.get('current_word_index', 0)
    results = data.get('word_results', [])
    
    answer_type = callback.data.split('_')[1]
    
    current_word = words[current_index]
    results.append({
        'word': current_word.word,
        'translation': current_word.translation,
        'level': current_word.level_english,
        'answer': answer_type
    })
    
    await state.update_data(
        current_word_index=current_index + 1,
        word_results=results
    )
    
    try:
        await callback.message.delete()
    except Exception as e:
        logging.warning(f"Could not delete message: {e}")
    
    await show_next_word(callback.message, state, db)

async def start_questions_phase(message: types.Message, state: FSMContext, db):
    """Почати етап з питаннями"""
    await message.answer(
        "✅ Етап зі словами завершено!\n\n"
        "Тепер пройдемо тестування з питаннями по темах."
    )
    
    # Отримати питання (по 1 з кожної теми для кожного рівня)
    questions = await db.get_questions_for_testing()
    print(f"Fetched {len(questions)} questions for testing.")
    
    await state.update_data(
        questions=questions,
        current_question_index=0,
        question_results=[]
    )
    
    await show_next_question(message, state, db)

async def show_next_question(message: types.Message, state: FSMContext, db):
    """Показати наступне питання"""
    data = await state.get_data()
    questions = data.get('questions', [])
    current_index = data.get('current_question_index', 0)
    
    if current_index >= len(questions):
        # Тестування завершено
        await finish_testing(message, state, db)
        return
    
    current_question = questions[current_index]
    
    # Парсити неправильні відповіді
    try:
        wrong_answers = json.loads(current_question.wrong_answers)
    except:
        wrong_answers = []
    
    keyboard = get_question_answer_keyboard(
        current_question.id,
        current_question.answer,
        wrong_answers
    )
    
    await message.answer(
        f"❓ Питання {current_index + 1}/{len(questions)}\n\n"
        f"<b>{current_question.question}</b>\n\n"
        f"📚 Тема: {current_question.topic}\n"
        f"📊 Рівень: {current_question.level_english}",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    
    await state.set_state(TestingStates.testing_questions)

@router.callback_query(F.data.startswith("q_"))
async def process_question_answer(callback: types.CallbackQuery, state: FSMContext, db):
    """Обробити відповідь на питання"""
    await callback.answer()
    
    data = await state.get_data()
    questions = data.get('questions', [])
    current_index = data.get('current_question_index', 0)
    results = data.get('question_results', [])
    
    # Формат: q_<question_id>_<correct/wrong>
    parts = callback.data.split('_')
    is_correct = parts[2] == 'correct'
    
    current_question = questions[current_index]
    results.append({
        'question': current_question.question,
        'topic': current_question.topic,
        'level': current_question.level_english,
        'is_correct': is_correct
    })
    
    await state.update_data(
        current_question_index=current_index + 1,
        question_results=results
    )
    
    try:
        await callback.message.delete()
    except Exception as e:
        logging.warning(f"Could not delete message: {e}")
    
    await show_next_question(callback.message, state, db)

async def finish_testing(message: types.Message, state: FSMContext, db):
    """Завершити тестування та визначити рівень"""
    logging.info(f"User level determination started.")

    data = await state.get_data()
    word_results = data.get('word_results', [])
    question_results = data.get('question_results', [])
    user_id = data.get('user_id')
    
    await message.answer("⏳ Тестування завершено! Обробляю результати...")
    
    # Визначити рівень через ChatGPT
    logging.info(f"Determining level for user {user_id}")
    level = await determine_english_level(word_results, question_results)
    logging.info(f"Determined level for user {user_id}: {level}")
    
    # Статистика по словах
    know_count = sum(1 for r in word_results if r['answer'] == 'know')
    forgot_count = sum(1 for r in word_results if r['answer'] == 'forgot')
    dont_know_count = sum(1 for r in word_results if r['answer'] == 'dont')
    
    # Статистика по питаннях
    correct_questions = sum(1 for r in question_results if r['is_correct'])
    total_questions = len(question_results)
    
    # Зберегти результати в базу даних
    total_all = len(word_results) + total_questions
    correct_all = know_count + (forgot_count // 2) + correct_questions
    
    try:
        await db.update_user_progress(
            user_id=user_id,
            level_english=level,
            total_questions=total_all,
            correct_answers=correct_all
        )
        logging.info(f"User {user_id} progress saved: level={level}")
    except Exception as e:
        logging.error(f"Error saving user progress: {e}")
    
    from handlers.basic import get_appropriate_keyboard
    keyboard = await get_appropriate_keyboard(db, user_id)
    
    await message.answer(
        f"🎉 <b>Результати тестування:</b>\n\n"
        f"📚 <b>Слова:</b>\n"
        f"✅ Знаю: {know_count}\n"
        f"🤔 Не згадав: {forgot_count}\n"
        f"❌ Не знаю: {dont_know_count}\n\n"
        f"❓ <b>Питання:</b>\n"
        f"✅ Правильних: {correct_questions}/{total_questions}\n"
        f"❌ Неправильних: {total_questions - correct_questions}\n\n"
        f"🎓 <b>Ваш рівень англійської: {level}</b>\n\n"
        f"💾 Результати збережено у вашому профілі!",
        parse_mode="HTML",
        reply_markup=keyboard
    )
    
    await state.clear()

async def determine_english_level(word_results: list, question_results: list) -> str:
    """Визначити рівень англійської через ChatGPT"""
    try:
        # Підготувати дані для аналізу
        word_analysis = []
        for result in word_results:
            status = {
                'know': 'знає',
                'forgot': 'не згадав',
                'dont': 'не знає'
            }.get(result['answer'], 'невідомо')
            
            word_analysis.append(
                f"Слово: {result['word']} (рівень {result['level']}) - {status}"
            )
        
        question_analysis = []
        for result in question_results:
            status = 'правильно' if result['is_correct'] else 'неправильно'
            question_analysis.append(
                f"Тема: {result['topic']}, рівень {result['level']} - {status}"
            )
        
        prompt = f"""Ти експерт з визначення рівня англійської мови.
Користувач пройшов тест на знання слів та питань різних рівнів (A0, A1, A2, B1, B2, C1, C2).

Результати по словах:
{chr(10).join(word_analysis)}

Результати по питаннях:
{chr(10).join(question_analysis)}

Проаналізуй результати та визнач рівень англійської мови користувача.
ВАЖЛИВО: У відповіді напиши ТІЛЬКИ один рівень з цього списку: A0, A1, A2, B1, B2, C1, C2
Нічого більше не пиши, тільки рівень."""

        level = await ask_ai_async(prompt)
        print(f"Determined level from GPT: {level}")
        
        valid_levels = ["A0", "A1", "A2", "B1", "B2", "C1", "C2"]
        if level in valid_levels:
            return level
        else:
            for valid_level in valid_levels:
                if valid_level in level:
                    return valid_level
            return "A1"
            
    except Exception as e:
        logging.error(f"Error determining level: {e}")
        # Fallback
        word_know = sum(1 for r in word_results if r['answer'] == 'know')
        question_correct = sum(1 for r in question_results if r['is_correct'])
        total = len(word_results) + len(question_results)
        percentage = ((word_know + question_correct) / total) * 100
        
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
