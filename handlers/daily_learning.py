from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from keyboards.reply import kb_with_level
from keyboards.inline import get_daily_word_keyboard, get_level_up_keyboard

router = Router()

# FSM для щоденного навчання слів
class DailyWords(StatesGroup):
    learning = State()

# FSM для щоденних питань
class DailyQuestions(StatesGroup):
    answering = State()

@router.message(lambda message: message.text == "📚 Вивчати слова (50/день)")
async def start_daily_words(message: types.Message, state: FSMContext, db):
    """Почати щоденне вивчення 50 слів"""
    user_id = message.from_user.id
    
    # Перевірити прогрес користувача
    progress = await db.get_user_progress(user_id)
    
    if not progress:
        await message.answer(
            "❌ Спочатку пройдіть тестування для визначення вашого рівня!",
            reply_markup=kb_with_level
        )
        return
    
    # Перевірити чи не перевищено ліміт
    if progress.words_studied_today >= 50:
        await message.answer(
            f"✅ Ви вже вивчили 50 слів сьогодні!\n\n"
            f"Повертайтесь завтра для нових слів 📚",
            reply_markup=kb_with_level
        )
        return
    
    # Отримати слова
    words = await db.get_daily_words(user_id, limit=50)
    
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
        stats={'easy': 0, 'know': 0, 'hard': 0, 'new': 0}
    )
    
    # Показати перше слово
    await show_word(message, state, db, 0, words)

async def show_word(message: types.Message, state: FSMContext, db, index: int, words: list):
    """Показати слово користувачу"""
    if index >= len(words):
        # Всі слова пройдено
        await finish_daily_words(message, state, db)
        return
    
    word = words[index]
    
    await message.answer(
        f"📝 Слово {index + 1}/50\n\n"
        f"🇬🇧 <b>{word.word}</b>\n\n"
        f"Наскільки добре ви знаєте це слово?",
        reply_markup=get_daily_word_keyboard(word.word_id),
        parse_mode="HTML"
    )

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
    
    # Показати переклад
    word = next((w for w in words if w.word_id == word_id), None)
    if word:
        await callback.message.edit_text(
            f"📝 Слово {current_index + 1}/50\n\n"
            f"🇬🇧 <b>{word.word}</b>\n"
            f"🇺🇦 {word.translation}\n\n"
            f"{'⭐️ Чудово!' if answer_type == 'easy' else '✅ Добре!' if answer_type == 'know' else '📖 Продовжуйте вчити!' if answer_type == 'hard' else '🆕 Нове слово!'}"
            ,
            parse_mode="HTML"
        )
    
    # Перейти до наступного слова
    next_index = current_index + 1
    await state.update_data(current_index=next_index, stats=stats)
    
    # Невелика затримка перед наступним словом
    import asyncio
    await asyncio.sleep(1)
    
    if next_index < len(words):
        await show_word(callback.message, state, db, next_index, words)
    else:
        await finish_daily_words(callback.message, state, db)

async def finish_daily_words(message: types.Message, state: FSMContext, db):
    """Завершити щоденне навчання слів"""
    user_id = message.from_user.user_id if hasattr(message, 'from_user') else message.chat.id
    
    data = await state.get_data()
    stats = data.get('stats', {'easy': 0, 'know': 0, 'hard': 0, 'new': 0})
    
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
    
    await message.answer(stats_text, parse_mode="HTML")
    
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

@router.message(lambda message: message.text == "❓ Практика питань (30/день)")
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
    
    # Перевірити ліміт
    if progress.questions_answered_today >= 30:
        await message.answer(
            f"✅ Ви вже відповіли на 30 питань сьогодні!\n\n"
            f"Повертайтесь завтра для нових питань ❓",
            reply_markup=kb_with_level
        )
        return
    
    # Отримати питання
    questions = await db.get_daily_questions(user_id, limit=30)
    
    if not questions:
        await message.answer(
            "❌ Немає доступних питань для вашого рівня.\n"
            "Спробуйте пізніше або зверніться до адміністратора.",
            reply_markup=kb_with_level
        )
        return
    
    await message.answer(
        f"🎯 <b>Щоденна практика</b>\n\n"
        f"Рівень: {progress.level_english}\n"
        f"Питань: 30\n\n"
        f"Функція в розробці... 🚧",
        reply_markup=kb_with_level,
        parse_mode="HTML"
    )
