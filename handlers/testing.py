import logging
import json
import random
from aiogram import types, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardRemove

from keyboards.reply import kb_with_level  # Замість kb_start
from keyboards.inline import get_word_answer_keyboard, get_question_answer_keyboard
from utils import ask_ai_async

router = Router()

# FSM States
class TestingStates(StatesGroup):
    testing_words = State()
    testing_questions = State()
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
    raw_questions = await db.get_questions_sequence()
    question_payloads = []
    for question in raw_questions:
        try:
            wrong_answers = json.loads(question.wrong_answers) if question.wrong_answers else []
        except json.JSONDecodeError:
            wrong_answers = []
        options = [*wrong_answers, question.answer]
        options = list(dict.fromkeys(options))
        random.shuffle(options)
        question_payloads.append({
            "id": question.id,
            "question": question.question,
            "options": options,
            "answer": question.answer,
            "topic": question.topic,
            "level": question.level_english,
            "explanation": question.explanation,
        })
    # Зберегти слова, результати та user_id в FSM
    await state.update_data(
        words=random_words,
        word_index=0,
        word_results=[],
        questions=question_payloads,
        question_index=0,
        question_results=[],
        user_id=message.from_user.id
    )
    
    # Почати тестування
    await show_next_word(message, state, db)

async def show_next_word(message: types.Message, state: FSMContext, db):
    """Показати наступне слово з інлайн кнопками"""
    data = await state.get_data()
    words = data.get('words', [])
    word_index = data.get('word_index', 0)
    
    if word_index >= len(words):
        # Тестування завершено
        await show_next_question(message, state, db)
        return
    
    current_word = words[word_index]
    
    # Створити інлайн кнопки
    keyboard = get_word_answer_keyboard(word_index)
    
    # Відправити слово
    await message.answer(
        f"Слово {word_index + 1}/{len(words)}\n\n"
        f"🇬🇧 <b>{current_word.word}</b>\n"
        f"🇺🇦 <span class=\"tg-spoiler\">{current_word.translation}</span>\n\n"
        f"Рівень: {current_word.level_english}",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    
    await state.set_state(TestingStates.testing_words)

async def show_next_question(message: types.Message, state: FSMContext, db):
    """Показати наступне питання з інлайн кнопками"""
    data = await state.get_data()
    questions = data.get('questions', [])
    question_index = data.get('question_index', 0)
    
    if question_index >= len(questions):
        # Тестування завершено
        await finish_testing(message, state, db)
        return
    
    current_question = questions[question_index]
    
    # Створити інлайн кнопки
    keyboard = get_question_answer_keyboard(question_index, current_question['options'])

    # Відправити питання
    await message.answer(
        f"Питання {question_index + 1}/{len(questions)}\n\n"
        f"{current_question['question']}\n\n"
        f"Рівень: {current_question['level']} | Тема: {current_question['topic']}",
        reply_markup=keyboard
    )
    await state.set_state(TestingStates.testing_questions)

@router.callback_query(F.data.startswith("answer_"))
async def process_answer(callback: types.CallbackQuery, state: FSMContext, db):
    """Обробити відповідь користувача"""
    # Відповісти на callback ОДРАЗУ (до будь-яких довгих операцій)
    await callback.answer()
    
    parts = callback.data.split('_')
    if len(parts) < 3:
        return

    answer_scope = parts[1]
    data = await state.get_data()

    if answer_scope == "word":
        try:
            answer_type = parts[2]
            word_index = int(parts[3])
        except (IndexError, ValueError):
            return
        words = data.get('words', [])
        if word_index >= len(words):
            return
        current_word = words[word_index]
        word_results = data.get('word_results', [])
        word_results.append({
            'word': current_word.word,
            'translation': current_word.translation,
            'level': current_word.level_english,
            'answer': answer_type
        })
        await state.update_data(
            word_index=word_index + 1,
            word_results=word_results
        )
        # Видалити попереднє повідомлення
        try:
            await callback.message.delete()
        except Exception as e:
            logging.warning(f"Could not delete message: {e}")
        # Показати наступне слово
        await show_next_word(callback.message, state, db)
        return

    if answer_scope == "question":
        try:
            question_index = int(parts[2])
            option_index = int(parts[3])
        except (IndexError, ValueError):
            return
        questions = data.get('questions', [])
        if question_index >= len(questions):
            return
        current_question = questions[question_index]
        options = current_question['options']
        if option_index >= len(options):
            return
        selected_option = options[option_index]
        is_correct = selected_option == current_question['answer']
        question_results = data.get('question_results', [])
        question_results.append({
            'question_id': current_question['id'],
            'question': current_question['question'],
            'selected': selected_option,
            'correct_answer': current_question['answer'],
            'topic': current_question['topic'],
            'level': current_question['level'],
            'is_correct': is_correct
        })
        await state.update_data(
            question_index=question_index + 1,
            question_results=question_results
        )
        # Видалити попереднє повідомлення
        try:
            await callback.message.delete()
        except Exception as e:
            logging.warning(f"Could not delete message: {e}")
        feedback = "✅ Правильно!" if is_correct else f"❌ Неправильно. Правильна відповідь: {current_question['answer']}"
        if current_question.get('explanation'):
            feedback += f"\nℹ️ {current_question['explanation']}"
        await callback.message.answer(feedback)
        await show_next_question(callback.message, state, db)

async def finish_testing(message: types.Message, state: FSMContext, db):
    """Завершити тестування та визначити рівень"""
    # info logging
    logging.info(f"User level determination started.")

    data = await state.get_data()
    word_results = data.get('word_results', [])
    question_results = data.get('question_results', [])
    user_id = data.get('user_id')
    
    await message.answer("⏳ Тестування завершено! Обробляю результати...")
    
    # Визначити рівень через ChatGPT
    logging.info(f"Determining level for user {user_id} with {len(word_results)} words and {len(question_results)} questions.")
    level = await determine_english_level(word_results, question_results)
    logging.info(f"Determined level for user {user_id}: {level}")
    
    know_count = sum(1 for r in word_results if r['answer'] == 'know')
    forgot_count = sum(1 for r in word_results if r['answer'] == 'forgot')
    dont_know_count = sum(1 for r in word_results if r['answer'] == 'dont')
    question_correct = sum(1 for r in question_results if r['is_correct'])
    question_total = len(question_results)

    total_questions = len(word_results) + question_total
    correct_answers = know_count + (forgot_count // 2) + question_correct
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
    
    stats_lines = [
        f"✅ Знаю: {know_count}",
        f"🤔 Не згадав: {forgot_count}",
        f"❌ Не знаю: {dont_know_count}",
    ]
    if question_total:
        stats_lines.append(f"🧠 Питання: {question_correct}/{question_total} правильно")
    stats_block = "\n".join(stats_lines)
    summary_text = (
        "🎉 <b>Результати тестування:</b>\n\n"
        "📊 Статистика:\n"
        f"{stats_block}\n\n"
        f"🎓 <b>Ваш рівень англійської: {level}</b>\n\n"
        "💾 Результати збережено у вашому профілі!"
    )

    await message.answer(summary_text, parse_mode="HTML", reply_markup=keyboard)
    
    # Очистити стан
    await state.clear()

async def determine_english_level(word_results: list, question_results: list | None = None) -> str:
    question_results = question_results or []
    try:
        # Підготувати дані для аналізу
        analysis_data = []
        for result in word_results:
            status = {
                'know': 'знає',
                'forgot': 'не згадав',
                'dont': 'не знає'
            }.get(result['answer'], 'невідомо')
            
            analysis_data.append(
                f"Слово: {result['word']} (рівень {result['level']}) - {status}"
            )

        words_block = chr(10).join(analysis_data) if analysis_data else "Результати по словах відсутні."

        question_analysis = []
        for result in question_results:
            status = "правильно" if result['is_correct'] else "неправильно"
            question_analysis.append(
                f"Рівень {result['level']} | Тема {result['topic']} - {status}"
            )

        questions_block = ""
        if question_analysis:
            questions_block = f"\n\nРезультати питань:\n{chr(10).join(question_analysis)}"

        prompt = f"""Ти експерт з визначення рівня англійської мови.
Користувач пройшов тест на знання слів різних рівнів (A0, A1, A2, B1, B2, C1, C2).

Результати тесту:
{words_block}{questions_block}

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
        know_count = sum(1 for r in word_results if r['answer'] == 'know')
        forgot_count = sum(1 for r in word_results if r['answer'] == 'forgot')
        question_correct = sum(1 for r in question_results if r['is_correct'])
        total_items = len(word_results) + len(question_results)
        if total_items == 0:
            return "A1"
        partial_score = know_count + question_correct + (forgot_count * 0.5)
        percentage = (partial_score / total_items) * 100

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
