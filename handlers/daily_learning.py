from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import json
import os
from aiogram.types import FSInputFile

from keyboards.reply import kb_with_level, kb_learning_words, kb_practicing_questions
from keyboards.inline import get_daily_word_keyboard, get_level_up_keyboard, get_daily_question_keyboard, get_next_question_keyboard

router = Router()

# FSM для щоденного навчання слів
class DailyWords(StatesGroup):
    learning = State()

# FSM для щоденних питань
class DailyQuestions(StatesGroup):
    answering = State()

@router.message(lambda message: message.text in ["📚 Вивчати слова (50/день)", "📚 Вивчати слова"])
async def start_daily_words(message: types.Message, state: FSMContext, db):
    """Почати щоденне вивчення слів"""
    user_id = message.from_user.id
    
    # Перевірити прогрес користувача
    progress = await db.get_user_progress(user_id)
    
    if not progress:
        # Отримати відповідну клавіатуру
        from handlers.basic import get_appropriate_keyboard
        keyboard = await get_appropriate_keyboard(db, user_id)
        
        await message.answer(
            "❌ Спочатку пройдіть тестування для визначення вашого рівня!",
            reply_markup=keyboard
        )
        return
    
    # Отримати ліміти користувача
    limits = await db.get_user_limits(user_id)
    daily_limit = limits['words']
    
    # Перевірити чи не перевищено ліміт
    if progress.words_studied_today >= daily_limit:
        await message.answer(
            f"✅ Ви вже вивчили {daily_limit} слів сьогодні!\n\n"
            f"Повертайтесь завтра для нових слів 📚",
            reply_markup=kb_with_level
        )
        return
    
    # Отримати слова (використовуємо ліміт з налаштувань)
    words = await db.get_daily_words(user_id)
    
    if not words:
        await message.answer(
            "❌ Немає доступних слів для вашого рівня.\n"
            "Спробуйте пізніше або зверніться до адміністратора.",
            reply_markup=kb_with_level
        )
        return
    
    # Зберегти в FSM
    await state.set_state(DailyWords.learning)
    await state.update_data(
        words=words,
        current_index=0,
        stats={'easy': 0, 'know': 0, 'hard': 0, 'new': 0},
        daily_limit=daily_limit
    )
    
    # Показати перше слово з клавіатурою
    await show_word(message, state, db, 0, words)

async def show_word(message: types.Message, state: FSMContext, db, index: int, words: list):
    """Показати слово користувачу"""
    if index >= len(words):
        await finish_daily_words(message, state, db)
        return
    
    word = words[index]
    
    # Отримати ліміт з FSM
    data = await state.get_data()
    daily_limit = data.get('daily_limit', 50)
    
    text = (
        f"📝 Слово {index + 1}/{daily_limit}\n\n"
        f"🇬🇧 <b>{word.word}</b>\n\n"
        f"Наскільки добре ви знаєте це слово?"
    )
    
    # Перевірити чи є аудіо
    audio_path = f"files/audios/{word.word}.mp3"
    
    if os.path.exists(audio_path):
        # Відправити з аудіо
        audio = FSInputFile(audio_path)
        await message.answer_voice(
            voice=audio,
            caption=text,
            reply_markup=get_daily_word_keyboard(word.word_id),
            parse_mode="HTML"
        )
    else:
        # Відправити тільки текст
        await message.answer(
            text,
            reply_markup=get_daily_word_keyboard(word.word_id),
            parse_mode="HTML"
        )
    
    # Показати клавіатуру з кнопкою завершення (тільки для першого слова)
    # if index == 0:
    #     await message.answer(
    #         "Ви можете завершити навчання в будь-який момент ⬇️",
    #         reply_markup=kb_learning_words
    #     )

@router.callback_query(F.data.startswith("word_"))
async def process_word_answer(callback: types.CallbackQuery, state: FSMContext, db):
    """Обробити відповідь користувача на слово"""
    user_id = callback.from_user.id
    
    # Розпарсити callback_data: word_{type}_{word_id}
    parts = callback.data.split('_')
    answer_type = parts[1]  # easy, know, hard, new
    word_id = int(parts[2])
    
    # Зберегти відповідь
    await db.save_word_answer(user_id, word_id, answer_type)
    
    # Оновити статистику в FSM
    data = await state.get_data()
    stats = data.get('stats', {'easy': 0, 'know': 0, 'hard': 0, 'new': 0})
    stats[answer_type] = stats.get(answer_type, 0) + 1
    
    current_index = data.get('current_index', 0)
    words = data.get('words', [])
    daily_limit = data.get('daily_limit', 50)
    
    # Показати переклад
    word = next((w for w in words if w.word_id == word_id), None)
    if word:
        translation_text = (
            f"📝 Слово {current_index + 1}/{daily_limit}\n\n"
            f"🇬🇧 <b>{word.word}</b>\n"
            f"🇺🇦 {word.translation}\n\n"
            f"{'⭐️ Чудово!' if answer_type == 'easy' else '✅ Добре!' if answer_type == 'know' else '📖 Продовжуйте вчити!' if answer_type == 'hard' else '🆕 Нове слово!'}"
        )
        
        # Перевірити чи це голосове повідомлення
        if callback.message.voice:
            # Редагувати caption для голосового
            await callback.message.edit_caption(
                caption=translation_text,
                parse_mode="HTML"
            )
        else:
            # Редагувати текст для звичайного повідомлення
            await callback.message.edit_text(
                translation_text,
                parse_mode="HTML"
            )
    
    # Перейти до наступного слова
    next_index = current_index + 1
    await state.update_data(current_index=next_index, stats=stats)
    
    # Невелика затримка перед видаленням
    import asyncio
    await asyncio.sleep(2.5)
    
    # Видалити попереднє повідомлення
    try:
        await callback.message.delete()
    except:
        pass
    
    if next_index < len(words):
        await show_word(callback.message, state, db, next_index, words)
    else:
        await finish_daily_words(callback.message, state, db)

@router.message(lambda message: message.text == "🛑 Завершити вивчення слів")
async def stop_learning_words(message: types.Message, state: FSMContext, db):
    """Дострокове завершення навчання слів"""
    # Перевірити чи користувач в режимі навчання
    current_state = await state.get_state()
    
    if current_state != DailyWords.learning:
        # Отримати відповідну клавіатуру
        from handlers.basic import get_appropriate_keyboard
        keyboard = await get_appropriate_keyboard(db, message.from_user.id)
        
        await message.answer(
            "Ви не в режимі навчання слів.",
            reply_markup=keyboard
        )
        return
    
    # Показати статистику і завершити
    data = await state.get_data()
    stats = data.get('stats', {'easy': 0, 'know': 0, 'hard': 0, 'new': 0})
    current_index = data.get('current_index', 0)
    
    total_studied = stats['easy'] + stats['know'] + stats['hard'] + stats['new']
    
    stats_text = (
        f"🛑 <b>Навчання завершено достроково</b>\n\n"
        f"📊 <b>Статистика:</b>\n"
        f"  Вивчено слів: {total_studied}\n"
        f"  ⭐️ Легко: {stats['easy']}\n"
        f"  ✅ Знаю: {stats['know']}\n"
        f"  ❓ Складно: {stats['hard']}\n"
        f"  ❌ Не знаю: {stats['new']}\n\n"
        f"Повертайтесь пізніше для продовження навчання! 📚"
    )
    
    # Отримати відповідну клавіатуру
    from handlers.basic import get_appropriate_keyboard
    keyboard = await get_appropriate_keyboard(db, message.from_user.id)
    
    await message.answer(stats_text, parse_mode="HTML", reply_markup=keyboard)
    await state.clear()

async def finish_daily_words(message: types.Message, state: FSMContext, db):
    """Завершити щоденне навчання слів"""
    user_id = message.from_user.id if hasattr(message, 'from_user') else message.chat.id
    
    data = await state.get_data()
    stats = data.get('stats', {'easy': 0, 'know': 0, 'hard': 0, 'new': 0})
    
    # Отримати відповідну клавіатуру
    from handlers.basic import get_appropriate_keyboard
    keyboard = await get_appropriate_keyboard(db, user_id)
    
    # Показати статистику
    stats_text = (
        f"🎉 <b>Вітаю! Ви завершили щоденне навчання!</b>\n\n"
        f"📊 <b>Статистика:</b>\n"
        f"  ⭐️ Легко: {stats['easy']}\n"
        f"  ✅ Знаю: {stats['know']}\n"
        f"  ❓ Складно: {stats['hard']}\n"
        f"  ❌ Не знаю: {stats['new']}\n\n"
        f"Повертайтесь завтра для нових слів! 📚"
    )
    
    await message.answer(stats_text, parse_mode="HTML", reply_markup=keyboard)
    
    # Перевірити можливість переходу на наступний рівень
    can_level_up = await db.check_level_up_eligibility(user_id)
    
    if can_level_up:
        progress = await db.get_user_progress(user_id)
        await suggest_level_up(message, db, progress.level_english)
    else:
        await message.answer(
            "Продовжуйте вчити! 💪",
            reply_markup=kb_with_level
        )
    
    await state.clear()

async def suggest_level_up(message: types.Message, db, current_level: str):
    """Запропонувати перехід на наступний рівень"""
    LEVELS = ["A0", "A1", "A2", "B1", "B2", "C1", "C2"]
    
    current_index = LEVELS.index(current_level)
    if current_index >= len(LEVELS) - 1:
        await message.answer(
            "🎓 Ви досягли максимального рівня! Вітаємо! 🎉",
            reply_markup=kb_with_level
        )
        return
    
    next_level = LEVELS[current_index + 1]
    user_id = message.from_user.id
    
    # Отримати статистику
    word_stats = await db.get_user_word_stats(user_id)
    progress = await db.get_user_progress(user_id)
    
    await message.answer(
        f"🎉 <b>Вітаю! Ваші результати чудові!</b>\n\n"
        f"📊 <b>Статистика:</b>\n"
        f"• Слова засвоєно: {word_stats['mastered']}/{word_stats['total']}\n"
        f"• Точність слова: {word_stats['accuracy']:.1f}%\n"
        f"• Точність питань: {progress.accuracy:.1f}%\n\n"
        f"🚀 Рекомендуємо перейти на рівень <b>{next_level}</b>!",
        reply_markup=get_level_up_keyboard(next_level),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("levelup_"))
async def process_level_up(callback: types.CallbackQuery, db):
    """Обробити рішення про перехід на новий рівень"""
    user_id = callback.from_user.id
    
    if callback.data == "levelup_stay":
        await callback.message.edit_text(
            "✅ Ви залишились на поточному рівні.\n"
            "Продовжуйте вчити! 💪"
        )
        await callback.message.answer(
            "Оберіть дію:",
            reply_markup=kb_with_level
        )
        return
    
    # Отримати новий рівень
    new_level = callback.data.split('_')[1]
    
    # Оновити рівень
    progress = await db.get_user_progress(user_id)
    await db.update_user_progress(
        user_id=user_id,
        level_english=new_level,
        total_questions=0,
        correct_answers=0
    )
    
    await callback.message.edit_text(
        f"🎉 <b>Вітаємо!</b>\n\n"
        f"Ваш новий рівень: <b>{new_level}</b>\n\n"
        f"Тепер ви можете вивчати слова та проходити питання нового рівня!",
        parse_mode="HTML"
    )
    
    await callback.message.answer(
        "Оберіть дію:",
        reply_markup=kb_with_level
    )

@router.message(lambda message: message.text in ["❓ Практика питань (30/день)", "❓ Практика питань"])
async def start_daily_questions(message: types.Message, state: FSMContext, db):
    """Почати щоденну практику питань"""
    user_id = message.from_user.id
    
    # Перевірити прогрес
    progress = await db.get_user_progress(user_id)
    
    if not progress:
        await message.answer(
            "❌ Спочатку пройдіть тестування для визначення вашого рівня!",
            reply_markup=kb_with_level
        )
        return
    
    # Отримати ліміти користувача
    limits = await db.get_user_limits(user_id)
    daily_limit = limits['questions']
    
    # Перевірити ліміт
    if progress.questions_answered_today >= daily_limit:
        await message.answer(
            f"✅ Ви вже відповіли на {daily_limit} питань сьогодні!\n\n"
            f"Повертайтесь завтра для нових питань ❓",
            reply_markup=kb_with_level
        )
        return
    
    # Отримати питання (використовуємо ліміт з налаштувань)
    questions = await db.get_daily_questions(user_id)
    
    if not questions:
        await message.answer(
            "❌ Немає доступних питань для вашого рівня.\n"
            "Спробуйте пізніше або зверніться до адміністратора.",
            reply_markup=kb_with_level
        )
        return
    
    # Зберегти в FSM
    await state.set_state(DailyQuestions.answering)
    await state.update_data(
        questions=questions,
        current_index=0,
        stats={'correct': 0, 'wrong': 0},
        daily_limit=daily_limit
    )
    
    # Показати перше питання
    await show_daily_question(message, state, db, 0, questions)

async def show_daily_question(message: types.Message, state: FSMContext, db, index: int, questions: list):
    """Показати питання користувачу"""
    if index >= len(questions):
        # Всі питання пройдено
        await finish_daily_questions(message, state, db)
        return
    
    question = questions[index]
    
    # Отримати ліміт з FSM
    data = await state.get_data()
    daily_limit = data.get('daily_limit', 30)
    
    # Парсити неправильні відповіді
    try:
        wrong_answers = json.loads(question.wrong_answers)
    except:
        wrong_answers = []
    
    keyboard = get_daily_question_keyboard(
        question.id,
        question.answer,
        wrong_answers
    )
    
    await message.answer(
        f"❓ Питання {index + 1}/{daily_limit}\n\n"
        f"<b>{question.question}</b>\n\n"
        f"📚 Тема: {question.topic}\n"
        f"📊 Рівень: {question.level_english}",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    
    # Показати клавіатуру з кнопкою завершення (тільки для першого питання)
    if index == 0:
        await message.answer(
            "Ви можете завершити практику в будь-який момент ⬇️",
            reply_markup=kb_practicing_questions
        )

@router.callback_query(F.data.startswith("daily_q_"))
async def process_daily_question_answer(callback: types.CallbackQuery, state: FSMContext, db):
    """Обробити відповідь на щоденне питання"""
    user_id = callback.from_user.id
    
    # Розпарсити callback_data: daily_q_{question_id}_{correct/wrong}_{answer_index}
    parts = callback.data.split('_')
    question_id = int(parts[2])
    is_correct = parts[3] == 'correct'
    
    # Отримати дані з FSM
    data = await state.get_data()
    questions = data.get('questions', [])
    current_index = data.get('current_index', 0)
    stats = data.get('stats', {'correct': 0, 'wrong': 0})
    daily_limit = data.get('daily_limit', 30)
    
    # Знайти поточне питання
    current_question = questions[current_index]
    
    # Зберегти відповідь в базу
    await db.save_question_answer(user_id, question_id, is_correct)
    
    # Оновити статистику
    if is_correct:
        stats['correct'] += 1
    else:
        stats['wrong'] += 1
    
    # Оновити індекс
    next_index = current_index + 1
    await state.update_data(current_index=next_index, stats=stats)
    
    if is_correct:
        # Правильна відповідь - одразу наступне питання
        await callback.message.edit_text(
            f"✅ <b>Правильно!</b>\n\n"
            f"Питання {current_index + 1}/{daily_limit}\n\n"
            f"<b>{current_question.question}</b>\n\n"
            f"✔️ Відповідь: <b>{current_question.answer}</b>",
            parse_mode="HTML"
        )
        
        # Невелика затримка
        import asyncio
        await asyncio.sleep(1.5)
        
        if next_index < len(questions):
            await show_daily_question(callback.message, state, db, next_index, questions)
        else:
            await finish_daily_questions(callback.message, state, db)
    else:
        # Неправильна відповідь - показати пояснення та кнопку
        explanation_text = (
            f"❌ <b>Неправильно</b>\n\n"
            f"Питання {current_index + 1}/{daily_limit}\n\n"
            f"<b>{current_question.question}</b>\n\n"
            f"✔️ Правильна відповідь: <b>{current_question.answer}</b>\n"
        )
        
        # Додати пояснення якщо є
        if current_question.explanation:
            explanation_text += f"\n💡 <b>Пояснення:</b>\n{current_question.explanation}"
        
        await callback.message.edit_text(
            explanation_text,
            reply_markup=get_next_question_keyboard(),
            parse_mode="HTML"
        )

@router.callback_query(F.data == "next_daily_question")
async def show_next_daily_question(callback: types.CallbackQuery, state: FSMContext, db):
    """Показати наступне питання після неправильної відповіді"""
    await callback.answer()
    
    data = await state.get_data()
    questions = data.get('questions', [])
    current_index = data.get('current_index', 0)
    
    # Видалити попереднє повідомлення
    try:
        await callback.message.delete()
    except:
        pass
    
    if current_index < len(questions):
        await show_daily_question(callback.message, state, db, current_index, questions)
    else:
        await finish_daily_questions(callback.message, state, db)

@router.message(lambda message: message.text == "🛑 Завершити практику питань")
async def stop_practicing_questions(message: types.Message, state: FSMContext, db):
    """Дострокове завершення практики питань"""
    # Перевірити чи користувач в режимі практики
    current_state = await state.get_state()
    
    if current_state != DailyQuestions.answering:
        await message.answer(
            "Ви не в режимі практики питань.",
            reply_markup=kb_with_level
        )
        return
    
    # Показати статистику і завершити
    data = await state.get_data()
    stats = data.get('stats', {'correct': 0, 'wrong': 0})
    
    total_answered = stats['correct'] + stats['wrong']
    accuracy = (stats['correct'] / total_answered * 100) if total_answered > 0 else 0
    
    stats_text = (
        f"🛑 <b>Практика завершена достроково</b>\n\n"
        f"📊 <b>Результати:</b>\n"
        f"  Питань пройдено: {total_answered}\n"
        f"  ✅ Правильних: {stats['correct']}\n"
        f"  ❌ Неправильних: {stats['wrong']}\n"
        f"  📈 Точність: {accuracy:.1f}%\n\n"
        f"Повертайтесь пізніше для продовження практики! 📝"
    )
    
    await message.answer(stats_text, parse_mode="HTML", reply_markup=kb_with_level)
    await state.clear()

async def finish_daily_questions(message: types.Message, state: FSMContext, db):
    """Завершити щоденну практику питань"""
    user_id = message.from_user.id if hasattr(message, 'from_user') else message.chat.id
    
    data = await state.get_data()
    stats = data.get('stats', {'correct': 0, 'wrong': 0})
    daily_limit = data.get('daily_limit', 30)
    
    total = stats['correct'] + stats['wrong']
    accuracy = (stats['correct'] / total * 100) if total > 0 else 0
    
    # Показати статистику
    stats_text = (
        f"🎉 <b>Вітаю! Ви завершили щоденну практику!</b>\n\n"
        f"📊 <b>Результати:</b>\n"
        f"  ✅ Правильних: {stats['correct']}\n"
        f"  ❌ Неправильних: {stats['wrong']}\n"
        f"  📈 Точність: {accuracy:.1f}%\n\n"
        f"{'🔥 Чудовий результат!' if accuracy >= 80 else '💪 Продовжуйте тренуватись!' if accuracy >= 60 else '📚 Приділіть більше уваги вивченню!'}\n\n"
        f"Повертайтесь завтра для нових питань! 📝"
    )
    
    await message.answer(stats_text, parse_mode="HTML", reply_markup=kb_with_level)
    
    # Перевірити можливість переходу на наступний рівень
    can_level_up = await db.check_level_up_eligibility(user_id)
    
    if can_level_up:
        progress = await db.get_user_progress(user_id)
        await suggest_level_up(message, db, progress.level_english)
    else:
        await message.answer(
            "Продовжуйте вчити! 💪",
            reply_markup=kb_with_level
        )
    
    await state.clear()
