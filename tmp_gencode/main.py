import asyncio
import logging
from typing import Dict
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

from db import *
from controllers import (
    UserController, WordLearningController, ChatGPTController,
    TestController, StatisticsController, SettingsController
)

import asyncio
import logging
import os
from typing import Dict
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

# Завантажити змінні середовища
load_dotenv()

from db import *
from controllers import (
    UserController, WordLearningController, ChatGPTController,
    TestController, StatisticsController, SettingsController
)

# Налаштування логування
logging.basicConfig(level=logging.INFO)

# Ініціалізація бота
BOT_TOKEN = os.getenv("BOT_TOKEN", "7365678598:AAHAMFBVPRR5etj4Fdt3TTLnmWJSDNbrWFQ")
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Глобальні змінні для контролерів
user_controller = None
word_controller = None
chatgpt_controller = None
test_controller = None
stats_controller = None
settings_controller = None

# Стани FSM для різних операцій
class LearningStates(StatesGroup):
    word_learning = State()
    testing = State()
    settings_change = State()

# Основні клавіатури
def get_main_menu_keyboard():
    """Головне меню згідно з діаграмою активності"""
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [
                types.KeyboardButton(text="📚 Вивчення слів"),
                types.KeyboardButton(text="🧠 Генерація тестів")
            ],
            [
                types.KeyboardButton(text="📊 Моя статистика"),
                types.KeyboardButton(text="⚙️ Налаштування")
            ],
            [
                types.KeyboardButton(text="📖 Читання"),
                types.KeyboardButton(text="🎯 Тест на рівень")
            ]
        ],
        resize_keyboard=True
    )

def get_word_answer_keyboard():
    """Клавіатура для відповідей на слова"""
    return types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(text="💡 Знаю", callback_data="word_know"),
                types.InlineKeyboardButton(text="❌ Не знаю", callback_data="word_unknown")
            ],
            [
                types.InlineKeyboardButton(text="🔊 Аудіо", callback_data="word_audio")
            ]
        ]
    )

def get_level_keyboard():
    """Клавіатура для вибору рівня"""
    return types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(text="A0", callback_data="level_A0"),
                types.InlineKeyboardButton(text="A1", callback_data="level_A1"),
                types.InlineKeyboardButton(text="A2", callback_data="level_A2")
            ],
            [
                types.InlineKeyboardButton(text="B1", callback_data="level_B1"),
                types.InlineKeyboardButton(text="B2", callback_data="level_B2")
            ],
            [
                types.InlineKeyboardButton(text="C1", callback_data="level_C1"),
                types.InlineKeyboardButton(text="C2", callback_data="level_C2")
            ]
        ]
    )

# ==================== ОБРОБНИК КОМАНДИ /START ====================

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """
    Обробка команди /start згідно з алгоритмом реєстрації (блок-схема 1)
    """
    # Реєстрація або отримання існуючого користувача
    is_new_user, user_data = await user_controller.handle_user_registration(message)
    
    if 'blocked' in user_data:
        await message.answer(
            "🚫 Ваш акаунт заблокований.\n"
            "📞 Зверніться до адміністратора для відновлення доступу."
        )
        return
    
    if 'error' in user_data:
        await message.answer(
            "🚨 Помилка створення акаунту.\n"
            "🔄 Спробуйте ще раз через хвилину."
        )
        return
    
    if is_new_user:
        # Новий користувач - вітальне повідомлення
        await message.answer(
            f"Привіт, {user_data['full_name'] or 'друже'}! 👋\n\n"
            "🎯 Я English Learning Bot!\n\n"
            "📚 Допоможу тобі вивчити англійську мову\n"
            "🧠 Можу генерувати тести з ChatGPT\n"
            "📊 Відстежую твій прогрес\n"
            "🎵 Маю аудіо для вимови слів\n\n"
            "🎉 Реєстрація завершена!\n"
            f"📈 Твій поточний рівень: {user_data['level_english']}"
        )
        
        # Запропонувати початковий тест
        await message.answer(
            "🎯 Хочеш пройти тест для точного визначення рівня?\n\n"
            "📋 Тест включає:\n"
            "• 40 слів різної складності\n"
            "• 20 граматичних питань\n"
            "• 10 питань на розуміння тексту\n\n"
            "Або можемо одразу почати навчання!",
            reply_markup=types.InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        types.InlineKeyboardButton(text="🎯 Пройти тест", callback_data="initial_test"),
                        types.InlineKeyboardButton(text="📚 Почати навчання", callback_data="start_learning")
                    ]
                ]
            )
        )
    else:
        # Існуючий користувач
        await message.answer(
            f"Вітаю знову, {user_data['full_name'] or 'друже'}! 👋\n\n"
            f"📈 Твій рівень: {user_data['level_english']}\n"
            f"📊 Точність: {user_data['accuracy']:.1f}%\n\n"
            "Що будемо вивчати сьогодні?",
            reply_markup=get_main_menu_keyboard()
        )

# ==================== ОБРОБНИКИ ГОЛОВНОГО МЕНЮ ====================

@dp.message(F.text == "📚 Вивчення слів")
async def handle_word_learning(message: types.Message, state: FSMContext):
    """Початок вивчення слів згідно з блок-схемою 3"""
    user_id = message.from_user.id
    
    # Отримати рівень користувача
    user_data = await user_controller.db.get_user(user_id)
    if not user_data:
        await message.answer("❌ Помилка: користувач не знайдений")
        return
    
    level = user_data['level_english']
    
    await message.answer(
        f"📚 Почнемо вивчення слів для рівня {level}\n\n"
        "🎯 Я покажу тобі 20 слів\n"
        "💡 Натискай 'Знаю' якщо знаєш слово\n"
        "❌ Натискай 'Не знаю' щоб вивчити\n"
        "🔊 Можеш прослухати вимову\n\n"
        "Готовий? 🚀"
    )
    
    # Почати сесію вивчення слів
    result = await word_controller.start_word_learning(user_id, level)
    
    if not result['success']:
        await message.answer(
            f"🚨 {result['message']}\n"
            "🔧 Зверніться до адміністратора"
        )
        return
    
    # Показати перше слово
    current_word = result['current_word']
    await message.answer(
        f"📖 Слово {result['progress']}:\n\n"
        f"**{current_word['word']}**\n\n"
        "Знаєш це слово?",
        reply_markup=get_word_answer_keyboard()
    )
    
    await state.set_state(LearningStates.word_learning)

@dp.callback_query(F.data.in_(["word_know", "word_unknown", "word_audio"]), LearningStates.word_learning)
async def handle_word_answer(callback: types.CallbackQuery, state: FSMContext):
    """Обробка відповідей на слова"""
    user_id = callback.from_user.id
    action = callback.data
    
    if action == "word_audio":
        # Відтворити аудіо (тут буде логіка для аудіо)
        await callback.answer("🔊 Аудіо відтворено", show_alert=False)
        return
    
    # Обробити відповідь
    knows_word = action == "word_know"
    result = await word_controller.process_word_answer(user_id, knows_word)
    
    if 'error' in result:
        await callback.message.edit_text("❌ Помилка сесії. Спробуйте почати знову.")
        await state.clear()
        return
    
    # Показати результат відповіді
    if result['result'] == 'correct':
        response_text = f"✅ {result['message']}"
    else:
        response_text = (
            f"📝 **{result['word']}** = {result['translation']}\n\n"
            f"💡 {result['message']}\n"
            "⏱️ Запам'ятовуй 3 секунди..."
        )
        
        # Пауза для запам'ятовування
        await asyncio.sleep(3)
    
    # Перевірити чи сесія завершена
    if 'session_completed' in result:
        await handle_word_session_completed(callback.message, result, state)
        return
    
    # Показати наступне слово
    next_word = result['next_word']
    await callback.message.edit_text(
        f"📖 Слово {result['progress']}:\n\n"
        f"**{next_word['word']}**\n\n"
        "Знаєш це слово?",
        reply_markup=get_word_answer_keyboard()
    )

async def handle_word_session_completed(message: types.Message, result: Dict, state: FSMContext):
    """Обробка завершення сесії вивчення слів"""
    # Показати результати
    results_text = (
        f"🎊 **Сесію завершено!**\n\n"
        f"📊 **Результати:**\n"
        f"✅ Знаю: {result['known_words']}/{result['total_words']}\n"
        f"❌ Вивчаю: {result['unknown_words']}/{result['total_words']}\n"
        f"📈 Точність: {result['accuracy']}%\n"
        f"⏱️ Час: {result['session_duration']}\n\n"
        f"{result['message']}\n"
        f"💡 {result['suggestion']}"
    )
    
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[])
    
    if result['has_unknown_words']:
        keyboard.inline_keyboard.append([
            types.InlineKeyboardButton(text="🔄 Повторити незнайомі", callback_data="repeat_unknown")
        ])
    
    if result['performance_level'] == 'excellent':
        keyboard.inline_keyboard.append([
            types.InlineKeyboardButton(text="🎓 Тест на підвищення", callback_data="level_up_test")
        ])
    
    keyboard.inline_keyboard.append([
        types.InlineKeyboardButton(text="🏠 Головне меню", callback_data="main_menu")
    ])
    
    await message.edit_text(results_text, reply_markup=keyboard)
    await state.clear()

@dp.message(F.text == "🧠 Генерація тестів")
async def handle_test_generation(message: types.Message):
    """Обробка генерації тестів згідно з блок-схемою 2"""
    user_id = message.from_user.id
    
    # Отримати рівень користувача
    user_data = await user_controller.db.get_user(user_id)
    if not user_data:
        await message.answer("❌ Помилка: користувач не знайдений")
        return
    
    level = user_data['level_english']
    
    # Отримати доступні теми
    topics = await test_controller.db.get_topics_by_level(level)
    
    if not topics:
        await message.answer(
            f"🚨 Теми для рівня {level} не знайдені\n"
            "🔧 Зверніться до адміністратора"
        )
        return
    
    # Показати доступні теми
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[])
    
    for topic in topics[:10]:  # Показати максимум 10 тем
        keyboard.inline_keyboard.append([
            types.InlineKeyboardButton(
                text=f"📝 {topic['topic_name']}", 
                callback_data=f"topic_{topic['topic_id']}"
            )
        ])
    
    await message.answer(
        f"🧠 **Генерація тестів через ChatGPT**\n\n"
        f"🎯 Твій рівень: {level}\n\n"
        f"Обери тему для тесту з 20 питань:",
        reply_markup=keyboard
    )

@dp.message(F.text == "📊 Моя статистика")
async def handle_statistics(message: types.Message):
    """Обробка статистики згідно з блок-схемою 4"""
    user_id = message.from_user.id
    
    # Отримати статистику
    stats_result = await stats_controller.get_user_statistics(user_id)
    
    if 'error' in stats_result:
        await message.answer("❌ Помилка отримання статистики")
        return
    
    user_stats = stats_result['user_stats']
    achievements = stats_result['achievements']
    daily_goal = stats_result['daily_goal']
    
    # Сформувати звіт
    stats_text = (
        f"📊 **ТВОЯ СТАТИСТИКА**\n\n"
        f"🎯 Поточний рівень: {user_stats['level_english']}\n"
        f"📈 Загальна точність: {user_stats['accuracy']:.1f}%\n"
        f"✅ Правильних відповідей: {user_stats['correct_answers']}/{user_stats['total_questions_answered']}\n"
        f"🎯 Пройдено сесій: {user_stats['completed_sessions']}/{user_stats['total_sessions']}\n"
        f"🎯 Щоденна ціль: {daily_goal} питань\n\n"
    )
    
    if achievements:
        stats_text += "🏆 **ТВОЇ ДОСЯГНЕННЯ:**\n"
        for achievement in achievements:
            stats_text += f"{achievement}\n"
        stats_text += "\n"
    
    # Рекомендації
    if stats_result['recommendations']:
        stats_text += "💡 **РЕКОМЕНДАЦІЇ:**\n"
        for rec in stats_result['recommendations']:
            stats_text += f"{rec}\n"
    
    # Кнопки
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[])
    
    if stats_result['level_up_ready']:
        keyboard.inline_keyboard.append([
            types.InlineKeyboardButton(text="🎓 Тест на підвищення", callback_data="level_up_test")
        ])
    
    keyboard.inline_keyboard.append([
        types.InlineKeyboardButton(text="🏠 Головне меню", callback_data="main_menu")
    ])
    
    await message.answer(stats_text, reply_markup=keyboard)

@dp.message(F.text == "⚙️ Налаштування")
async def handle_settings(message: types.Message):
    """Обробка налаштувань згідно з блок-схемою 5"""
    user_id = message.from_user.id
    
    # Отримати поточні налаштування
    settings = await settings_controller.get_user_settings(user_id)
    
    settings_text = (
        f"⚙️ **ТВОЇ НАЛАШТУВАННЯ**\n\n"
        f"🌐 Мова інтерфейсу: {settings.get('preferred_language', 'UA')}\n"
        f"🎯 Щоденна ціль: {settings.get('daily_goal', 50)} питань\n"
        f"⏰ Час нагадування: {settings.get('notification_time', '19:00')}\n"
        f"🔊 Звук: {'Увімкнено' if settings.get('sound_enabled', True) else 'Вимкнено'}\n"
        f"📊 Поточний рівень: {settings.get('level_english', 'A0')}\n\n"
        "Що хочеш змінити?"
    )
    
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(text="🌐 Мова", callback_data="settings_language"),
                types.InlineKeyboardButton(text="🎯 Ціль", callback_data="settings_goal")
            ],
            [
                types.InlineKeyboardButton(text="⏰ Час", callback_data="settings_time"),
                types.InlineKeyboardButton(text="🔊 Звук", callback_data="settings_sound")
            ],
            [
                types.InlineKeyboardButton(text="📊 Тест на рівень", callback_data="level_test"),
                types.InlineKeyboardButton(text="🔄 Скинути прогрес", callback_data="reset_progress")
            ],
            [
                types.InlineKeyboardButton(text="🏠 Головне меню", callback_data="main_menu")
            ]
        ]
    )
    
    await message.answer(settings_text, reply_markup=keyboard)

# ==================== CALLBACK ОБРОБНИКИ ====================

@dp.callback_query(F.data == "main_menu")
async def handle_main_menu_callback(callback: types.CallbackQuery, state: FSMContext):
    """Повернення до головного меню"""
    await state.clear()
    await callback.message.delete()
    
    user_data = await user_controller.db.get_user(callback.from_user.id)
    await callback.message.answer(
        f"🏠 **Головне меню**\n\n"
        f"📈 Рівень: {user_data['level_english']}\n"
        f"📊 Точність: {user_data['accuracy']:.1f}%\n\n"
        "Що будемо робити?",
        reply_markup=get_main_menu_keyboard()
    )

@dp.callback_query(F.data.startswith("topic_"))
async def handle_topic_selection(callback: types.CallbackQuery, state: FSMContext):
    """Обробка вибору теми для тесту"""
    topic_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id
    
    await callback.message.edit_text(
        "🤖 Генерую питання через ChatGPT...\n"
        "⏳ Це може зайняти декілька секунд"
    )
    
    # Тут буде логіка початку тесту
    # Поки що заглушка
    await asyncio.sleep(2)
    
    await callback.message.edit_text(
        "🚧 Функція генерації тестів поки що в розробці\n\n"
        "Скоро буде доступна!",
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(text="🏠 Головне меню", callback_data="main_menu")]
            ]
        )
    )

# ==================== ІНІЦІАЛІЗАЦІЯ ====================

async def setup_database():
    """Налаштування бази даних та контролерів"""
    connection = Connection()
    await connection.connect()
    
    db = DB(connection.connection)
    await db.create_tables()
    await db.insert_sample_data()  # Додати тестові дані
    
    # Ініціалізація контролерів
    global user_controller, word_controller, chatgpt_controller
    global test_controller, stats_controller, settings_controller
    
    user_controller = UserController(db)
    word_controller = WordLearningController(db)
    chatgpt_controller = ChatGPTController(db, api_key=None)  # Додати API ключ при потребі
    test_controller = TestController(db, chatgpt_controller)
    stats_controller = StatisticsController(db)
    settings_controller = SettingsController(db)
    
    print("✅ База даних та контролери ініціалізовано")

async def main():
    """Основна функція запуску бота"""
    await setup_database()
    
    print("🚀 Запуск English Learning Bot...")
    print("📚 Функції бота:")
    print("  • Реєстрація користувачів")
    print("  • Вивчення слів з аудіо")
    print("  • Генерація тестів через ChatGPT")
    print("  • Відстеження прогресу")
    print("  • Налаштування користувача")
    print("  • Статистика та аналітика")
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())


