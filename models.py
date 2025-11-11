from sqlalchemy import BigInteger, Boolean, Column, Integer, String, TIMESTAMP, Float, ForeignKey, func, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, unique=True, nullable=False)
    username = Column(String(255))
    first_name = Column(String(255))
    last_name = Column(String(255))
    registration_date = Column(TIMESTAMP, server_default=func.current_timestamp())
    user_progress_id = Column(Integer)
    tg_id = Column(BigInteger)
    tg_premium = Column(Boolean)
    tg_lang = Column(String(10))
    
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
