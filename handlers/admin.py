from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from keyboards.reply import kb_admin_panel, kb_with_level
from keyboards.inline import get_user_info_keyboard

router = Router()

# FSM для пошуку користувача
class AdminStates(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_admin_id = State()

@router.message(lambda message: message.text == "👑 Адмін панель")
async def show_admin_panel(message: types.Message, db):
    """Показати адмін-панель"""
    user_id = message.from_user.id
    
    # Перевірити чи є користувач адміном
    is_admin = await db.is_user_admin(user_id)
    
    if not is_admin:
        await message.answer(
            "❌ У вас немає доступу до адмін-панелі.",
            reply_markup=kb_with_level
        )
        return
    
    await message.answer(
        "👑 <b>АДМІН ПАНЕЛЬ</b>\n\n"
        "Оберіть дію:",
        reply_markup=kb_admin_panel,
        parse_mode="HTML"
    )

@router.message(lambda message: message.text == "📊 Статистика слів")
async def admin_words_statistics(message: types.Message, db):
    """Показати статистику слів для адміна"""
    user_id = message.from_user.id
    
    # Перевірити права
    is_admin = await db.is_user_admin(user_id)
    if not is_admin:
        await message.answer("❌ Немає доступу")
        return
    
    # Отримати статистику
    words_stats = await db.get_words_statistics()
    
    stats_text = (
        f"📊 <b>СТАТИСТИКА СЛІВ</b>\n\n"
        f"📚 Всього слів в базі: <b>{words_stats['total']}</b>\n\n"
        f"<b>По рівнях:</b>\n"
    )
    
    for level in ["A0", "A1", "A2", "B1", "B2", "C1", "C2"]:
        count = words_stats['by_level'].get(level, 0)
        percentage = (count / words_stats['total'] * 100) if words_stats['total'] > 0 else 0
        stats_text += f"  {level}: {count} слів ({percentage:.1f}%)\n"
    
    await message.answer(stats_text, parse_mode="HTML")

@router.message(lambda message: message.text == "❓ Статистика питань")
async def admin_questions_statistics(message: types.Message, db):
    """Показати статистику питань для адміна"""
    user_id = message.from_user.id
    
    # Перевірити права
    is_admin = await db.is_user_admin(user_id)
    if not is_admin:
        await message.answer("❌ Немає доступу")
        return
    
    # Отримати статистику
    questions_stats = await db.get_questions_statistics()
    
    stats_text = (
        f"📊 <b>СТАТИСТИКА ПИТАНЬ</b>\n\n"
        f"❓ Всього питань в базі: <b>{questions_stats['total']}</b>\n\n"
        f"<b>По рівнях:</b>\n"
    )
    
    for level in ["A1", "A2", "B1", "B2", "C1", "C2"]:
        count = questions_stats['by_level'].get(level, 0)
        percentage = (count / questions_stats['total'] * 100) if questions_stats['total'] > 0 else 0
        stats_text += f"  {level}: {count} питань ({percentage:.1f}%)\n"
    
    await message.answer(stats_text, parse_mode="HTML")

@router.message(lambda message: message.text == "👥 Статистика користувачів")
async def admin_users_statistics(message: types.Message, db):
    """Показати статистику користувачів для адміна"""
    user_id = message.from_user.id
    
    # Перевірити права
    is_admin = await db.is_user_admin(user_id)
    if not is_admin:
        await message.answer("❌ Немає доступу")
        return
    
    # Отримати статистику
    users_stats = await db.get_users_statistics()
    
    stats_text = (
        f"📊 <b>СТАТИСТИКА КОРИСТУВАЧІВ</b>\n\n"
        f"👥 Всього користувачів: <b>{users_stats['total']}</b>\n"
        f"📈 З прогресом: <b>{users_stats['with_progress']}</b>\n"
        f"⭐️ Преміум ТГ: <b>{users_stats['premium']}</b>\n"
        f"👑 Адміністраторів: <b>{users_stats['admins']}</b>\n\n"
        f"<b>По рівнях:</b>\n"
    )
    
    for level in ["A0", "A1", "A2", "B1", "B2", "C1", "C2"]:
        count = users_stats['by_level'].get(level, 0)
        percentage = (count / users_stats['with_progress'] * 100) if users_stats['with_progress'] > 0 else 0
        stats_text += f"  {level}: {count} користувачів ({percentage:.1f}%)\n"
    
    await message.answer(stats_text, parse_mode="HTML")

@router.message(lambda message: message.text == "🔍 Знайти користувача")
async def admin_find_user_request(message: types.Message, state: FSMContext, db):
    """Запит на пошук користувача"""
    user_id = message.from_user.id
    
    # Перевірити права
    is_admin = await db.is_user_admin(user_id)
    if not is_admin:
        await message.answer("❌ Немає доступу")
        return
    
    await state.set_state(AdminStates.waiting_for_user_id)
    await message.answer(
        "🔍 <b>Пошук користувача</b>\n\n"
        "Введіть Telegram ID користувача:",
        parse_mode="HTML"
    )

@router.message(AdminStates.waiting_for_user_id)
async def admin_find_user_process(message: types.Message, state: FSMContext, db):
    """Обробка пошуку користувача"""
    try:
        tg_id = int(message.text)
    except ValueError:
        await message.answer("❌ Невірний формат ID. Введіть число.")
        return
    
    # Знайти користувача
    user = await db.find_user_by_telegram_id(tg_id)
    
    if not user:
        await message.answer(
            f"❌ Користувача з ID <code>{tg_id}</code> не знайдено.",
            parse_mode="HTML"
        )
        await state.clear()
        return
    
    # Отримати повну інформацію
    user_info = await db.get_user_full_info(user.user_id)
    
    if not user_info:
        await message.answer("❌ Помилка отримання інформації")
        await state.clear()
        return
    
    # Сформувати повідомлення
    user_data = user_info['user']
    progress_data = user_info['progress']
    word_stats = user_info['word_stats']
    
    # Перевірити чи є користувач адміном
    is_target_admin = user_data.is_admin
    
    info_text = (
        f"👤 <b>ІНФОРМАЦІЯ ПРО КОРИСТУВАЧА</b>\n\n"
        f"<b>Основне:</b>\n"
        f"  • ID: <code>{user_data.user_id}</code>\n"
        f"  • Telegram ID: <code>{user_data.tg_id}</code>\n"
        f"  • Ім'я: {user_data.first_name} {user_data.last_name or ''}\n"
        f"  • Username: @{user_data.username or 'немає'}\n"
        f"  • Premium: {'✅' if user_data.tg_premium else '❌'}\n"
        f"  • Адмін: {'👑 ТАК' if is_target_admin else '❌ НІ'}\n"
        f"  • Дата реєстрації: {user_data.registration_date.strftime('%d.%m.%Y %H:%M')}\n\n"
    )
    
    if progress_data:
        info_text += (
            f"<b>Прогрес:</b>\n"
            f"  • Рівень: <b>{progress_data.level_english}</b>\n"
            f"  • Слів вивчено: {word_stats['total']}\n"
            f"  • Засвоєно слів: {word_stats['mastered']}\n"
            f"  • Точність слів: {word_stats['accuracy']:.1f}%\n"
            f"  • Питань пройдено: {progress_data.total_questions_answered}\n"
            f"  • Правильних відповідей: {progress_data.correct_answers}\n"
            f"  • Точність питань: {progress_data.accuracy:.1f}%\n"
            f"  • Сьогодні слів: {progress_data.words_studied_today}\n"
            f"  • Сьогодні питань: {progress_data.questions_answered_today}\n"
        )
    else:
        info_text += "<b>Прогрес:</b> Немає даних\n"
    
    # Передати is_target_admin в клавіатуру
    await message.answer(
        info_text,
        reply_markup=get_user_info_keyboard(user_data.user_id, is_target_admin=is_target_admin),
        parse_mode="HTML"
    )
    
    await state.clear()

# @router.message(lambda message: message.text == "👤 Призначити адміна")
# async def admin_make_admin_request(message: types.Message, state: FSMContext, db):
#     """Запит на призначення адміна"""
#     user_id = message.from_user.id
    
#     # Перевірити права
#     is_admin = await db.is_user_admin(user_id)
#     if not is_admin:
#         await message.answer("❌ Немає доступу")
#         return
    
#     await state.set_state(AdminStates.waiting_for_admin_id)
#     await message.answer(
#         "👤 <b>Призначення адміністратора</b>\n\n"
#         "Введіть Telegram ID користувача, якого хочете зробити адміном:",
#         parse_mode="HTML"
#     )

@router.message(AdminStates.waiting_for_admin_id)
async def admin_make_admin_process(message: types.Message, state: FSMContext, db):
    """Обробка призначення адміна"""
    try:
        tg_id = int(message.text)
    except ValueError:
        await message.answer("❌ Невірний формат ID. Введіть число.")
        return
    
    # Знайти користувача
    user = await db.find_user_by_telegram_id(tg_id)
    
    if not user:
        await message.answer(
            f"❌ Користувача з ID <code>{tg_id}</code> не знайдено.",
            parse_mode="HTML"
        )
        await state.clear()
        return
    
    # Призначити адміном
    success = await db.set_user_admin(user.user_id, True)
    
    if success:
        await message.answer(
            f"✅ Користувача <b>{user.first_name}</b> (ID: <code>{tg_id}</code>) призначено адміністратором!",
            parse_mode="HTML"
        )
    else:
        await message.answer("❌ Помилка при призначенні адміністратора")
    
    await state.clear()

@router.callback_query(F.data.startswith("admin_make_"))
async def admin_make_admin_inline(callback: types.CallbackQuery, db):
    """Призначити адміна через inline кнопку"""
    requester_id = callback.from_user.id
    
    # Перевірити права
    is_admin = await db.is_user_admin(requester_id)
    if not is_admin:
        await callback.answer("❌ Немає доступу", show_alert=True)
        return
    
    # Отримати user_id з callback_data
    target_user_id = int(callback.data.split('_')[2])
    
    # Призначити адміном
    success = await db.set_user_admin(target_user_id, True)
    
    if success:
        await callback.answer("✅ Користувача призначено адміном!", show_alert=True)
        await callback.message.edit_text(
            f"{callback.message.text}\n\n"
            f"✅ <b>Користувача призначено адміністратором!</b>",
            parse_mode="HTML"
        )
    else:
        await callback.answer("❌ Помилка", show_alert=True)

@router.callback_query(F.data.startswith("admin_remove_"))
async def admin_remove_admin_inline(callback: types.CallbackQuery, db):
    """Зняти адміна через inline кнопку"""
    requester_id = callback.from_user.id
    
    # Перевірити права
    is_admin = await db.is_user_admin(requester_id)
    if not is_admin:
        await callback.answer("❌ Немає доступу", show_alert=True)
        return
    
    # Отримати user_id з callback_data
    target_user_id = int(callback.data.split('_')[2])
    
    # Зняти адміна
    success = await db.set_user_admin(target_user_id, False)
    
    if success:
        await callback.answer("✅ Адміна знято!", show_alert=True)
        await callback.message.edit_text(
            f"{callback.message.text}\n\n"
            f"✅ <b>Адміністратора знято!</b>",
            parse_mode="HTML"
        )
    else:
        await callback.answer("❌ Помилка", show_alert=True)

@router.callback_query(F.data.startswith("admin_reset_"))
async def admin_reset_user_inline(callback: types.CallbackQuery, db):
    """Скинути прогрес користувача через inline кнопку"""
    requester_id = callback.from_user.id
    
    # Перевірити права
    is_admin = await db.is_user_admin(requester_id)
    if not is_admin:
        await callback.answer("❌ Немає доступу", show_alert=True)
        return
    
    # Отримати user_id з callback_data
    target_user_id = int(callback.data.split('_')[2])
    
    # Скинути прогрес
    success = await db.reset_user_progress(target_user_id)
    
    if success:
        await callback.answer("✅ Прогрес скинуто!", show_alert=True)
        await callback.message.edit_text(
            f"{callback.message.text}\n\n"
            f"✅ <b>Прогрес користувача скинуто!</b>",
            parse_mode="HTML"
        )
    else:
        await callback.answer("❌ Помилка", show_alert=True)

@router.message(lambda message: message.text == "◀️ Назад до головного меню")
async def admin_back_to_main(message: types.Message, db):
    """Повернутись з адмін-панелі"""
    user_id = message.from_user.id
    
    # Отримати відповідну клавіатуру
    from handlers.basic import get_appropriate_keyboard
    keyboard = await get_appropriate_keyboard(db, user_id)
    
    await message.answer(
        "↩️ Повернулись до головного меню.",
        reply_markup=keyboard
    )
