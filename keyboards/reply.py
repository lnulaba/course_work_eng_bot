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

# Клавіатура для користувачів з визначеним рівнем
kb_with_level = types.ReplyKeyboardMarkup(
    keyboard=[
        [
            types.KeyboardButton(text="Пройти заново тестування"),
        ],
        [
            types.KeyboardButton(text="Змінити рівень самому"),
            types.KeyboardButton(text="Статистика"),
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
