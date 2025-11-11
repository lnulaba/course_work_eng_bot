from aiogram import types, Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from keyboards.reply import (
    kb_unregistered, 
    kb_no_level, 
    kb_with_level, 
    kb_select_level,
    kb_settings,
    get_main_keyboard
)
from keyboards.inline import get_reset_confirmation_keyboard

router = Router()

# FSM для вибору рівня
class LevelSelection(StatesGroup):
    selecting_level = State()

# FSM для налаштування нагадувань
class ReminderSettings(StatesGroup):
    waiting_for_time = State()

async def get_appropriate_keyboard(db, user_id):
    """Отримати відповідну клавіатуру залежно від стану користувача"""
    user = await db.get_user(user_id)
    
    if not user:
        return kb_unregistered
    
    progress = await db.get_user_progress(user_id)
    
    if not progress:
        return kb_no_level
    
    # Перевірити чи є користувач адміном
    is_admin = await db.is_user_admin(user_id)
    return get_main_keyboard(is_admin=is_admin)

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
            f"Тепер ви можете вивчати слова та проходити питання цього рівня.",
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
    
    # Отримати ліміти користувача
    limits = await db.get_user_limits(user_id)
    
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
        message_text += f"\n🎓 <b>Поточний рівень: {progress.level_english}</b>\n"
        
        # Статистика слів користувача
        user_word_stats = await db.get_user_word_stats(user_id)
        
        message_text += f"\n📚 <b>Слова:</b>\n"
        message_text += f"  • Сьогодні вивчено: {progress.words_studied_today}/{limits['words']}\n"
        message_text += f"  • Всього на рівні: {user_word_stats['total']}\n"
        message_text += f"  • Засвоєно (lvl 3-4): {user_word_stats['mastered']}\n"
        message_text += f"  • Точність: {user_word_stats['accuracy']:.1f}%\n"
        
        message_text += f"\n❓ <b>Питання:</b>\n"
        message_text += f"  • Сьогодні пройдено: {progress.questions_answered_today}/{limits['questions']}\n"
        message_text += f"  • Всього: {progress.total_questions_answered}\n"
        message_text += f"  • Правильно: {progress.correct_answers}\n"
        message_text += f"  • Точність: {progress.accuracy:.1f}%\n"
        
        # Прогрес до наступного рівня
        can_level_up = await db.check_level_up_eligibility(user_id)
        if can_level_up:
            message_text += f"\n📈 <b>✅ Ви готові до переходу на наступний рівень!</b>\n"
        else:
            # Показати що потрібно
            min_words_needed = max(0, 100 - user_word_stats['total'])
            # min_mastered_needed = max(0, 50 - user_word_stats['mastered'])
            
            message_text += f"\n📈 <b>Прогрес до наступного рівня:</b>\n"
            if min_words_needed > 0:
                message_text += f"  • Вивчіть ще {min_words_needed} слів\n"
            # if min_mastered_needed > 0:
            #     message_text += f"  • Засвойте ще {min_mastered_needed} слів (lvl 3+)\n"
            # if user_word_stats['accuracy'] < 60:
            #     message_text += f"  • Покращте точність слів до 60%\n"
            # if progress.accuracy < 60:
            #     message_text += f"  • Покращте точність питань до 60%\n"
    else:
        message_text += f"\n🎓 <b>Ваш прогрес:</b>\n"
        message_text += f"  Пройдіть тестування для визначення рівня!\n"
    
    await message.answer(message_text, parse_mode="HTML")

@router.message(lambda message: message.text == "⚙️ Налаштування")
async def show_settings(message: types.Message, db):
    """Показати меню налаштувань"""
    user_id = message.from_user.id
    progress = await db.get_user_progress(user_id)
    
    if not progress:
        await message.answer(
            "❌ Спочатку пройдіть тестування!",
            reply_markup=kb_with_level
        )
        return
    
    settings_text = (
        f"⚙️ <b>НАЛАШТУВАННЯ</b>\n\n"
        f"🎓 Поточний рівень: <b>{progress.level_english}</b>\n"
        f"📊 Точність: {progress.accuracy:.1f}%\n"
        f"📚 Слів вивчено: {progress.words_studied_today}\n"
        f"❓ Питань пройдено: {progress.questions_answered_today}\n\n"
        f"Оберіть дію:"
    )
    
    await message.answer(
        settings_text,
        reply_markup=kb_settings,
        parse_mode="HTML"
    )

@router.message(lambda message: message.text == "🔄 Пройти тестування заново")
async def restart_testing_from_settings(message: types.Message, state: FSMContext, db):
    """Перенаправити на тестування"""
    await message.answer(
        "🔄 Ви будете перенаправлені на тестування.\n"
        "Ваш рівень буде оновлено після проходження тесту.",
        reply_markup=kb_with_level
    )
    
    # Імпортуємо handler тестування
    from handlers.testing import start_testing
    await start_testing(message, state, db)

@router.message(lambda message: message.text == "📊 Змінити рівень вручну")
async def change_level_from_settings(message: types.Message, state: FSMContext):
    """Перенаправити на зміну рівня"""
    await state.set_state(LevelSelection.selecting_level)
    await message.answer(
        "Оберіть новий рівень англійської мови:",
        reply_markup=kb_select_level
    )

@router.message(lambda message: message.text == "🗑️ Скинути весь прогрес")
async def request_reset_progress(message: types.Message, db):
    """Запитати підтвердження скидання прогресу"""
    user_id = message.from_user.id
    progress = await db.get_user_progress(user_id)
    word_stats = await db.get_user_word_stats(user_id)
    
    warning_text = (
        f"⚠️ <b>УВАГА!</b>\n\n"
        f"Ви впевнені, що хочете скинути весь прогрес?\n\n"
        f"<b>Буде видалено:</b>\n"
        f"• Рівень: {progress.level_english if progress else 'не встановлено'}\n"
        f"• Слів вивчено: {word_stats['total']}\n"
        f"• Засвоєних слів: {word_stats['mastered']}\n"
        f"• Питань пройдено: {progress.total_questions_answered if progress else 0}\n"
        f"• Точність: {progress.accuracy:.1f}% if progress else 0\n\n"
        f"❗️ Цю дію <b>неможливо</b> скасувати!"
    )
    
    await message.answer(
        warning_text,
        reply_markup=get_reset_confirmation_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "reset_confirm")
async def confirm_reset_progress(callback: types.CallbackQuery, db):
    """Підтвердження скидання прогресу"""
    user_id = callback.from_user.id
    
    try:
        await db.reset_user_progress(user_id)
        
        await callback.message.edit_text(
            "✅ <b>Прогрес успішно скинуто!</b>\n\n"
            "Тепер ви можете пройти тестування заново.",
            parse_mode="HTML"
        )

    except Exception as e:
        await callback.message.edit_text(
            f"❌ Помилка при скиданні прогресу: {e}\n\n"
            "Спробуйте ще раз або зверніться до адміністратора.",
            parse_mode="HTML"
        )
        
        await callback.message.answer(
            "Повертаємось до налаштувань.",
            reply_markup=kb_settings
        )

@router.callback_query(F.data == "reset_cancel")
async def cancel_reset_progress(callback: types.CallbackQuery):
    """Скасування скидання прогресу"""
    await callback.message.edit_text(
        "✅ Скидання прогресу скасовано.\n"
        "Ваші дані збережено."
    )
    
    await callback.message.answer(
        "Повертаємось до налаштувань.",
        reply_markup=kb_settings
    )

@router.message(lambda message: message.text == "◀️ Повернутись назад")
async def back_from_settings(message: types.Message, db):
    """Повернутись з налаштувань"""
    user_id = message.from_user.id
    keyboard = await get_appropriate_keyboard(db, user_id)
    
    await message.answer(
        "↩️ Повернулись до головного меню.",
        reply_markup=keyboard
    )

@router.message(lambda message: message.text == "🔔 Налаштування нагадувань")
async def show_reminder_settings(message: types.Message, db):
    """Показати налаштування нагадувань"""
    user_id = message.from_user.id
    
    # Отримати поточні налаштування
    settings = await db.get_user_reminder_settings(user_id)
    
    status_text = "✅ Увімкнено" if settings['enabled'] else "❌ Вимкнено"
    
    settings_text = (
        f"🔔 <b>НАЛАШТУВАННЯ НАГАДУВАНЬ</b>\n\n"
        f"📊 Поточні налаштування:\n"
        f"  • Статус: {status_text}\n"
        f"  • Час нагадування: {settings['time']}\n\n"
        f"<b>Команди:</b>\n"
        f"  /reminder_on - Увімкнути нагадування\n"
        f"  /reminder_off - Вимкнути нагадування\n"
        f"  /reminder_time - Змінити час нагадування\n\n"
        f"💡 Нагадування допоможе вам не забувати про щоденне навчання!"
    )
    
    await message.answer(settings_text, parse_mode="HTML")

@router.message(Command("reminder_on"))
async def enable_reminder(message: types.Message, db):
    """Увімкнути нагадування"""
    user_id = message.from_user.id
    
    success = await db.update_user_reminder_settings(user_id, enabled=True)
    
    if success:
        settings = await db.get_user_reminder_settings(user_id)
        await message.answer(
            f"✅ Нагадування увімкнено!\n\n"
            f"⏰ Час нагадування: {settings['time']}\n\n"
            f"Ви отримуватимете щоденне нагадування про навчання.",
            parse_mode="HTML"
        )
    else:
        await message.answer("❌ Помилка при увімкненні нагадувань")

@router.message(Command("reminder_off"))
async def disable_reminder(message: types.Message, db):
    """Вимкнути нагадування"""
    user_id = message.from_user.id
    
    success = await db.update_user_reminder_settings(user_id, enabled=False)
    
    if success:
        await message.answer(
            "❌ Нагадування вимкнено.\n\n"
            "Ви можете увімкнути їх знову командою /reminder_on"
        )
    else:
        await message.answer("❌ Помилка при вимкненні нагадувань")

@router.message(Command("reminder_time"))
async def request_reminder_time(message: types.Message, state: FSMContext):
    """Запит на зміну часу нагадування"""
    await state.set_state(ReminderSettings.waiting_for_time)
    
    await message.answer(
        "⏰ <b>Зміна часу нагадування</b>\n\n"
        "Введіть новий час у форматі <b>HH:MM</b> (24-годинний формат)\n\n"
        "Наприклад:\n"
        "  • 09:00 - о 9 ранку\n"
        "  • 18:30 - о 6:30 вечора\n"
        "  • 21:00 - о 9 вечора\n\n"
        "Або натисніть /cancel для скасування",
        parse_mode="HTML"
    )

@router.message(ReminderSettings.waiting_for_time)
async def process_reminder_time(message: types.Message, state: FSMContext, db):
    """Обробка зміни часу нагадування"""
    user_id = message.from_user.id
    time_input = message.text.strip()
    
    # Валідація формату HH:MM
    try:
        hour, minute = time_input.split(':')
        hour = int(hour)
        minute = int(minute)
        
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError
        
        # Форматувати час
        formatted_time = f"{hour:02d}:{minute:02d}"
        
        # Зберегти новий час
        success = await db.update_user_reminder_settings(user_id, time=formatted_time)
        
        if success:
            await message.answer(
                f"✅ Час нагадування оновлено!\n\n"
                f"⏰ Новий час: <b>{formatted_time}</b>\n\n"
                f"Ви отримуватимете щоденне нагадування о цій годині.",
                parse_mode="HTML"
            )
        else:
            await message.answer("❌ Помилка при збереженні часу")
        
        await state.clear()
    
    except ValueError:
        await message.answer(
            "❌ Невірний формат часу!\n\n"
            "Використовуйте формат <b>HH:MM</b> (24-годинний)\n"
            "Наприклад: 09:00 або 18:30\n\n"
            "Спробуйте ще раз або натисніть /cancel для скасування",
            parse_mode="HTML"
        )

@router.message(Command("cancel"))
async def cancel_handler(message: types.Message, state: FSMContext, db):
    """Скасувати поточну дію"""
    current_state = await state.get_state()
    
    if current_state is None:
        await message.answer("Немає активних дій для скасування.")
        return
    
    await state.clear()
    
    keyboard = await get_appropriate_keyboard(db, message.from_user.id)
    await message.answer(
        "✅ Дію скасовано.",
        reply_markup=keyboard
    )
