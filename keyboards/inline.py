from aiogram import types

def get_word_answer_keyboard(current_index: int) -> types.InlineKeyboardMarkup:
    """Створити інлайн клавіатуру для відповіді на слово"""
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(text="✅ Знаю", callback_data=f"answer_know_{current_index}"),
            types.InlineKeyboardButton(text="🤔 Не згадав", callback_data=f"answer_forgot_{current_index}"),
            types.InlineKeyboardButton(text="❌ Не знаю", callback_data=f"answer_dont_know_{current_index}")
        ]
    ])
    return keyboard
