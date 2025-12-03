from sqlalchemy import BigInteger, Boolean, Column, Integer, String, TIMESTAMP, Float, ForeignKey, func, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)  # Ціле автоінкрементне PK. Генерується БД.
    user_id = Column(BigInteger, unique=True, nullable=False)   # Зовнішній/публічний ідентифікатор (наприклад, Telegram). Унікальний, обов’язковий.
    username = Column(String(255))                               # Нік користувача, до 255 символів. За замовчуванням nullable=True.
    first_name = Column(String(255))                             # Ім’я, до 255 символів.
    last_name = Column(String(255))                              # Прізвище, до 255 символів.
    registration_date = Column(                                  # Дата реєстрації. Задається на стороні БД при вставці.
        TIMESTAMP, 
        server_default=func.current_timestamp()                  # DDL DEFAULT CURRENT_TIMESTAMP (працює навіть якщо поле не вказувати в INSERT).
    )
    user_progress_id = Column(Integer)                           # Посилання на прогрес (краще зробити ForeignKey, якщо є відповідна таблиця).
    tg_id = Column(BigInteger)                                   # Telegram internal ID (може дублювати user_id або бути окремим).
    tg_premium = Column(Boolean)                                 # Ознака Premium. Якщо потрібно строго True/False — зробіть nullable=False і дефолт.
    tg_lang = Column(String(10))                                 # Мова інтерфейсу (наприклад, 'en', 'uk', 'ru'), до 10 символів.
    
    # Налаштування денних лімітів
    daily_words_limit = Column(Integer, default=50)
    daily_questions_limit = Column(Integer, default=30)
    
    # Адміністратор
    is_admin = Column(Boolean, default=False)
    
    # Налаштування нагадувань
    reminder_enabled = Column(Boolean, default=True)
    reminder_time = Column(String(5), default="09:00")  # Формат HH:MM
    
    # Relationship - використовуємо user_id для зв'язку
    progress = relationship("UserProgress", back_populates="user", foreign_keys="UserProgress.user_id", uselist=False)

class UserProgress(Base):
    __tablename__ = 'user_progress'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.user_id'), nullable=False)
    level_english = Column(String(2), nullable=False)
    total_questions_answered = Column(Integer, default=0)
    correct_answers = Column(Integer, default=0)
    accuracy = Column(Float, default=0.0)
    last_updated = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    # Нові поля для щоденного навчання
    words_studied_today = Column(Integer, default=0)
    questions_answered_today = Column(Integer, default=0)
    last_study_date = Column(TIMESTAMP)
    
    words_total = Column(Integer, default=0)
    words_mastered = Column(Integer, default=0)  # mastery_level >= 3
    
    # Relationship - використовуємо user_id для зв'язку
    user = relationship("User", back_populates="progress", foreign_keys=[user_id])

class UserWordProgress(Base):
    """Прогрес користувача по словах (spaced repetition)"""
    __tablename__ = 'user_word_progress'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.user_id'), nullable=False)
    word_id = Column(Integer, ForeignKey('words.word_id'), nullable=False)
    
    mastery_level = Column(Integer, default=0)  # 0-4
    times_reviewed = Column(Integer, default=0)
    
    first_seen_date = Column(TIMESTAMP, server_default=func.current_timestamp())
    last_review_date = Column(TIMESTAMP)
    next_review_date = Column(TIMESTAMP)
    
    __table_args__ = (
        UniqueConstraint('user_id', 'word_id', name='unique_user_word'),
    )
    
    # Relationships
    user_rel = relationship("User", foreign_keys=[user_id])
    word_rel = relationship("Words", foreign_keys=[word_id])

class Words(Base):
    __tablename__ = 'words'
    
    word_id = Column(Integer, primary_key=True, autoincrement=True)
    word = Column(String(100), nullable=False)
    translation = Column(String(200), nullable=False)
    level_english = Column(String(2), nullable=False) 
    file_audio = Column(String(255))
    check_admin = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())

class Topics(Base):
    __tablename__ = 'topics'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    topic = Column(String(100), nullable=False, unique=True)
    description = Column(String(500))
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())

class Questions(Base):
    __tablename__ = 'questions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    question = Column(String(500), nullable=False)
    wrong_answers = Column(String(1000), nullable=False)  # JSON array as string
    answer = Column(String(200), nullable=False)
    explanation = Column(String(1000))  # Пояснення правильної відповіді
    topic = Column(String(100), ForeignKey('topics.topic'), nullable=False)
    level_english = Column(String(2), nullable=False)
    check_admin = Column(Boolean, default=False)
    level_question = Column(Float, default=2.5)  # Складність питання 1-5
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    
    # Relationship
    topic_rel = relationship("Topics", backref="questions")
