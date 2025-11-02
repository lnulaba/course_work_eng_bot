from sqlalchemy import BigInteger, Boolean, Column, Integer, String, TIMESTAMP, func
from sqlalchemy.ext.declarative import declarative_base

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



class Words(Base):
    __tablename__ = 'words'
    
    word_id = Column(Integer, primary_key=True, autoincrement=True)
    word = Column(String(100), nullable=False)
    translation = Column(String(200), nullable=False)
    level_english = Column(String(2), nullable=False) 
    file_audio = Column(String(255))
    check_admin = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
