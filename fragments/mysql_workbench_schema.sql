-- =====================================================
-- ENGLISH LEARNING BOT - DATABASE SCHEMA FOR MySQL WORKBENCH
-- 7 TABLES WITH DIFFERENT RELATIONSHIP TYPES
-- =====================================================

-- Створення бази даних
CREATE DATABASE IF NOT EXISTS english_learning_bot 
    CHARACTER SET utf8mb4 
    COLLATE utf8mb4_unicode_ci;

USE english_learning_bot;

-- Вимкнути перевірку foreign key для створення таблиць
SET FOREIGN_KEY_CHECKS = 0;

-- =====================================================
-- ТАБЛИЦЯ 1: КОРИСТУВАЧІ (ОСНОВНА ТАБЛИЦЯ)
-- =====================================================
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT UNIQUE NOT NULL COMMENT 'Telegram user ID',
    username VARCHAR(50) COMMENT 'Telegram username',
    first_name VARCHAR(100) NOT NULL COMMENT 'Ім\'я користувача',
    last_name VARCHAR(100) COMMENT 'Прізвище користувача',
    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Дата реєстрації',
    is_active BOOLEAN DEFAULT TRUE COMMENT 'Чи активний користувач',
    
    INDEX idx_user_id (user_id),
    INDEX idx_username (username),
    INDEX idx_registration_date (registration_date)
) ENGINE=InnoDB COMMENT='Основна таблиця користувачів системи';

-- =====================================================
-- ТАБЛИЦЯ 2: ПРОГРЕС КОРИСТУВАЧІВ (ЗВ'ЯЗОК 1:1 З USERS)
-- =====================================================
CREATE TABLE user_progress (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL COMMENT 'FK до users.user_id',
    level_english ENUM('A0','A1','A2','B1','B2','C1','C2') 
        NOT NULL DEFAULT 'A0' COMMENT 'Поточний рівень англійської',
    total_questions_answered INT DEFAULT 0 COMMENT 'Загальна кількість питань',
    correct_answers INT DEFAULT 0 COMMENT 'Правильні відповіді',
    accuracy DECIMAL(5,2) DEFAULT 0.00 COMMENT 'Точність у відсотках',
    words_learned INT DEFAULT 0 COMMENT 'Кількість вивчених слів',
    study_streak_days INT DEFAULT 0 COMMENT 'Дні поспіль навчання',
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY unique_user_progress (user_id),
    FOREIGN KEY fk_progress_user (user_id) 
        REFERENCES users(user_id) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE,
    
    INDEX idx_level (level_english),
    INDEX idx_accuracy (accuracy),
    INDEX idx_last_updated (last_updated)
) ENGINE=InnoDB COMMENT='Прогрес навчання користувачів (1:1 з users)';

-- =====================================================
-- ТАБЛИЦЯ 3: НАЛАШТУВАННЯ (ЗВ'ЯЗОК 1:1 З USERS)
-- =====================================================
CREATE TABLE settings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL COMMENT 'FK до users.user_id',
    preferred_language ENUM('ua','en','pl','ru') DEFAULT 'ua' 
        COMMENT 'Мова інтерфейсу',
    notification_time TIME DEFAULT '08:00:00' 
        COMMENT 'Час щоденних нагадувань',
    daily_goal INT DEFAULT 20 
        COMMENT 'Щоденна ціль питань',
    notifications_enabled BOOLEAN DEFAULT TRUE 
        COMMENT 'Чи увімкнені нагадування',
    sound_enabled BOOLEAN DEFAULT TRUE 
        COMMENT 'Чи увімкнений звук',
    difficulty_preference ENUM('easy','medium','hard','adaptive') DEFAULT 'adaptive'
        COMMENT 'Налаштування складності',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY unique_user_settings (user_id),
    FOREIGN KEY fk_settings_user (user_id) 
        REFERENCES users(user_id) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE,
    
    INDEX idx_notifications (notifications_enabled, notification_time),
    INDEX idx_language (preferred_language)
) ENGINE=InnoDB COMMENT='Персональні налаштування користувачів (1:1 з users)';

-- =====================================================
-- ТАБЛИЦЯ 4: ТЕМИ НАВЧАННЯ (З САМОРЕФЕРЕНЦІЄЮ)
-- =====================================================
CREATE TABLE topics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    topic VARCHAR(100) NOT NULL COMMENT 'Назва теми',
    description TEXT COMMENT 'Опис теми',
    parent_topic_id INT NULL COMMENT 'FK до topics.id (батьківська тема)',
    icon VARCHAR(50) DEFAULT '📚' COMMENT 'Емодзі іконка',
    difficulty_level ENUM('beginner','intermediate','advanced') DEFAULT 'beginner',
    is_active BOOLEAN DEFAULT TRUE COMMENT 'Чи активна тема',
    sort_order INT DEFAULT 0 COMMENT 'Порядок сортування',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE KEY unique_topic_name (topic),
    FOREIGN KEY fk_parent_topic (parent_topic_id) 
        REFERENCES topics(id) 
        ON DELETE SET NULL 
        ON UPDATE CASCADE,
    
    INDEX idx_parent_topic (parent_topic_id),
    INDEX idx_active_topics (is_active, sort_order),
    INDEX idx_difficulty (difficulty_level)
) ENGINE=InnoDB COMMENT='Теми навчання з ієрархічною структурою (самореференція)';

-- =====================================================
-- ТАБЛИЦЯ 5: СЛОВНИК СЛІВ
-- =====================================================
CREATE TABLE words (
    id INT AUTO_INCREMENT PRIMARY KEY,
    word VARCHAR(100) NOT NULL COMMENT 'Англійське слово',
    translation VARCHAR(200) NOT NULL COMMENT 'Переклад українською',
    phonetic VARCHAR(100) COMMENT 'Фонетична транскрипція',
    level_english ENUM('A0','A1','A2','B1','B2','C1','C2') NOT NULL 
        COMMENT 'Рівень складності слова',
    part_of_speech ENUM('noun','verb','adjective','adverb','preposition','other') 
        DEFAULT 'noun' COMMENT 'Частина мови',
    frequency_rank INT COMMENT 'Ранг частотності використання',
    check_admin BOOLEAN DEFAULT FALSE COMMENT 'Перевірено адміністратором',
    file_audio VARCHAR(255) COMMENT 'Шлях до аудіо файлу',
    example_sentence TEXT COMMENT 'Приклад використання',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY unique_word_level (word, level_english),
    INDEX idx_level_admin (level_english, check_admin),
    INDEX idx_word_search (word),
    INDEX idx_frequency (frequency_rank),
    INDEX idx_part_of_speech (part_of_speech),
    FULLTEXT idx_word_translation (word, translation, example_sentence)
) ENGINE=InnoDB COMMENT='Словник англійських слів з перекладами';

-- =====================================================
-- ТАБЛИЦЯ 6: БАНК ПИТАНЬ (ЗВ'ЯЗОК N:1 З TOPICS)
-- =====================================================
CREATE TABLE questions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    question TEXT NOT NULL COMMENT 'Текст питання',
    option_a VARCHAR(500) NOT NULL COMMENT 'Варіант відповіді A',
    option_b VARCHAR(500) NOT NULL COMMENT 'Варіант відповіді B', 
    option_c VARCHAR(500) NOT NULL COMMENT 'Варіант відповіді C',
    option_d VARCHAR(500) NOT NULL COMMENT 'Варіант відповіді D',
    correct_answer ENUM('A','B','C','D') NOT NULL COMMENT 'Правильна відповідь',
    explanation TEXT COMMENT 'Пояснення правильної відповіді',
    topic_id INT NOT NULL COMMENT 'FK до topics.id',
    level_english ENUM('A0','A1','A2','B1','B2','C1','C2') NOT NULL 
        COMMENT 'Рівень складності питання',
    difficulty_score DECIMAL(2,1) DEFAULT 2.5 
        COMMENT 'Складність від 1.0 до 5.0'
        CHECK (difficulty_score >= 1.0 AND difficulty_score <= 5.0),
    check_admin BOOLEAN DEFAULT FALSE COMMENT 'Перевірено адміністратором',
    usage_count INT DEFAULT 0 COMMENT 'Кількість використань',
    success_rate DECIMAL(5,2) DEFAULT 0.00 COMMENT 'Відсоток правильних відповідей',
    created_by ENUM('admin','chatgpt','import') DEFAULT 'admin' 
        COMMENT 'Джерело створення питання',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY fk_question_topic (topic_id) 
        REFERENCES topics(id) 
        ON DELETE RESTRICT 
        ON UPDATE CASCADE,
    
    INDEX idx_topic_level (topic_id, level_english),
    INDEX idx_difficulty (difficulty_score),
    INDEX idx_admin_approved (check_admin, level_english),
    INDEX idx_success_rate (success_rate),
    FULLTEXT idx_question_search (question, explanation)
) ENGINE=InnoDB COMMENT='Банк тестових питань (N:1 з topics)';

-- =====================================================
-- ТАБЛИЦЯ 7: ТЕСТОВІ СЕСІЇ (ЗВ'ЯЗКИ З USERS, TOPICS, USER_PROGRESS)
-- =====================================================
CREATE TABLE test_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL COMMENT 'FK до users.user_id',
    session_type ENUM('level_test','word_study','topic_test','chatgpt_test','mixed_test') 
        NOT NULL COMMENT 'Тип тестової сесії',
    topic_id INT NULL COMMENT 'FK до topics.id (може бути NULL для word_study)',
    session_name VARCHAR(200) COMMENT 'Назва сесії',
    questions_answered INT DEFAULT 0 COMMENT 'Кількість відповідей у сесії',
    correct_answers INT DEFAULT 0 COMMENT 'Правильні відповіді в сесії',
    session_accuracy DECIMAL(5,2) DEFAULT 0.00 COMMENT 'Точність сесії у відсотках',
    session_duration INT DEFAULT 0 COMMENT 'Тривалість в секундах',
    average_response_time DECIMAL(6,2) DEFAULT 0.00 COMMENT 'Середній час відповіді в секундах',
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Початок сесії',
    completed_at TIMESTAMP NULL COMMENT 'Завершення сесії',
    is_completed BOOLEAN DEFAULT FALSE COMMENT 'Чи завершена сесія',
    session_notes TEXT COMMENT 'Додаткові нотатки про сесію',
    
    FOREIGN KEY fk_session_user (user_id) 
        REFERENCES users(user_id) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE,
    FOREIGN KEY fk_session_topic (topic_id) 
        REFERENCES topics(id) 
        ON DELETE SET NULL 
        ON UPDATE CASCADE,
    
    INDEX idx_user_sessions (user_id, is_completed),
    INDEX idx_session_type (session_type),
    INDEX idx_topic_sessions (topic_id, completed_at),
    INDEX idx_completion_date (completed_at),
    INDEX idx_session_accuracy (session_accuracy)
) ENGINE=InnoDB COMMENT='Історія тестових сесій користувачів (зв\'язки з users, topics)';

-- Увімкнути перевірку foreign key
SET FOREIGN_KEY_CHECKS = 1;

-- =====================================================
-- ПОЧАТКОВІ ДАНІ ДЛЯ ДЕМОНСТРАЦІЇ ЗВ'ЯЗКІВ
-- =====================================================

-- Додавання основних тем (батьківські теми)
INSERT INTO topics (topic, description, parent_topic_id, icon, difficulty_level, sort_order) VALUES
('Grammar', 'English Grammar Rules and Structure', NULL, '📝', 'beginner', 1),
('Vocabulary', 'English Words and Meanings', NULL, '📚', 'beginner', 2),
('Tenses', 'Verb Tenses in English', NULL, '⏰', 'intermediate', 3),
('Reading', 'Reading Comprehension Skills', NULL, '📖', 'intermediate', 4),
('Listening', 'Audio Content and Pronunciation', NULL, '🎧', 'advanced', 5);

-- Додавання підтем (демонстрація самореференції)
INSERT INTO topics (topic, description, parent_topic_id, icon, difficulty_level, sort_order) VALUES
('Present Tenses', 'Present Simple, Present Continuous, Present Perfect', 3, '⏰', 'beginner', 1),
('Past Tenses', 'Past Simple, Past Continuous, Past Perfect', 3, '⏰', 'intermediate', 2),
('Future Tenses', 'Future Simple, Future Continuous, Future Perfect', 3, '⏰', 'intermediate', 3),
('Articles', 'A, An, The usage rules', 1, '📝', 'beginner', 1),
('Prepositions', 'In, On, At, By, For, etc.', 1, '📝', 'intermediate', 2),
('Basic Vocabulary', 'Common everyday words', 2, '📚', 'beginner', 1),
('Advanced Vocabulary', 'Academic and professional terms', 2, '📚', 'advanced', 2);

-- Додавання тестових користувачів
INSERT INTO users (user_id, username, first_name, last_name) VALUES
(12345, 'johndoe', 'John', 'Doe'),
(67890, 'mariasmith', 'Maria', 'Smith'),
(11111, 'alexbrown', 'Alex', 'Brown');

-- Додавання прогресу користувачів (1:1 зв'язок)
INSERT INTO user_progress (user_id, level_english, total_questions_answered, correct_answers, words_learned, study_streak_days) VALUES
(12345, 'A2', 150, 120, 45, 7),
(67890, 'B1', 280, 220, 78, 12),
(11111, 'A1', 95, 70, 25, 3);

-- Додавання налаштувань користувачів (1:1 зв'язок)
INSERT INTO settings (user_id, preferred_language, notification_time, daily_goal, difficulty_preference) VALUES
(12345, 'ua', '08:00:00', 20, 'adaptive'),
(67890, 'en', '19:30:00', 30, 'medium'),
(11111, 'ua', '10:00:00', 15, 'easy');

-- Додавання слів
INSERT INTO words (word, translation, phonetic, level_english, part_of_speech, frequency_rank, check_admin, example_sentence) VALUES
('apple', 'яблуко', '/ˈæp.əl/', 'A0', 'noun', 1500, TRUE, 'I eat an apple every day.'),
('beautiful', 'красивий', '/ˈbjuː.tɪ.fəl/', 'A1', 'adjective', 800, TRUE, 'She has a beautiful smile.'),
('environment', 'навколишнє середовище', '/ɪnˈvaɪ.rən.mənt/', 'B1', 'noun', 400, TRUE, 'We must protect our environment.'),
('sophisticated', 'витончений', '/səˈfɪs.tɪ.keɪ.tɪd/', 'C1', 'adjective', 1200, TRUE, 'He has sophisticated taste in art.'),
('house', 'будинок', '/haʊs/', 'A0', 'noun', 200, TRUE, 'My house is big and comfortable.');

-- Додавання питань (N:1 зв'язок з topics)
INSERT INTO questions (question, option_a, option_b, option_c, option_d, correct_answer, explanation, topic_id, level_english, difficulty_score, check_admin, created_by) VALUES
('What is the past tense of "go"?', 'goed', 'went', 'gone', 'goes', 'B', 'The past tense of "go" is "went".', 7, 'A1', 2.0, TRUE, 'admin'),
('Choose the correct article: "__ apple is red."', 'A', 'An', 'The', 'No article', 'B', 'Use "an" before words starting with vowel sounds.', 9, 'A1', 1.5, TRUE, 'admin'),
('I __ coffee every morning.', 'drink', 'drinks', 'drinking', 'drank', 'A', 'Use present simple "drink" for habits.', 6, 'A2', 2.5, TRUE, 'chatgpt'),
('Which sentence is in Present Perfect?', 'I go to school', 'I went to school', 'I have gone to school', 'I will go to school', 'C', 'Present Perfect uses have/has + past participle.', 6, 'B1', 3.5, TRUE, 'admin'),
('What does "sophisticated" mean?', 'simple', 'complex and refined', 'old-fashioned', 'broken', 'B', '"Sophisticated" means complex, refined, or developed.', 12, 'C1', 4.0, TRUE, 'admin');

-- Додавання тестових сесій (демонстрація зв'язків з users, topics)
INSERT INTO test_sessions (user_id, session_type, topic_id, session_name, questions_answered, correct_answers, session_duration, is_completed, completed_at) VALUES
(12345, 'topic_test', 6, 'Present Tenses Practice', 10, 8, 450, TRUE, '2024-10-20 10:30:00'),
(12345, 'word_study', NULL, 'Daily Vocabulary', 20, 16, 600, TRUE, '2024-10-21 09:15:00'),
(67890, 'chatgpt_test', 1, 'Grammar Challenge', 25, 22, 900, TRUE, '2024-10-21 14:20:00'),
(11111, 'level_test', NULL, 'Initial Assessment', 50, 35, 1800, TRUE, '2024-10-19 16:45:00'),
(67890, 'mixed_test', 4, 'Reading Comprehension', 15, 13, 720, TRUE, '2024-10-22 11:00:00');

-- =====================================================
-- ТРИГЕРИ ДЛЯ АВТОМАТИЧНОГО ОНОВЛЕННЯ СТАТИСТИКИ
-- =====================================================

DELIMITER //

-- Тригер для автоматичного розрахунку accuracy в user_progress
CREATE TRIGGER update_user_accuracy
    BEFORE UPDATE ON user_progress
    FOR EACH ROW
BEGIN
    IF NEW.total_questions_answered > 0 THEN
        SET NEW.accuracy = ROUND((NEW.correct_answers / NEW.total_questions_answered) * 100, 2);
    ELSE
        SET NEW.accuracy = 0.00;
    END IF;
END //

-- Тригер для автоматичного розрахунку session_accuracy
CREATE TRIGGER update_session_accuracy
    BEFORE UPDATE ON test_sessions
    FOR EACH ROW
BEGIN
    IF NEW.questions_answered > 0 THEN
        SET NEW.session_accuracy = ROUND((NEW.correct_answers / NEW.questions_answered) * 100, 2);
    ELSE
        SET NEW.session_accuracy = 0.00;
    END IF;
    
    -- Автоматично встановлювати is_completed = TRUE якщо completed_at не NULL
    IF NEW.completed_at IS NOT NULL AND OLD.completed_at IS NULL THEN
        SET NEW.is_completed = TRUE;
        SET NEW.session_duration = TIMESTAMPDIFF(SECOND, NEW.started_at, NEW.completed_at);
    END IF;
END //

-- Тригер для оновлення статистики питань
CREATE TRIGGER update_question_stats
    AFTER INSERT ON test_sessions
    FOR EACH ROW
BEGIN
    -- Оновлення статистики використання питань (якщо є topic_id)
    IF NEW.topic_id IS NOT NULL AND NEW.is_completed = TRUE THEN
        UPDATE questions 
        SET usage_count = usage_count + NEW.questions_answered,
            success_rate = ROUND(((success_rate * usage_count) + (NEW.session_accuracy * NEW.questions_answered)) / (usage_count + NEW.questions_answered), 2)
        WHERE topic_id = NEW.topic_id;
    END IF;
END //

DELIMITER ;

-- =====================================================
-- ПРЕДСТАВЛЕННЯ (VIEWS) ДЛЯ ЗРУЧНОГО ДОСТУПУ ДО ДАНИХ
-- =====================================================

-- Представлення для повної інформації про користувачів
CREATE VIEW user_full_info AS
SELECT 
    u.id,
    u.user_id,
    u.username,
    CONCAT(u.first_name, ' ', COALESCE(u.last_name, '')) as full_name,
    u.registration_date,
    u.is_active,
    up.level_english,
    up.total_questions_answered,
    up.correct_answers,
    up.accuracy,
    up.words_learned,
    up.study_streak_days,
    up.last_updated as progress_updated,
    s.preferred_language,
    s.daily_goal,
    s.notifications_enabled,
    s.difficulty_preference
FROM users u
LEFT JOIN user_progress up ON u.user_id = up.user_id
LEFT JOIN settings s ON u.user_id = s.user_id;

-- Представлення для ієрархії тем
CREATE VIEW topics_hierarchy AS
SELECT 
    t.id,
    t.topic,
    t.description,
    t.parent_topic_id,
    pt.topic as parent_topic_name,
    t.difficulty_level,
    t.is_active,
    COUNT(st.id) as subtopics_count,
    COUNT(q.id) as questions_count
FROM topics t
LEFT JOIN topics pt ON t.parent_topic_id = pt.id
LEFT JOIN topics st ON st.parent_topic_id = t.id
LEFT JOIN questions q ON q.topic_id = t.id
GROUP BY t.id, t.topic, t.description, t.parent_topic_id, pt.topic, t.difficulty_level, t.is_active;

-- Представлення для статистики сесій
CREATE VIEW session_statistics AS
SELECT 
    ts.user_id,
    u.first_name,
    u.last_name,
    up.level_english,
    COUNT(ts.id) as total_sessions,
    COUNT(CASE WHEN ts.is_completed = TRUE THEN 1 END) as completed_sessions,
    AVG(ts.session_accuracy) as avg_accuracy,
    SUM(ts.session_duration) as total_study_time,
    AVG(ts.session_duration) as avg_session_duration,
    MAX(ts.completed_at) as last_session_date,
    COUNT(CASE WHEN ts.completed_at >= DATE_SUB(NOW(), INTERVAL 7 DAY) THEN 1 END) as sessions_this_week
FROM test_sessions ts
JOIN users u ON ts.user_id = u.user_id
JOIN user_progress up ON u.user_id = up.user_id
GROUP BY ts.user_id, u.first_name, u.last_name, up.level_english;

-- =====================================================
-- ФУНКЦІЇ ДЛЯ РОБОТИ З ДАНИМИ
-- =====================================================

DELIMITER //

-- Функція для отримання рекомендованих слів
CREATE FUNCTION get_user_level_words(p_user_id BIGINT, p_limit INT)
RETURNS JSON
READS SQL DATA
DETERMINISTIC
BEGIN
    DECLARE user_level VARCHAR(2);
    DECLARE words_json JSON;
    
    -- Отримати рівень користувача
    SELECT level_english INTO user_level 
    FROM user_progress 
    WHERE user_id = p_user_id;
    
    IF user_level IS NULL THEN
        SET user_level = 'A0';
    END IF;
    
    -- Отримати слова у форматі JSON
    SELECT JSON_ARRAYAGG(
        JSON_OBJECT(
            'word', word,
            'translation', translation,
            'phonetic', phonetic,
            'example', example_sentence
        )
    ) INTO words_json
    FROM words 
    WHERE level_english = user_level 
      AND check_admin = TRUE
    ORDER BY RAND()
    LIMIT p_limit;
    
    RETURN words_json;
END //

-- Процедура для оновлення прогресу після сесії
CREATE PROCEDURE update_progress_after_session(
    IN p_session_id INT
)
BEGIN
    DECLARE session_user_id BIGINT;
    DECLARE session_questions INT;
    DECLARE session_correct INT;
    DECLARE session_completed BOOLEAN;
    
    -- Отримати дані сесії
    SELECT user_id, questions_answered, correct_answers, is_completed
    INTO session_user_id, session_questions, session_correct, session_completed
    FROM test_sessions
    WHERE id = p_session_id;
    
    -- Оновити прогрес користувача тільки для завершених сесій
    IF session_completed = TRUE THEN
        UPDATE user_progress
        SET 
            total_questions_answered = total_questions_answered + session_questions,
            correct_answers = correct_answers + session_correct,
            last_updated = NOW()
        WHERE user_id = session_user_id;
    END IF;
END //

DELIMITER ;

-- =====================================================
-- ІНДЕКСИ ДЛЯ ОПТИМІЗАЦІЇ ПРОДУКТИВНОСТІ
-- =====================================================

-- Композитні індекси для складних запитів
CREATE INDEX idx_sessions_user_type_completed ON test_sessions(user_id, session_type, is_completed);
CREATE INDEX idx_questions_topic_level_admin ON questions(topic_id, level_english, check_admin);
CREATE INDEX idx_words_level_frequency ON words(level_english, frequency_rank);
CREATE INDEX idx_progress_level_accuracy ON user_progress(level_english, accuracy);

-- =====================================================
-- КОМЕНТАРІ ДО СХЕМИ
-- =====================================================

-- Додавання коментарів до таблиць
ALTER TABLE users COMMENT = 'Основна таблиця користувачів Telegram бота';
ALTER TABLE user_progress COMMENT = 'Прогрес навчання користувачів (1:1 з users)';
ALTER TABLE settings COMMENT = 'Персональні налаштування (1:1 з users)';
ALTER TABLE topics COMMENT = 'Ієрархічна структура тем навчання (самореференція)';
ALTER TABLE words COMMENT = 'Словник англійських слів з аудіо та прикладами';
ALTER TABLE questions COMMENT = 'Банк тестових питань (N:1 з topics)';
ALTER TABLE test_sessions COMMENT = 'Історія тестових сесій (зв\'язки з users, topics)';

-- =====================================================
-- ПРИКЛАДИ ЗАПИТІВ ДЛЯ ДЕМОНСТРАЦІЇ ЗВ'ЯЗКІВ
-- =====================================================

/*
-- 1. Отримати повну інформацію про користувача з прогресом і налаштуваннями (1:1 зв'язки)
SELECT * FROM user_full_info WHERE user_id = 12345;

-- 2. Показати ієрархію тем з підтемами (самореференція)
SELECT 
    CASE 
        WHEN parent_topic_name IS NULL THEN topic
        ELSE CONCAT('  └─ ', topic, ' (', parent_topic_name, ')')
    END as topic_hierarchy,
    questions_count
FROM topics_hierarchy 
ORDER BY COALESCE(parent_topic_id, id), id;

-- 3. Статистика сесій користувача з інформацією про теми (багато зв'язків)
SELECT 
    ts.session_name,
    t.topic as topic_name,
    ts.session_accuracy,
    ts.session_duration,
    ts.completed_at
FROM test_sessions ts
LEFT JOIN topics t ON ts.topic_id = t.id
WHERE ts.user_id = 12345 AND ts.is_completed = TRUE
ORDER BY ts.completed_at DESC;

-- 4. Питання по темах з урахуванням ієрархії
SELECT 
    pt.topic as main_topic,
    t.topic as subtopic,
    q.question,
    q.level_english,
    q.success_rate
FROM questions q
JOIN topics t ON q.topic_id = t.id
LEFT JOIN topics pt ON t.parent_topic_id = pt.id
WHERE q.check_admin = TRUE
ORDER BY pt.topic, t.topic, q.difficulty_score;

-- 5. Аналіз прогресу користувачів по рівнях
SELECT 
    up.level_english,
    COUNT(*) as users_count,
    AVG(up.accuracy) as avg_accuracy,
    AVG(ss.total_sessions) as avg_sessions
FROM user_progress up
LEFT JOIN session_statistics ss ON up.user_id = ss.user_id
GROUP BY up.level_english
ORDER BY up.level_english;
*/
