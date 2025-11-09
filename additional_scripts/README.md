# Additional Scripts

## generate_questions.py

Скрипт для автоматичної генерації тестових питань через GPT-4 та додавання їх у базу даних.

### Використання:

```bash
python additional_scripts/generate_questions.py
```

### Що робить скрипт:

1. Підключається до бази даних
2. Додає теми (Topics) якщо їх ще немає
3. Генерує питання для кожної теми та рівня
4. Зберігає питання в таблицю `questions`

### Конфігурація:

Відредагуйте `TOPICS_CONFIG` у файлі для зміни:
- Тем
- Рівнів
- Кількості питань на рівень

### Приклад виводу:

```
============================================================
GPT Question Generator for English Learning Bot
============================================================

Connecting to database...
✓ Connected to database

Adding topics to database...
  ✓ Added topic: Tenses
  ✓ Added topic: Grammar
  ✓ Added topic: Vocabulary

============================================================
Topic: Tenses
============================================================

Generating 10 questions for Tenses - A1...
  Generating question 1/10... ✓
  Generating question 2/10... ✓
  ...
  Results: 10 success, 0 failed

============================================================
SUMMARY
============================================================
Total questions generated: 320
Total failures: 0
Success rate: 100.0%
============================================================
```

## word_add_db.py

Скрипт для додавання слів з JSON файлів до бази даних.

## testdb.py

Скрипт для тестування підключення до бази даних.
