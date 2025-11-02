"""
Конфігурація для English Learning Bot
Налаштування для роботи з діаграмою активності
"""

import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class DatabaseConfig:
    """Конфігурація бази даних"""
    host: str = "31.222.235.200"
    user: str = "gkevzmyh_martha" 
    password: str = "oC7xQ9cS5e"
    database: str = "gkevzmyh_eng_courses"
    charset: str = "utf8mb4"

@dataclass
class BotConfig:
    """Конфігурація Telegram бота"""
    token: str = "7365678598:AAHAMFBVPRR5etj4Fdt3TTLnmWJSDNbrWFQ"
    webhook_url: Optional[str] = None
    webhook_path: Optional[str] = None
    webhook_secret: Optional[str] = None

@dataclass
class ChatGPTConfig:
    """Конфігурація ChatGPT API"""
    api_key: Optional[str] = None  # Встановити через змінну середовища
    model: str = "gpt-3.5-turbo"
    max_tokens: int = 3000
    temperature: float = 0.7

@dataclass
class LearningConfig:
    """Конфігурація навчальних параметрів"""
    words_per_session: int = 20
    questions_per_test: int = 20
    default_daily_goal: int = 50
    level_up_threshold: float = 80.0  # Мінімальна точність для підвищення рівня
    min_questions_for_level_up: int = 100

@dataclass
class Config:
    """Загальна конфігурація додатку"""
    database: DatabaseConfig
    bot: BotConfig
    chatgpt: ChatGPTConfig
    learning: LearningConfig
    debug: bool = False

def load_config() -> Config:
    """Завантажити конфігурацію з змінних середовища або використати значення за замовчуванням"""
    
    # Завантажити змінні середовища
    chatgpt_api_key = os.getenv("OPENAI_API_KEY")
    bot_token = os.getenv("BOT_TOKEN", "7365678598:AAHAMFBVPRR5etj4Fdt3TTLnmWJSDNbrWFQ")
    debug_mode = os.getenv("DEBUG", "False").lower() == "true"
    
    # База даних
    db_config = DatabaseConfig(
        host=os.getenv("DB_HOST", "31.222.235.200"),
        user=os.getenv("DB_USER", "gkevzmyh_martha"),
        password=os.getenv("DB_PASSWORD", "oC7xQ9cS5e"),
        database=os.getenv("DB_NAME", "gkevzmyh_eng_courses")
    )
    
    # Telegram бот
    bot_config = BotConfig(
        token=bot_token,
        webhook_url=os.getenv("WEBHOOK_URL"),
        webhook_path=os.getenv("WEBHOOK_PATH"),
        webhook_secret=os.getenv("WEBHOOK_SECRET")
    )
    
    # ChatGPT
    chatgpt_config = ChatGPTConfig(
        api_key=chatgpt_api_key,
        model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
        max_tokens=int(os.getenv("OPENAI_MAX_TOKENS", "3000")),
        temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
    )
    
    # Навчальні параметри
    learning_config = LearningConfig(
        words_per_session=int(os.getenv("WORDS_PER_SESSION", "20")),
        questions_per_test=int(os.getenv("QUESTIONS_PER_TEST", "20")),
        default_daily_goal=int(os.getenv("DEFAULT_DAILY_GOAL", "50")),
        level_up_threshold=float(os.getenv("LEVEL_UP_THRESHOLD", "80.0")),
        min_questions_for_level_up=int(os.getenv("MIN_QUESTIONS_FOR_LEVEL_UP", "100"))
    )
    
    return Config(
        database=db_config,
        bot=bot_config,
        chatgpt=chatgpt_config,
        learning=learning_config,
        debug=debug_mode
    )

# Константи для рівнів CEFR
LEVELS = {
    'A0': {'name': 'Початковий', 'order': 0},
    'A1': {'name': 'Елементарний', 'order': 1},
    'A2': {'name': 'Базовий', 'order': 2},
    'B1': {'name': 'Середній', 'order': 3},
    'B2': {'name': 'Вище середнього', 'order': 4},
    'C1': {'name': 'Просунутий', 'order': 5},
    'C2': {'name': 'Вільне володіння', 'order': 6}
}

def get_next_level(current_level: str) -> Optional[str]:
    """Отримати наступний рівень"""
    current_order = LEVELS.get(current_level, {}).get('order', 0)
    
    for level, data in LEVELS.items():
        if data['order'] == current_order + 1:
            return level
    
    return None  # Вже максимальний рівень

def get_level_name(level: str) -> str:
    """Отримати назву рівня"""
    return LEVELS.get(level, {}).get('name', 'Невідомий')

# Типи сесій
SESSION_TYPES = {
    'word_study': 'Вивчення слів',
    'ai_generated_test': 'Тест згенерований AI',
    'level_assessment': 'Оцінка рівня',
    'topic_test': 'Тест за темою'
}

# Мови інтерфейсу
LANGUAGES = {
    'UA': 'Українська',
    'EN': 'English',
    'RU': 'Русский',
    'PL': 'Polski'
}
