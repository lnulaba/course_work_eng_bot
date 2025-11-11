from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import func, select, and_, or_
from models import Base, User, Words, UserProgress, Questions, Topics, UserWordProgress
from datetime import datetime, timedelta

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
        

    async def get_questions_for_testing(self):
        """Отримати по 1 питанню з кожної теми для кожного рівня (відсортовано)"""
        async with self.session_maker() as session:
            levels = ["A1", "A2", "B1", "B2", "C1", "C2"]
            all_questions = []
            
            # Отримати всі теми
            topics_result = await session.execute(select(Topics.topic))
            topics = [row[0] for row in topics_result.all()]
            
            # Для кожного рівня
            for level in levels:
                # Для кожної теми
                for topic in topics:
                    result = await session.execute(
                        select(Questions)
                        .where(Questions.check_admin == False) # поки що тільки не перевірені питання
                        .where(Questions.level_english == level)
                        .where(Questions.topic == topic)
                        .order_by(func.rand())
                        .limit(1)
                    )
                    question = result.scalar_one_or_none()
                    if question:
                        all_questions.append(question)
            
            return all_questions
        
        
    async def get_questions_statistics(self):
        """Отримати статистику питань по рівнях та темах"""
        async with self.session_maker() as session:
            # Загальна кількість питань
            total_result = await session.execute(
                select(func.count(Questions.id))
            )
            total_questions = total_result.scalar()
            
            # Кількість питань по рівнях
            level_result = await session.execute(
                select(Questions.level_english, func.count(Questions.id))
                .group_by(Questions.level_english)
                .order_by(Questions.level_english)
            )
            questions_by_level = {level: count for level, count in level_result.all()}
            
            # Кількість питань по темах
            topic_result = await session.execute(
                select(Questions.topic, func.count(Questions.id))
                .group_by(Questions.topic)
                .order_by(func.count(Questions.id).desc())
            )
            questions_by_topic = {topic: count for topic, count in topic_result.all()}
            
            # Кількість питань по рівнях та темах
            level_topic_result = await session.execute(
                select(Questions.level_english, Questions.topic, func.count(Questions.id))
                .group_by(Questions.level_english, Questions.topic)
                .order_by(Questions.level_english, Questions.topic)
            )
            questions_by_level_topic = {}
            for level, topic, count in level_topic_result.all():
                if level not in questions_by_level_topic:
                    questions_by_level_topic[level] = {}
                questions_by_level_topic[level][topic] = count
            
            return {
                "total": total_questions,
                "by_level": questions_by_level,
                "by_topic": questions_by_topic,
                "by_level_topic": questions_by_level_topic
            }
    
    async def get_words_statistics(self):
        """Отримати статистику слів по рівнях"""
        async with self.session_maker() as session:
            # Загальна кількість слів
            total_result = await session.execute(
                select(func.count(Words.word_id))
            )
            total_words = total_result.scalar()
            
            # Кількість слів по рівнях
            level_result = await session.execute(
                select(Words.level_english, func.count(Words.word_id))
                .group_by(Words.level_english)
                .order_by(Words.level_english)
            )
            words_by_level = {level: count for level, count in level_result.all()}
            
            return {
                "total": total_words,
                "by_level": words_by_level
            }
        
    async def get_user_limits(self, user_id: int):
        """Отримати денні ліміти користувача"""
        async with self.session_maker() as session:
            result = await session.execute(
                select(User.daily_words_limit, User.daily_questions_limit).where(User.user_id == user_id)
            )
            limits = result.one_or_none()
            
            if limits:
                return {
                    'words': limits[0] or 50,
                    'questions': limits[1] or 30
                }
            return {
                'words': 50,
                'questions': 30
            }
    
    async def update_user_limits(self, user_id: int, words_limit: int = None, questions_limit: int = None):
        """Оновити денні ліміти користувача"""
        async with self.session_maker() as session:
            result = await session.execute(
                select(User).where(User.user_id == user_id)
            )
            user = result.scalar_one_or_none()
            
            if user:
                if words_limit is not None:
                    user.daily_words_limit = words_limit
                if questions_limit is not None:
                    user.daily_questions_limit = questions_limit
                
                await session.commit()
                return True
            return False
    
    async def get_daily_words(self, user_id: int, limit: int = None):
        """
        Отримати слова для щоденного навчання
        
        Якщо limit не вказано, використовується ліміт з налаштувань користувача
        """
        async with self.session_maker() as session:
            # Отримати рівень користувача та ліміт
            progress = await self.get_user_progress(user_id)
            if not progress:
                return []
            
            # Якщо ліміт не вказано, отримати з налаштувань користувача
            if limit is None:
                limits = await self.get_user_limits(user_id)
                limit = limits['words']
            
            user_level = progress.level_english
            today = datetime.now().date()
            
            # 1. Слова на повтор (next_review_date <= today)
            review_query = (
                select(Words)
                .join(UserWordProgress, Words.word_id == UserWordProgress.word_id)
                .where(
                    and_(
                        UserWordProgress.user_id == user_id,
                        UserWordProgress.next_review_date <= today,
                        Words.level_english == user_level
                    )
                )
                .order_by(UserWordProgress.next_review_date)
                .limit(limit // 2)  # До половини ліміту на повтор
            )
            review_result = await session.execute(review_query)
            review_words = list(review_result.scalars().all())
            
            # 2. Нові слова (не в user_word_progress)
            words_needed = limit - len(review_words)
            if words_needed > 0:
                # Отримати ID слів, які вже є в прогресі
                existing_word_ids_query = select(UserWordProgress.word_id).where(
                    UserWordProgress.user_id == user_id
                )
                existing_result = await session.execute(existing_word_ids_query)
                existing_word_ids = [row[0] for row in existing_result.all()]
                
                # Вибрати нові слова
                new_words_query = (
                    select(Words)
                    .where(
                        and_(
                            Words.level_english == user_level,
                            Words.word_id.not_in(existing_word_ids) if existing_word_ids else True
                        )
                    )
                    .order_by(func.rand())
                    .limit(words_needed)
                )
                new_result = await session.execute(new_words_query)
                new_words = list(new_result.scalars().all())
                
                review_words.extend(new_words)
            
            return review_words[:limit]
    
    async def save_word_answer(self, user_id: int, word_id: int, answer_type: str):
        """
        Зберегти відповідь користувача на слово
        
        answer_type: 'easy', 'know', 'hard', 'new'
        """
        REVIEW_INTERVALS = {
            0: 0,      # Сьогодні
            1: 1,      # +1 день
            2: 3,      # +3 дні
            3: 7,      # +7 днів
            4: 30,     # +30 днів
        }
        
        async with self.session_maker() as session:
            # Знайти або створити запис прогресу
            result = await session.execute(
                select(UserWordProgress).where(
                    and_(
                        UserWordProgress.user_id == user_id,
                        UserWordProgress.word_id == word_id
                    )
                )
            )
            word_progress = result.scalar_one_or_none()
            
            now = datetime.now()
            
            if not word_progress:
                # Створити новий запис
                word_progress = UserWordProgress(
                    user_id=user_id,
                    word_id=word_id,
                    mastery_level=0,
                    times_reviewed=0,
                    first_seen_date=now
                )
                session.add(word_progress)
            
            # Оновити mastery_level
            if answer_type == 'easy':
                word_progress.mastery_level = min(4, word_progress.mastery_level + 2)
            elif answer_type == 'know':
                word_progress.mastery_level = min(4, word_progress.mastery_level + 1)
            elif answer_type == 'hard':
                word_progress.mastery_level = 1
            elif answer_type == 'new':
                word_progress.mastery_level = 0
            
            word_progress.times_reviewed += 1
            word_progress.last_review_date = now
            
            # Розрахувати next_review_date
            days_to_add = REVIEW_INTERVALS.get(word_progress.mastery_level, 0)
            word_progress.next_review_date = now + timedelta(days=days_to_add)
            
            await session.commit()
            
            # Оновити загальний прогрес користувача
            await self._update_user_daily_progress(user_id, words_increment=1)
    
    async def _update_user_daily_progress(self, user_id: int, words_increment: int = 0, questions_increment: int = 0):
        """Оновити щоденний прогрес користувача"""
        async with self.session_maker() as session:
            result = await session.execute(
                select(UserProgress).where(UserProgress.user_id == user_id)
            )
            progress = result.scalar_one_or_none()
            
            if not progress:
                return
            
            today = datetime.now().date()
            last_study = progress.last_study_date.date() if progress.last_study_date else None
            
            # Скинути лічильники якщо новий день
            if last_study != today:
                progress.words_studied_today = 0
                progress.questions_answered_today = 0
            
            progress.words_studied_today += words_increment
            progress.questions_answered_today += questions_increment
            progress.last_study_date = datetime.now()
            
            # Оновити загальну кількість слів
            if words_increment > 0:
                progress.words_total = progress.words_studied_today
                
                # Порахувати засвоєні слова (mastery >= 3)
                mastered_query = select(func.count(UserWordProgress.id)).where(
                    and_(
                        UserWordProgress.user_id == user_id,
                        UserWordProgress.mastery_level >= 3
                    )
                )
                mastered_result = await session.execute(mastered_query)
                progress.words_mastered = mastered_result.scalar()
            
            await session.commit()
    
    async def get_daily_questions(self, user_id: int, limit: int = None):
        """
        Отримати питання поточного рівня
        
        Якщо limit не вказано, використовується ліміт з налаштувань користувача
        """
        async with self.session_maker() as session:
            # Отримати рівень користувача та ліміт
            progress = await self.get_user_progress(user_id)
            if not progress:
                return []
            
            # Якщо ліміт не вказано, отримати з налаштувань користувача
            if limit is None:
                limits = await self.get_user_limits(user_id)
                limit = limits['questions']
            
            user_level = progress.level_english
            
            # Отримати всі теми
            topics_result = await session.execute(select(Topics.topic))
            topics = [row[0] for row in topics_result.all()]
            
            if not topics:
                # Якщо немає тем, просто випадково вибрати питання
                query = (
                    select(Questions)
                    .where(
                        and_(
                            Questions.level_english == user_level,
                            Questions.check_admin == False
                        )
                    )
                    .order_by(func.rand())
                    .limit(limit)
                )
                result = await session.execute(query)
                return list(result.scalars().all())
            
            # Розрахувати скільки питань на тему
            questions_per_topic = max(1, limit // len(topics))
            all_questions = []
            
            for topic in topics:
                query = (
                    select(Questions)
                    .where(
                        and_(
                            Questions.level_english == user_level,
                            Questions.topic == topic,
                            Questions.check_admin == False
                        )
                    )
                    .order_by(func.rand())
                    .limit(questions_per_topic)
                )
                result = await session.execute(query)
                all_questions.extend(result.scalars().all())
            
            # Якщо не вистачає, доповнити
            if len(all_questions) < limit:
                remaining = limit - len(all_questions)
                existing_ids = [q.id for q in all_questions]
                
                extra_query = (
                    select(Questions)
                    .where(
                        and_(
                            Questions.level_english == user_level,
                            Questions.check_admin == False,
                            Questions.id.not_in(existing_ids) if existing_ids else True
                        )
                    )
                    .order_by(func.rand())
                    .limit(remaining)
                )
                extra_result = await session.execute(extra_query)
                all_questions.extend(extra_result.scalars().all())
            
            return all_questions[:limit]
    
    async def check_level_up_eligibility(self, user_id: int):
        """
        Перевірити чи може користувач перейти на наступний рівень
        
        Критерії:
        1. Мінімум 100 слів вивчено на поточному рівні
        2. Мінімум 50 слів з mastery_level >= 3
        3. Точність по словах >= 60%
        4. Точність по питаннях >= 60%
        """
        async with self.session_maker() as session:
            progress = await self.get_user_progress(user_id)
            if not progress:
                return False
            
            # Перевірка точності питань
            if progress.accuracy < 60.0:
                return False
            
            # Порахувати всі слова користувача
            total_words_query = select(func.count(UserWordProgress.id)).where(
                UserWordProgress.user_id == user_id
            )
            total_words_result = await session.execute(total_words_query)
            total_words = total_words_result.scalar()
            
            if total_words < 100:
                return False
            
            # Порахувати засвоєні слова
            mastered_words_query = select(func.count(UserWordProgress.id)).where(
                and_(
                    UserWordProgress.user_id == user_id,
                    UserWordProgress.mastery_level >= 3
                )
            )
            mastered_result = await session.execute(mastered_words_query)
            mastered_words = mastered_result.scalar()
            
            if mastered_words < 50:
                return False
            
            # Порахувати точність по словах (% слів з mastery >= 3)
            word_accuracy = (mastered_words / total_words * 100) if total_words > 0 else 0
            
            return word_accuracy >= 60.0
    
    async def get_user_word_stats(self, user_id: int):
        """Отримати статистику слів користувача"""
        async with self.session_maker() as session:
            # Загальна кількість слів
            total_query = select(func.count(UserWordProgress.id)).where(
                UserWordProgress.user_id == user_id
            )
            total_result = await session.execute(total_query)
            total_words = total_result.scalar()
            
            # Засвоєні слова (mastery >= 3)
            mastered_query = select(func.count(UserWordProgress.id)).where(
                and_(
                    UserWordProgress.user_id == user_id,
                    UserWordProgress.mastery_level >= 3
                )
            )
            mastered_result = await session.execute(mastered_query)
            mastered_words = mastered_result.scalar()
            
            # Точність
            accuracy = (mastered_words / total_words * 100) if total_words > 0 else 0
            
            return {
                'total': total_words,
                'mastered': mastered_words,
                'accuracy': accuracy
            }
    
    async def is_user_admin(self, user_id: int):
        """Перевірити чи є користувач адміністратором"""
        async with self.session_maker() as session:
            result = await session.execute(
                select(User.is_admin).where(User.user_id == user_id)
            )
            is_admin = result.scalar_one_or_none()
            return is_admin if is_admin is not None else False
    
    async def set_user_admin(self, user_id: int, is_admin: bool = True):
        """Встановити/зняти статус адміністратора"""
        async with self.session_maker() as session:
            result = await session.execute(
                select(User).where(User.user_id == user_id)
            )
            user = result.scalar_one_or_none()
            
            if user:
                user.is_admin = is_admin
                await session.commit()
                return True
            return False
    
    async def save_question_answer(self, user_id: int, question_id: int, is_correct: bool):
        """
        Зберегти відповідь користувача на питання
        
        Оновлює лічильник questions_answered_today та загальну статистику
        """
        await self._update_user_daily_progress(user_id, questions_increment=1)
        
        # Якщо правильна відповідь, оновити статистику точності
        if is_correct:
            async with self.session_maker() as session:
                result = await session.execute(
                    select(UserProgress).where(UserProgress.user_id == user_id)
                )
                progress = result.scalar_one_or_none()
                
                if progress:
                    progress.total_questions_answered += 1
                    progress.correct_answers += 1
                    progress.accuracy = (progress.correct_answers / progress.total_questions_answered * 100)
                    await session.commit()
        else:
            # Неправильна відповідь - тільки збільшити лічильник
            async with self.session_maker() as session:
                result = await session.execute(
                    select(UserProgress).where(UserProgress.user_id == user_id)
                )
                progress = result.scalar_one_or_none()
                
                if progress:
                    progress.total_questions_answered += 1
                    progress.accuracy = (progress.correct_answers / progress.total_questions_answered * 100)
                    await session.commit()
    
    async def reset_user_progress(self, user_id: int):
        """Повністю скинути прогрес користувача"""
        async with self.session_maker() as session:
            # Видалити прогрес по словах
            await session.execute(
                select(UserWordProgress).where(UserWordProgress.user_id == user_id)
            )
            word_progress_result = await session.execute(
                select(UserWordProgress).where(UserWordProgress.user_id == user_id)
            )
            for wp in word_progress_result.scalars().all():
                await session.delete(wp)
            
            # Видалити загальний прогрес
            progress_result = await session.execute(
                select(UserProgress).where(UserProgress.user_id == user_id)
            )
            progress = progress_result.scalar_one_or_none()
            if progress:
                await session.delete(progress)
            
            # Скинути user_progress_id в таблиці users
            user_result = await session.execute(
                select(User).where(User.user_id == user_id)
            )
            user = user_result.scalar_one_or_none()
            if user:
                user.user_progress_id = None
            
            await session.commit()
            return True
    
    async def get_users_statistics(self):
        """Отримати загальну статистику користувачів"""
        async with self.session_maker() as session:
            # Загальна кількість користувачів
            total_users_result = await session.execute(select(func.count(User.id)))
            total_users = total_users_result.scalar()
            
            # Користувачі з прогресом
            users_with_progress_result = await session.execute(
                select(func.count(UserProgress.id))
            )
            users_with_progress = users_with_progress_result.scalar()
            
            # Користувачі по рівнях
            users_by_level_result = await session.execute(
                select(UserProgress.level_english, func.count(UserProgress.id))
                .group_by(UserProgress.level_english)
                .order_by(UserProgress.level_english)
            )
            users_by_level = {level: count for level, count in users_by_level_result.all()}
            
            # Премиум користувачі
            premium_users_result = await session.execute(
                select(func.count(User.id)).where(User.tg_premium == True)
            )
            premium_users = premium_users_result.scalar()
            
            # Адміністратори
            admin_users_result = await session.execute(
                select(func.count(User.id)).where(User.is_admin == True)
            )
            admin_users = admin_users_result.scalar()
            
            return {
                "total": total_users,
                "with_progress": users_with_progress,
                "by_level": users_by_level,
                "premium": premium_users,
                "admins": admin_users
            }
    
    async def find_user_by_telegram_id(self, tg_id: int):
        """Знайти користувача по Telegram ID"""
        async with self.session_maker() as session:
            result = await session.execute(
                select(User).where(User.tg_id == tg_id)
            )
            return result.scalar_one_or_none()
    
    async def get_user_full_info(self, user_id: int):
        """Отримати повну інформацію про користувача"""
        async with self.session_maker() as session:
            # Користувач
            user_result = await session.execute(
                select(User).where(User.user_id == user_id)
            )
            user = user_result.scalar_one_or_none()
            
            if not user:
                return None
            
            # Прогрес
            progress_result = await session.execute(
                select(UserProgress).where(UserProgress.user_id == user_id)
            )
            progress = progress_result.scalar_one_or_none()
            
            # Статистика слів
            word_stats = await self.get_user_word_stats(user_id)
            
            return {
                "user": user,
                "progress": progress,
                "word_stats": word_stats
            }
    
    async def get_all_users_list(self, limit: int = 50, offset: int = 0):
        """Отримати список всіх користувачів з пагінацією"""
        async with self.session_maker() as session:
            result = await session.execute(
                select(User)
                .order_by(User.registration_date.desc())
                .limit(limit)
                .offset(offset)
            )
            return result.scalars().all()
        
    async def get_user_reminder_settings(self, user_id: int):
        """Отримати налаштування нагадувань користувача"""
        async with self.session_maker() as session:
            result = await session.execute(
                select(User.reminder_enabled, User.reminder_time, User.tg_id)
                .where(User.user_id == user_id)
            )
            settings = result.one_or_none()
            
            if settings:
                return {
                    'enabled': settings[0] if settings[0] is not None else True,
                    'time': settings[1] or "09:00",
                    'tg_id': settings[2]
                }
            return {
                'enabled': True,
                'time': "09:00",
                'tg_id': None
            }
    
    async def update_user_reminder_settings(self, user_id: int, enabled: bool = None, time: str = None):
        """Оновити налаштування нагадувань користувача"""
        async with self.session_maker() as session:
            result = await session.execute(
                select(User).where(User.user_id == user_id)
            )
            user = result.scalar_one_or_none()
            
            if user:
                if enabled is not None:
                    user.reminder_enabled = enabled
                if time is not None:
                    user.reminder_time = time
                
                await session.commit()
                return True
            return False
    
    async def get_users_for_reminder(self, current_time: str):
        """
        Отримати користувачів для відправки нагадування
        current_time - формат HH:MM
        """
        async with self.session_maker() as session:
            result = await session.execute(
                select(User)
                .where(
                    and_(
                        User.reminder_enabled == True,
                        User.reminder_time == current_time
                    )
                )
            )
            return result.scalars().all()


