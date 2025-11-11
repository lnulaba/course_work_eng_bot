from aiogram import types
import random

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

def get_question_answer_keyboard(question_id: int, correct_answer: str, wrong_answers: list) -> types.InlineKeyboardMarkup:
    """Створити інлайн клавіатуру з варіантами відповідей на питання"""
    # Об'єднати правильну та неправильні відповіді
    all_answers = wrong_answers + [correct_answer]
    random.shuffle(all_answers)
    
    # Створити кнопки
    buttons = []
    for answer in all_answers:
        is_correct = answer == correct_answer
        callback_data = f"q_{question_id}_{'correct' if is_correct else 'wrong'}"
        buttons.append([types.InlineKeyboardButton(text=answer, callback_data=callback_data)])
    
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard
