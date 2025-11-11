from aiogram import types

# Клавіатура для незареєстрованих користувачів та без рівня
kb_unregistered = types.ReplyKeyboardMarkup(
    keyboard=[
        [
            types.KeyboardButton(text="Почати тестування"),
        ],
        [
            types.KeyboardButton(text="Інформація про курс"),
            types.KeyboardButton(text="Допомога"),
        ],
        [
            types.KeyboardButton(text="Підтримати розробника"),
        ]
    ],
    resize_keyboard=True,
)

# Така сама клавіатура для користувачів без рівня
kb_no_level = kb_unregistered

# Клавіатура для користувачів з визначеним рівнем (БЕЗ кнопки адмін-панелі)
kb_with_level_no_admin = types.ReplyKeyboardMarkup(
    keyboard=[
        [
            types.KeyboardButton(text="📚 Вивчати слова"),
            types.KeyboardButton(text="❓ Практика питань"),
        ],
        [
            types.KeyboardButton(text="Статистика"),
            types.KeyboardButton(text="⚙️ Налаштування"),
        ],
        [
            types.KeyboardButton(text="Інформація про курс"),
            types.KeyboardButton(text="Допомога"),
        ],
        [
            types.KeyboardButton(text="Підтримати розробника"),
        ]
    ],
    resize_keyboard=True,
)

# Клавіатура для користувачів з визначеним рівнем (З кнопкою адмін-панелі)
kb_with_level = types.ReplyKeyboardMarkup(
    keyboard=[
        [
            types.KeyboardButton(text="📚 Вивчати слова"),
            types.KeyboardButton(text="❓ Практика питань"),
        ],
        [
            types.KeyboardButton(text="Статистика"),
            types.KeyboardButton(text="⚙️ Налаштування"),
        ],
        [
            types.KeyboardButton(text="👑 Адмін панель"),  # Додана кнопка
        ],
        [
            types.KeyboardButton(text="Інформація про курс"),
            types.KeyboardButton(text="Допомога"),
        ],
        [
            types.KeyboardButton(text="Підтримати розробника"),
        ]
    ],
    resize_keyboard=True,
)

# Клавіатура для вибору рівня
kb_select_level = types.ReplyKeyboardMarkup(
    keyboard=[
        [
            types.KeyboardButton(text="A0"),
            types.KeyboardButton(text="A1"),
            types.KeyboardButton(text="A2"),
        ],
        [
            types.KeyboardButton(text="B1"),
            types.KeyboardButton(text="B2"),
        ],
        [
            types.KeyboardButton(text="C1"),
            types.KeyboardButton(text="C2"),
        ],
        [
            types.KeyboardButton(text="Назад"),
        ]
    ],
    resize_keyboard=True,
)

# Клавіатура для режиму навчання слів
kb_learning_words = types.ReplyKeyboardMarkup(
    keyboard=[
        [
            types.KeyboardButton(text="🛑 Завершити вивчення слів"),
        ]
    ],
    resize_keyboard=True,
)

# Клавіатура для режиму практики питань
kb_practicing_questions = types.ReplyKeyboardMarkup(
    keyboard=[
        [
            types.KeyboardButton(text="🛑 Завершити практику питань"),
        ]
    ],
    resize_keyboard=True,
)

# Клавіатура налаштувань
kb_settings = types.ReplyKeyboardMarkup(
    keyboard=[
        [
            types.KeyboardButton(text="🔄 Пройти тестування заново"),
            types.KeyboardButton(text="📊 Змінити рівень вручну"),
        ],
        [
            types.KeyboardButton(text="🔔 Налаштування нагадувань"),
            types.KeyboardButton(text="🗑️ Скинути весь прогрес"),
        ],
        [
            types.KeyboardButton(text="◀️ Повернутись назад"),
        ]
    ],
    resize_keyboard=True,
)

# Клавіатура адмін-панелі
kb_admin_panel = types.ReplyKeyboardMarkup(
    keyboard=[
        [
            types.KeyboardButton(text="📊 Статистика слів"),
            types.KeyboardButton(text="❓ Статистика питань"),
        ],
        [
            types.KeyboardButton(text="👥 Статистика користувачів"),
        ],
        [
            types.KeyboardButton(text="🔍 Знайти користувача"),
            # types.KeyboardButton(text="👤 Призначити адміна"),
        ],
        [
            types.KeyboardButton(text="◀️ Назад до головного меню"),
        ]
    ],
    resize_keyboard=True,
)

# Функція для отримання клавіатури залежно від статусу адміна
def get_main_keyboard(is_admin: bool = False) -> types.ReplyKeyboardMarkup:
    """Отримати головну клавіатуру з урахуванням статусу адміна"""
    if is_admin:
        return kb_with_level
    else:
        return kb_with_level_no_admin
