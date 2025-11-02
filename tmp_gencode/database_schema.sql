-- =====================================================
-- ENGLISH LEARNING BOT - DATABASE SCHEMA (7 TABLES)
-- =====================================================

-- Таблиця 1: Користувачі
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    user_id BIGINT UNIQUE NOT NULL,           -- Telegram user ID
    username VARCHAR(50),                      -- Telegram username
    first_name VARCHAR(100) NOT NULL,        -- Ім'я користувача
    last_name VARCHAR(100),                   -- Прізвище користувача
    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблиця 2: Прогрес користувача
CREATE TABLE user_progress (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,                  -- FK до users
    level_english VARCHAR(2) NOT NULL DEFAULT 'A0' 
        CHECK (level_english IN ('A0','A1','A2','B1','B2','C1','C2')),
    total_questions_answered INT DEFAULT 0,   -- Загальна кількість питань
    correct_answers INT DEFAULT 0,            -- Правильні відповіді
    accuracy DECIMAL(5,2) DEFAULT 0.0,       -- Точність у відсотках
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Таблиця 3: Налаштування користувача
CREATE TABLE settings (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,                  -- FK до users
    preferred_language VARCHAR(2) DEFAULT 'ua' 
        CHECK (preferred_language IN ('ua','en','pl')),
    notification_time TIME DEFAULT '08:00:00', -- Час нагадувань
    daily_goal INT DEFAULT 20,               -- Щоденна ціль питань
    
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Таблиця 4: Теми навчання
CREATE TABLE topics (
    id SERIAL PRIMARY KEY,
    topic VARCHAR(100) NOT NULL UNIQUE,      -- Назва теми (Tenses, Grammar, etc.)
    description TEXT,                         -- Опис теми
    icon VARCHAR(50) DEFAULT '📚',           -- Емодзі іконка
    is_active BOOLEAN DEFAULT TRUE           -- Чи активна тема
);

-- Таблиця 5: Словник
CREATE TABLE words (
    id SERIAL PRIMARY KEY,
    word VARCHAR(100) NOT NULL,              -- Англійське слово
    translation VARCHAR(200) NOT NULL,       -- Переклад українською
    level_english VARCHAR(2) NOT NULL 
        CHECK (level_english IN ('A0','A1','A2','B1','B2','C1','C2')),
    check_admin BOOLEAN DEFAULT FALSE,       -- Перевірено адміністратором
    file_audio VARCHAR(255),                 -- Шлях до аудіо файлу
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблиця 6: Банк питань
CREATE TABLE questions (
    id SERIAL PRIMARY KEY,
    question TEXT NOT NULL,                  -- Текст питання
    wrong_answer JSON NOT NULL,              -- Масив неправильних відповідей
    answer VARCHAR(500) NOT NULL,            -- Правильна відповідь
    topic_id INT NOT NULL,                   -- FK до topics
    level_english VARCHAR(2) NOT NULL 
        CHECK (level_english IN ('A0','A1','A2','B1','B2','C1','C2')),
    check_admin BOOLEAN DEFAULT FALSE,       -- Перевірено адміністратором
    level_question DECIMAL(2,1) DEFAULT 2.5 -- Складність від 1.0 до 5.0
        CHECK (level_question >= 1.0 AND level_question <= 5.0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE RESTRICT
);

-- Таблиця 7: Сесії тестування (НОВА!)
CREATE TABLE test_sessions (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,                 -- FK до users
    session_type VARCHAR(20) NOT NULL 
        CHECK (session_type IN ('level_test', 'word_study', 'topic_test', 'chatgpt_test')),
    topic_id INT,                            -- FK до topics (nullable для word_study)
    questions_answered INT DEFAULT 0,        -- Кількість питань у сесії
    correct_answers INT DEFAULT 0,           -- Правильні відповіді в сесії
    session_duration INT DEFAULT 0,          -- Тривалість в секундах
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,                  -- Час завершення сесії
    is_completed BOOLEAN DEFAULT FALSE,      -- Чи завершена сесія
    
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE SET NULL
);

-- =====================================================
-- ІНДЕКСИ ДЛЯ ОПТИМІЗАЦІЇ ПРОДУКТИВНОСТІ
-- =====================================================

-- Основні індекси
CREATE INDEX idx_users_user_id ON users(user_id);
CREATE INDEX idx_user_progress_user_id ON user_progress(user_id);
CREATE INDEX idx_settings_user_id ON settings(user_id);

-- Індекси для пошуку контенту
CREATE INDEX idx_words_level ON words(level_english);
CREATE INDEX idx_words_level_admin ON words(level_english, check_admin);
CREATE INDEX idx_questions_level ON questions(level_english);
CREATE INDEX idx_questions_topic ON questions(topic_id);
CREATE INDEX idx_questions_level_topic ON questions(level_english, topic_id);

-- Індекси для аналітики
CREATE INDEX idx_test_sessions_user ON test_sessions(user_id);
CREATE INDEX idx_test_sessions_user_completed ON test_sessions(user_id, is_completed);
CREATE INDEX idx_test_sessions_type ON test_sessions(session_type);
CREATE INDEX idx_test_sessions_date ON test_sessions(started_at);

-- =====================================================
-- ПОЧАТКОВІ ДАНІ
-- =====================================================

-- Додавання тем навчання
INSERT INTO topics (topic, description, icon) VALUES
('Tenses', 'Questions related to verb tenses in English (Present, Past, Future)', '⏰'),
('Grammar', 'Questions related to English grammar rules and structure', '📝'),
('Vocabulary', 'Questions related to English vocabulary and word meanings', '📚'),
('Reading Comprehension', 'Questions that test understanding of written English texts', '📖'),
('Listening', 'Questions based on audio content and pronunciation', '🎧'),
('Speaking Practice', 'Interactive speaking exercises and pronunciation practice', '🗣️');

-- Приклади слів для різних рівнів
INSERT INTO words (word, translation, level_english, check_admin, file_audio) VALUES
-- A0 Level (0-300 words)
('hello', 'привіт', 'A0', TRUE, 'audio/hello.mp3'),
('apple', 'яблуко', 'A0', TRUE, 'audio/apple.mp3'),
('cat', 'кіт', 'A0', TRUE, 'audio/cat.mp3'),
('dog', 'собака', 'A0', TRUE, 'audio/dog.mp3'),
('water', 'вода', 'A0', TRUE, 'audio/water.mp3'),

-- A1 Level (300-1000 words)  
('house', 'будинок', 'A1', TRUE, 'audio/house.mp3'),
('family', 'родина', 'A1', TRUE, 'audio/family.mp3'),
('work', 'робота', 'A1', TRUE, 'audio/work.mp3'),
('school', 'школа', 'A1', TRUE, 'audio/school.mp3'),
('friend', 'друг', 'A1', TRUE, 'audio/friend.mp3'),

-- A2 Level (1000-2500 words)
('environment', 'навколишнє середовище', 'A2', TRUE, 'audio/environment.mp3'),
('education', 'освіта', 'A2', TRUE, 'audio/education.mp3'),
('restaurant', 'ресторан', 'A2', TRUE, 'audio/restaurant.mp3'),
('vacation', 'відпустка', 'A2', TRUE, 'audio/vacation.mp3'),
('exercise', 'вправа, фізичні вправи', 'A2', TRUE, 'audio/exercise.mp3');

-- Приклади питань для різних тем
INSERT INTO questions (question, wrong_answer, answer, topic_id, level_english, check_admin, level_question) VALUES

-- Tenses (topic_id = 1)
('What is the past tense of "go"?', 
 '["goed", "gone", "goes"]', 
 'went', 1, 'A1', TRUE, 2.0),

('Choose the correct form: "I _____ coffee every morning."', 
 '["drinks", "drinking", "drank"]', 
 'drink', 1, 'A2', TRUE, 2.5),

('Which sentence is in Present Perfect?', 
 '["I go to school", "I went to school", "I will go to school"]', 
 'I have gone to school', 1, 'B1', TRUE, 3.5),

-- Grammar (topic_id = 2)
('Choose the correct article: "_____ apple is red."', 
 '["A", "The", "No article"]', 
 'An', 2, 'A1', TRUE, 2.0),

('What is the plural of "child"?', 
 '["childs", "childes", "child"]', 
 'children', 2, 'A2', TRUE, 3.0),

-- Vocabulary (topic_id = 3)
('What does "enormous" mean?', 
 '["very small", "medium size", "colorful"]', 
 'very big', 3, 'B2', TRUE, 4.0),

('Choose the synonym for "happy":', 
 '["sad", "angry", "tired"]', 
 'joyful', 3, 'A2', TRUE, 2.5);

-- =====================================================
-- ТРИГЕРИ ДЛЯ АВТОМАТИЧНОГО ОНОВЛЕННЯ
-- =====================================================

-- Тригер для автоматичного розрахунку accuracy в user_progress
CREATE OR REPLACE FUNCTION update_accuracy()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.total_questions_answered > 0 THEN
        NEW.accuracy = ROUND((NEW.correct_answers::DECIMAL / NEW.total_questions_answered) * 100, 2);
    ELSE
        NEW.accuracy = 0.0;
    END IF;
    NEW.last_updated = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_accuracy
    BEFORE UPDATE ON user_progress
    FOR EACH ROW
    EXECUTE FUNCTION update_accuracy();

-- Тригер для автоматичного завершення test_sessions
CREATE OR REPLACE FUNCTION auto_complete_session()
RETURNS TRIGGER AS $$
BEGIN
    -- Якщо встановлено completed_at, то сесія автоматично завершується
    IF NEW.completed_at IS NOT NULL AND OLD.completed_at IS NULL THEN
        NEW.is_completed = TRUE;
        NEW.session_duration = EXTRACT(EPOCH FROM (NEW.completed_at - NEW.started_at))::INT;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_auto_complete_session
    BEFORE UPDATE ON test_sessions
    FOR EACH ROW
    EXECUTE FUNCTION auto_complete_session();

-- =====================================================
-- ПРЕДСТАВЛЕННЯ (VIEWS) ДЛЯ АНАЛІТИКИ
-- =====================================================

-- Представлення для статистики користувачів
CREATE VIEW user_statistics AS
SELECT 
    u.user_id,
    u.first_name,
    u.last_name,
    up.level_english,
    up.total_questions_answered,
    up.correct_answers,
    up.accuracy,
    COUNT(ts.id) as total_sessions,
    AVG(ts.session_duration) as avg_session_duration,
    s.daily_goal,
    s.preferred_language
FROM users u
LEFT JOIN user_progress up ON u.user_id = up.user_id
LEFT JOIN settings s ON u.user_id = s.user_id
LEFT JOIN test_sessions ts ON u.user_id = ts.user_id AND ts.is_completed = TRUE
GROUP BY u.user_id, u.first_name, u.last_name, up.level_english, 
         up.total_questions_answered, up.correct_answers, up.accuracy,
         s.daily_goal, s.preferred_language;

-- Представлення для аналізу контенту по рівнях
CREATE VIEW content_by_level AS
SELECT 
    level_english,
    COUNT(DISTINCT w.id) as words_count,
    COUNT(DISTINCT q.id) as questions_count,
    AVG(q.level_question) as avg_question_difficulty
FROM (
    SELECT DISTINCT level_english FROM words
    UNION 
    SELECT DISTINCT level_english FROM questions
) levels
LEFT JOIN words w ON levels.level_english = w.level_english AND w.check_admin = TRUE
LEFT JOIN questions q ON levels.level_english = q.level_english AND q.check_admin = TRUE
GROUP BY levels.level_english
ORDER BY 
    CASE levels.level_english
        WHEN 'A0' THEN 1 WHEN 'A1' THEN 2 WHEN 'A2' THEN 3
        WHEN 'B1' THEN 4 WHEN 'B2' THEN 5 WHEN 'C1' THEN 6 WHEN 'C2' THEN 7
    END;

-- Представлення для щоденної активності
CREATE VIEW daily_activity AS
SELECT 
    DATE(started_at) as activity_date,
    COUNT(DISTINCT user_id) as active_users,
    COUNT(*) as total_sessions,
    SUM(questions_answered) as total_questions,
    AVG(session_duration) as avg_session_duration,
    SUM(CASE WHEN is_completed THEN 1 ELSE 0 END) as completed_sessions
FROM test_sessions
WHERE started_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE(started_at)
ORDER BY activity_date DESC;

-- =====================================================
-- ФУНКЦІЇ ДЛЯ РОБОТИ З ДАНИМИ
-- =====================================================

-- Функція для отримання рекомендованих слів для користувача
CREATE OR REPLACE FUNCTION get_recommended_words(
    p_user_id BIGINT,
    p_limit INT DEFAULT 20
)
RETURNS TABLE(
    word_id INT,
    word VARCHAR(100),
    translation VARCHAR(200),
    audio_file VARCHAR(255)
) AS $$
DECLARE
    user_level VARCHAR(2);
BEGIN
    -- Отримуємо поточний рівень користувача
    SELECT level_english INTO user_level 
    FROM user_progress 
    WHERE user_id = p_user_id;
    
    -- Якщо рівень не знайдено, встановлюємо A0
    IF user_level IS NULL THEN
        user_level := 'A0';
    END IF;
    
    -- Повертаємо випадкові слова для поточного рівня
    RETURN QUERY
    SELECT w.id, w.word, w.translation, w.file_audio
    FROM words w
    WHERE w.level_english = user_level
      AND w.check_admin = TRUE
    ORDER BY RANDOM()
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Функція для оновлення прогресу після тестової сесії
CREATE OR REPLACE FUNCTION update_progress_from_session(
    p_session_id INT
)
RETURNS BOOLEAN AS $$
DECLARE
    session_record test_sessions%ROWTYPE;
BEGIN
    -- Отримуємо дані сесії
    SELECT * INTO session_record
    FROM test_sessions
    WHERE id = p_session_id AND is_completed = TRUE;
    
    IF NOT FOUND THEN
        RETURN FALSE;
    END IF;
    
    -- Оновлюємо прогрес користувача
    UPDATE user_progress
    SET 
        total_questions_answered = total_questions_answered + session_record.questions_answered,
        correct_answers = correct_answers + session_record.correct_answers,
        last_updated = CURRENT_TIMESTAMP
    WHERE user_id = session_record.user_id;
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- КОМЕНТАРІ ДО СХЕМИ
-- =====================================================

COMMENT ON TABLE users IS 'Основна таблиця користувачів Telegram бота';
COMMENT ON TABLE user_progress IS 'Відстеження прогресу навчання кожного користувача';  
COMMENT ON TABLE settings IS 'Персональні налаштування користувачів';
COMMENT ON TABLE topics IS 'Каталог тем для навчання (граматика, лексика, тощо)';
COMMENT ON TABLE words IS 'Словник англійських слів з перекладами та аудіо';
COMMENT ON TABLE questions IS 'Банк тестових питань для різних тем та рівнів';
COMMENT ON TABLE test_sessions IS 'Історія всіх тестових сесій користувачів';

COMMENT ON COLUMN users.user_id IS 'Унікальний ID користувача з Telegram';
COMMENT ON COLUMN user_progress.accuracy IS 'Точність відповідей у відсотках (0.00-100.00)';
COMMENT ON COLUMN questions.wrong_answer IS 'JSON масив з неправильними варіантами відповідей';
COMMENT ON COLUMN questions.level_question IS 'Складність питання від 1.0 (легке) до 5.0 (складне)';
COMMENT ON COLUMN test_sessions.session_type IS 'Тип тестової сесії: level_test, word_study, topic_test, chatgpt_test';
COMMENT ON COLUMN test_sessions.session_duration IS 'Тривалість сесії в секундах';
