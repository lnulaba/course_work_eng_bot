from aiogram import types

def get_word_answer_keyboard(current_index: int) -> types.InlineKeyboardMarkup:
    """Створити інлайн клавіатуру для відповіді на слово"""
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(text="✅ Знаю", callback_data=f"answer_word_know_{current_index}"),
            types.InlineKeyboardButton(text="🤔 Не згадав", callback_data=f"answer_word_forgot_{current_index}"),
            types.InlineKeyboardButton(text="❌ Не знаю", callback_data=f"answer_word_dont_{current_index}")
        ]
    ])
    return keyboard

def get_question_answer_keyboard(question_index: int, options) -> types.InlineKeyboardMarkup:
    """Створити інлайн клавіатуру для відповіді на питання"""
    rows = [
        [types.InlineKeyboardButton(text=option, callback_data=f"answer_question_{question_index}_{idx}")]
        for idx, option in enumerate(options)
    ]
    return types.InlineKeyboardMarkup(inline_keyboard=rows)
