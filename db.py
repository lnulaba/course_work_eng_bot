from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import func, select
from models import Base, User, Words, UserProgress, Questions, Topics

class Connection:    
    def __init__(self):
        self.host = "31.222.235.200"
        self.user = "gkevzmyh_martha"
        self.password = "oC7xQ9cS5e"
        self.database = "gkevzmyh_eng_courses"
        self.engine = None
        self.session_maker = None

    async def connect(self):
        try:
            database_url = f"mysql+aiomysql://{self.user}:{self.password}@{self.host}/{self.database}"
            self.engine = create_async_engine(database_url, echo=False)
            self.session_maker = async_sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)
            
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            
            print("Connection to MySQL DB successful")
        except Exception as e:
            print(f"The error '{e}' occurred")


class DB:
    def __init__(self, session_maker):
        self.session_maker = session_maker

    async def add_user(self, user_id, username, first_name, last_name, tg_id, tg_premium, tg_lang):
        async with self.session_maker() as session:
            # Перевірка чи користувач вже існує
            result = await session.execute(select(User).where(User.user_id == user_id))
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                # Оновлення існуючого користувача
                existing_user.username = username
                existing_user.first_name = first_name
                existing_user.last_name = last_name
                existing_user.tg_id = tg_id
                existing_user.tg_premium = tg_premium
                existing_user.tg_lang = tg_lang
            else:
                # Додавання нового користувача
                new_user = User(
                    user_id=user_id,
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                    tg_id=tg_id,
                    tg_premium=tg_premium,
                    tg_lang=tg_lang
                )
                session.add(new_user)
            
            await session.commit()

    async def get_user(self, user_id):
        """
         Fetch a user by their user_id.
         """
        async with self.session_maker() as session:
            result = await session.execute(select(User).where(User.user_id == user_id))
            return result.scalar_one_or_none()
        
    async def get_word(self, word_id):
        """
        Fetch a word by its ID.
        """
        'dockstring'
        async with self.session_maker() as session:
            result = await session.execute(select(Words).where(Words.word_id == word_id))
            return result.scalar_one_or_none()
        
    # вибрати 40 рандомних слів сумарно, з кожного рівня приблизно по 3-4
    # 


    async def get_random_words(self, levels=["A0", "A1", "A2", "B1", "B2", "C1", "C2"], total_count=35):
        async with self.session_maker() as session:
            words_per_level = total_count // len(levels)
            random_words = []
            
            for level in levels:
                result = await session.execute(
                    select(Words).where(Words.level_english == level).order_by(func.rand()).limit(words_per_level)
                )
                level_words = result.scalars().all()
                random_words.extend(level_words)
            
            return random_words
        
    async def get_user_progress(self, user_id):
        """Отримати прогрес користувача"""
        async with self.session_maker() as session:
            result = await session.execute(
                select(UserProgress).where(UserProgress.user_id == user_id)
            )
            return result.scalar_one_or_none()
    
    async def update_user_progress(self, user_id, level_english, total_questions, correct_answers):
        """Оновити або створити прогрес користувача"""
        async with self.session_maker() as session:
            # Спробувати знайти існуючий прогрес
            result = await session.execute(
                select(UserProgress).where(UserProgress.user_id == user_id)
            )
            progress = result.scalar_one_or_none()
            
            accuracy = (correct_answers / total_questions * 100) if total_questions > 0 else 0.0
            
            if progress:
                # Оновити існуючий запис
                progress.level_english = level_english
                progress.total_questions_answered += total_questions
                progress.correct_answers += correct_answers
                progress.accuracy = (progress.correct_answers / progress.total_questions_answered * 100)
            else:
                # Створити новий запис
                progress = UserProgress(
                    user_id=user_id,
                    level_english=level_english,
                    total_questions_answered=total_questions,
                    correct_answers=correct_answers,
                    accuracy=accuracy
                )
                session.add(progress)
            
            await session.commit()
            await session.refresh(progress)
            
            # Оновити user_progress_id у таблиці users
            user_result = await session.execute(
                select(User).where(User.user_id == user_id)
            )
            user = user_result.scalar_one_or_none()
            if user and user.user_progress_id != progress.id:
                user.user_progress_id = progress.id
                await session.commit()
            
            return progress
        
    async def add_topic(self, topic, description=None):
        """Додати тему"""
        async with self.session_maker() as session:
            # Перевірка чи тема вже існує
            result = await session.execute(select(Topics).where(Topics.topic == topic))
            existing_topic = result.scalar_one_or_none()
            
            if not existing_topic:
                new_topic = Topics(topic=topic, description=description)
                session.add(new_topic)
                await session.commit()
                return new_topic
            return existing_topic
    
    async def add_question(self, question, wrong_answers, answer, topic, level_english, level_question=2.5, explanation=None):
        """Додати питання"""
        async with self.session_maker() as session:
            import json
            
            # Перетворити список неправильних відповідей в JSON string
            if isinstance(wrong_answers, list):
                wrong_answers_str = json.dumps(wrong_answers, ensure_ascii=False)
            else:
                wrong_answers_str = wrong_answers
            
            new_question = Questions(
                question=question,
                wrong_answers=wrong_answers_str,
                answer=answer,
                explanation=explanation,
                topic=topic,
                level_english=level_english,
                level_question=level_question,
                check_admin=False
            )
            session.add(new_question)
            await session.commit()
            return new_question
    
    async def get_random_questions(self, level=None, topic=None, count=20):
        """Отримати випадкові питання"""
        async with self.session_maker() as session:
            query = select(Questions).where(Questions.check_admin == True)
            
            if level:
                query = query.where(Questions.level_english == level)
            if topic:
                query = query.where(Questions.topic == topic)
            
            query = query.order_by(func.rand()).limit(count)
            result = await session.execute(query)
            return result.scalars().all()


