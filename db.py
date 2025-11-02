import asyncio
import aiomysql
import json
from datetime import datetime
from typing import Optional, List, Dict, Any

# Клас для роботи з базою даних English Learning Bot
# Підтримує повну структуру згідно з діаграмою активності

class Connection:    
    def __init__(self):
        self.host="31.222.235.200"
        self.user="gkevzmyh_martha"
        self.password="oC7xQ9cS5e"
        self.database="gkevzmyh_eng_courses"
        self.connection = None

    async def connect(self):
        try:
            self.connection = await aiomysql.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                db=self.database
            )
            print("Connection to MySQL DB successful")
        except Exception as e:
            print(f"The error '{e}' occurred")


class DB:
    def __init__(self, connection):
        self.connection = connection

    async def create_tables(self):
        """Створення всіх таблиць згідно з діаграмою"""
        await self.create_users_table()
        await self.create_user_progress_table()
        await self.create_settings_table()
        await self.create_topics_table()
        await self.create_words_table()
        await self.create_questions_table()
        await self.create_test_sessions_table()

    async def create_users_table(self):
        async with self.connection.cursor() as cursor:
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    telegram_id BIGINT UNIQUE NOT NULL,
                    username VARCHAR(50),
                    full_name VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE
                );
            """)
            await self.connection.commit()

    async def create_user_progress_table(self):
        async with self.connection.cursor() as cursor:
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_progress (
                    progress_id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id BIGINT UNIQUE,
                    level_english ENUM('A0', 'A1', 'A2', 'B1', 'B2', 'C1', 'C2') DEFAULT 'A0',
                    total_questions_answered INT DEFAULT 0,
                    correct_answers INT DEFAULT 0,
                    accuracy DECIMAL(5,2) DEFAULT 0.00,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                );
            """)
            await self.connection.commit()

    async def create_settings_table(self):
        async with self.connection.cursor() as cursor:
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    setting_id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id BIGINT UNIQUE,
                    preferred_language ENUM('UA', 'EN', 'RU', 'PL') DEFAULT 'UA',
                    daily_goal INT DEFAULT 50,
                    notification_time TIME DEFAULT '19:00:00',
                    sound_enabled BOOLEAN DEFAULT TRUE,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                );
            """)
            await self.connection.commit()

    async def create_topics_table(self):
        async with self.connection.cursor() as cursor:
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS topics (
                    topic_id INT AUTO_INCREMENT PRIMARY KEY,
                    topic_name VARCHAR(100) NOT NULL,
                    description TEXT,
                    difficulty_level ENUM('A0', 'A1', 'A2', 'B1', 'B2', 'C1', 'C2') NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE
                );
            """)
            await self.connection.commit()

    async def create_words_table(self):
        async with self.connection.cursor() as cursor:
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS words (
                    word_id INT AUTO_INCREMENT PRIMARY KEY,
                    word VARCHAR(100) NOT NULL,
                    translation VARCHAR(200) NOT NULL,
                    level_english ENUM('A0', 'A1', 'A2', 'B1', 'B2', 'C1', 'C2') NOT NULL,
                    file_audio VARCHAR(255),
                    check_admin BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            await self.connection.commit()

    async def create_questions_table(self):
        async with self.connection.cursor() as cursor:
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS questions (
                    question_id INT AUTO_INCREMENT PRIMARY KEY,
                    topic_id INT,
                    question_text TEXT NOT NULL,
                    option_a VARCHAR(255) NOT NULL,
                    option_b VARCHAR(255) NOT NULL,
                    option_c VARCHAR(255) NOT NULL,
                    option_d VARCHAR(255),
                    correct_answer CHAR(1) NOT NULL,
                    difficulty_level ENUM('A0', 'A1', 'A2', 'B1', 'B2', 'C1', 'C2') NOT NULL,
                    ai_generated BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (topic_id) REFERENCES topics(topic_id) ON DELETE SET NULL
                );
            """)
            await self.connection.commit()

    async def create_test_sessions_table(self):
        async with self.connection.cursor() as cursor:
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS test_sessions (
                    session_id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    session_type ENUM('word_study', 'ai_generated_test', 'level_assessment', 'topic_test') NOT NULL,
                    questions_answered INT DEFAULT 0,
                    correct_answers INT DEFAULT 0,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP NULL,
                    is_completed BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                );
            """)
            await self.connection.commit()

    # ==================== USER OPERATIONS ====================
    
    async def register_user(self, telegram_id: int, username: str = None, full_name: str = None) -> bool:
        """Реєстрація нового користувача згідно з алгоритмом"""
        try:
            async with self.connection.cursor() as cursor:
                # Перевірити чи користувач існує
                await cursor.execute("SELECT user_id FROM users WHERE telegram_id = %s", (telegram_id,))
                existing_user = await cursor.fetchone()
                
                if existing_user:
                    return False  # Користувач вже існує
                
                # Створити нового користувача
                await cursor.execute("""
                    INSERT INTO users (telegram_id, username, full_name, user_id)
                    VALUES (%s, %s, %s, %s)
                """, (telegram_id, username, full_name, telegram_id))
                
                # Створити початкові налаштування
                await cursor.execute("""
                    INSERT INTO settings (user_id, preferred_language, daily_goal, notification_time, sound_enabled)
                    VALUES (%s, 'UA', 50, '19:00:00', TRUE)
                """, (telegram_id,))
                
                # Ініціалізувати прогрес
                await cursor.execute("""
                    INSERT INTO user_progress (user_id, level_english, total_questions_answered, correct_answers, accuracy)
                    VALUES (%s, 'A0', 0, 0, 0.00)
                """, (telegram_id,))
                
                await self.connection.commit()
                return True
                
        except Exception as e:
            print(f"Error registering user: {e}")
            await self.connection.rollback()
            return False

    async def get_user(self, telegram_id: int) -> Optional[Dict]:
        """Отримати дані користувача"""
        async with self.connection.cursor() as cursor:
            await cursor.execute("""
                SELECT u.*, up.level_english, up.accuracy, s.daily_goal
                FROM users u
                LEFT JOIN user_progress up ON u.user_id = up.user_id
                LEFT JOIN settings s ON u.user_id = s.user_id
                WHERE u.telegram_id = %s AND u.is_active = TRUE
            """, (telegram_id,))
            result = await cursor.fetchone()
            
            if result:
                return {
                    'user_id': result[0],
                    'telegram_id': result[1],
                    'username': result[2],
                    'full_name': result[3],
                    'created_at': result[4],
                    'is_active': result[5],
                    'level_english': result[6] if len(result) > 6 else 'A0',
                    'accuracy': float(result[7]) if len(result) > 7 and result[7] else 0.0,
                    'daily_goal': result[8] if len(result) > 8 else 50
                }
            return None

    # ==================== WORD LEARNING ====================
    
    async def get_words_by_level(self, level: str, limit: int = 20) -> List[Dict]:
        """Отримати слова за рівнем для вивчення"""
        async with self.connection.cursor() as cursor:
            await cursor.execute("""
                SELECT word_id, word, translation, file_audio
                FROM words 
                WHERE level_english = %s AND check_admin = TRUE
                ORDER BY RAND() 
                LIMIT %s
            """, (level, limit))
            
            results = await cursor.fetchall()
            return [
                {
                    'word_id': result[0],
                    'word': result[1],
                    'translation': result[2],
                    'file_audio': result[3]
                }
                for result in results
            ]

    async def create_word_session(self, user_id: int) -> int:
        """Створити сесію вивчення слів"""
        async with self.connection.cursor() as cursor:
            await cursor.execute("""
                INSERT INTO test_sessions (user_id, session_type, started_at)
                VALUES (%s, 'word_study', NOW())
            """, (user_id,))
            await self.connection.commit()
            return cursor.lastrowid

    async def complete_word_session(self, session_id: int, correct_answers: int, total_questions: int):
        """Завершити сесію вивчення слів"""
        async with self.connection.cursor() as cursor:
            await cursor.execute("""
                UPDATE test_sessions 
                SET questions_answered = %s, correct_answers = %s, 
                    completed_at = NOW(), is_completed = TRUE
                WHERE session_id = %s
            """, (total_questions, correct_answers, session_id))
            await self.connection.commit()

    # ==================== PROGRESS TRACKING ====================
    
    async def update_user_progress(self, user_id: int, correct_answers: int, total_questions: int):
        """Оновити прогрес користувача"""
        async with self.connection.cursor() as cursor:
            await cursor.execute("""
                UPDATE user_progress 
                SET total_questions_answered = total_questions_answered + %s,
                    correct_answers = correct_answers + %s,
                    accuracy = (correct_answers + %s) / (total_questions_answered + %s) * 100,
                    last_updated = NOW()
                WHERE user_id = %s
            """, (total_questions, correct_answers, correct_answers, total_questions, user_id))
            await self.connection.commit()

    async def get_user_statistics(self, user_id: int) -> Dict:
        """Отримати статистику користувача"""
        async with self.connection.cursor() as cursor:
            # Основна статистика
            await cursor.execute("""
                SELECT up.*, 
                       COUNT(ts.session_id) as total_sessions,
                       COUNT(CASE WHEN ts.is_completed = TRUE THEN 1 END) as completed_sessions
                FROM user_progress up
                LEFT JOIN test_sessions ts ON up.user_id = ts.user_id
                WHERE up.user_id = %s
                GROUP BY up.user_id
            """, (user_id,))
            
            result = await cursor.fetchone()
            if result:
                return {
                    'level_english': result[2],
                    'total_questions_answered': result[3],
                    'correct_answers': result[4],
                    'accuracy': float(result[5]),
                    'last_updated': result[6],
                    'total_sessions': result[7],
                    'completed_sessions': result[8]
                }
            return {}

    # ==================== TOPICS AND QUESTIONS ====================
    
    async def get_topics_by_level(self, level: str) -> List[Dict]:
        """Отримати теми за рівнем"""
        async with self.connection.cursor() as cursor:
            await cursor.execute("""
                SELECT topic_id, topic_name, description
                FROM topics 
                WHERE difficulty_level <= %s AND is_active = TRUE
                ORDER BY topic_name
            """, (level,))
            
            results = await cursor.fetchall()
            return [
                {
                    'topic_id': result[0],
                    'topic_name': result[1],
                    'description': result[2]
                }
                for result in results
            ]

    async def save_ai_questions(self, topic_id: int, questions: List[Dict]) -> List[int]:
        """Зберегти питання згенеровані AI"""
        question_ids = []
        async with self.connection.cursor() as cursor:
            for q in questions:
                await cursor.execute("""
                    INSERT INTO questions 
                    (topic_id, question_text, option_a, option_b, option_c, option_d, 
                     correct_answer, difficulty_level, ai_generated)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, TRUE)
                """, (
                    topic_id, q['question'], q['options']['A'], q['options']['B'], 
                    q['options']['C'], q['options'].get('D', ''), q['correct_answer'], 
                    q.get('difficulty_level', 'A1')
                ))
                question_ids.append(cursor.lastrowid)
            
            await self.connection.commit()
        return question_ids

    # ==================== SETTINGS ====================
    
    async def get_user_settings(self, user_id: int) -> Dict:
        """Отримати налаштування користувача"""
        async with self.connection.cursor() as cursor:
            await cursor.execute("""
                SELECT preferred_language, daily_goal, notification_time, sound_enabled
                FROM settings WHERE user_id = %s
            """, (user_id,))
            
            result = await cursor.fetchone()
            if result:
                return {
                    'preferred_language': result[0],
                    'daily_goal': result[1],
                    'notification_time': str(result[2]) if result[2] else None,
                    'sound_enabled': bool(result[3])
                }
            return {}

    async def update_user_settings(self, user_id: int, **kwargs):
        """Оновити налаштування користувача"""
        if not kwargs:
            return
        
        set_clauses = []
        values = []
        
        for key, value in kwargs.items():
            if key in ['preferred_language', 'daily_goal', 'notification_time', 'sound_enabled']:
                set_clauses.append(f"{key} = %s")
                values.append(value)
        
        if set_clauses:
            values.append(user_id)
            query = f"UPDATE settings SET {', '.join(set_clauses)} WHERE user_id = %s"
            
            async with self.connection.cursor() as cursor:
                await cursor.execute(query, values)
                await self.connection.commit()

    # Залишити старі методи для сумісності
    async def add_user(self, user_id, username, first_name, last_name, tg_id, tg_premium, tg_lang):
        """Старий метод для сумісності"""
        full_name = f"{first_name or ''} {last_name or ''}".strip()
        return await self.register_user(tg_id, username, full_name)

    # ==================== ДОДАТКОВІ МЕТОДИ ====================
    
    async def create_test_session(self, user_id: int, session_type: str) -> int:
        """Створити сесію тестування"""
        async with self.connection.cursor() as cursor:
            await cursor.execute("""
                INSERT INTO test_sessions (user_id, session_type, started_at)
                VALUES (%s, %s, NOW())
            """, (user_id, session_type))
            await self.connection.commit()
            return cursor.lastrowid

    async def complete_test_session(self, session_id: int, total_questions: int, correct_answers: int):
        """Завершити сесію тестування"""
        async with self.connection.cursor() as cursor:
            await cursor.execute("""
                UPDATE test_sessions 
                SET questions_answered = %s, correct_answers = %s, 
                    completed_at = NOW(), is_completed = TRUE
                WHERE session_id = %s
            """, (total_questions, correct_answers, session_id))
            await self.connection.commit()

    async def insert_sample_data(self):
        """Вставити тестові дані для демонстрації"""
        try:
            async with self.connection.cursor() as cursor:
                # Додати теми
                topics_data = [
                    ("Present Simple", "Basic present tense", "A1"),
                    ("Past Simple", "Basic past tense", "A1"),
                    ("Present Perfect", "Perfect tense usage", "A2"),
                    ("Modal Verbs", "Can, could, should, must", "A2"),
                    ("Conditional Sentences", "If clauses", "B1"),
                    ("Passive Voice", "Passive constructions", "B1"),
                    ("Reported Speech", "Indirect speech", "B2"),
                    ("Subjunctive Mood", "Advanced grammar", "C1")
                ]
                
                for topic_name, description, level in topics_data:
                    await cursor.execute("""
                        INSERT IGNORE INTO topics (topic_name, description, difficulty_level)
                        VALUES (%s, %s, %s)
                    """, (topic_name, description, level))
                
                # Додати слова
                words_data = [
                    ("hello", "привіт", "A0", None),
                    ("goodbye", "до побачення", "A0", None),
                    ("thank you", "дякую", "A0", None),
                    ("cat", "кіт", "A0", None),
                    ("dog", "собака", "A0", None),
                    ("house", "дім", "A1", None),
                    ("school", "школа", "A1", None),
                    ("beautiful", "красивий", "A2", None),
                    ("important", "важливий", "A2", None),
                    ("necessary", "необхідний", "B1", None),
                    ("essential", "суттєвий", "B1", None),
                    ("significant", "значний", "B2", None),
                    ("fundamental", "фундаментальний", "B2", None),
                    ("sophisticated", "витончений", "C1", None),
                    ("elaborate", "детальний", "C1", None),
                    ("quintessential", "найтиповіший", "C2", None),
                    ("ubiquitous", "всюдисущий", "C2", None)
                ]
                
                for word, translation, level, audio in words_data:
                    await cursor.execute("""
                        INSERT IGNORE INTO words (word, translation, level_english, file_audio, check_admin)
                        VALUES (%s, %s, %s, %s, TRUE)
                    """, (word, translation, level, audio))
                
                await self.connection.commit()
                print("✅ Тестові дані додано успішно")
                
        except Exception as e:
            print(f"❌ Помилка додавання тестових даних: {e}")
            await self.connection.rollback()



