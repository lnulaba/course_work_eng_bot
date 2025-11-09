import asyncio
import json
import sys
from pathlib import Path

# Додати кореневу директорію до sys.path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from g4f.client import Client
from db import Connection, DB

# Конфігурація генерації
TOPICS_CONFIG = {
    "Tenses": {
        "description": "Questions about English verb tenses",
        "levels": ["A1", "A2", "B1", "B2", "C1", "C2"],
        "questions_per_level": 10
    },
    "Grammar": {
        "description": "Questions about English grammar rules",
        "levels": ["A1", "A2", "B1", "B2", "C1", "C2"],
        "questions_per_level": 10
    },
    "Vocabulary": {
        "description": "Questions about English vocabulary",
        "levels": ["A1", "A2", "B1", "B2", "C1", "C2"],
        "questions_per_level": 10
    },
    "Prepositions": {
        "description": "Questions about English prepositions",
        "levels": ["A2", "B1", "B2", "C1"],
        "questions_per_level": 8
    }
}

def generate_question_with_gpt(topic: str, level: str) -> dict:
    """Згенерувати одне питання через GPT"""
    client = Client()
    
    prompt = f"""Generate 1 English grammar question for level {level} on the topic "{topic}".

Requirements:
- Question must be in English
- Provide exactly 4 incorrect answer options
- Provide 1 correct answer
- Provide a brief explanation (1-2 sentences) in UKRAINIAN (українською мовою) why the answer is correct
- Question difficulty should match {level} level (A1=beginner, C2=advanced)
- Make it practical and useful for learning

Return ONLY a valid JSON object in this exact format:
{{
    "question": "question text here in English",
    "wrong_answers": ["wrong1", "wrong2", "wrong3", "wrong4"],
    "answer": "correct answer here in English",
    "explanation": "пояснення українською мовою, чому ця відповідь правильна"
}}

IMPORTANT: The explanation MUST be in Ukrainian language!

Do not include any explanations, markdown, or extra text. Just the JSON."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            web_search=False
        )
        
        content = response.choices[0].message.content.strip()
        
        # Видалити markdown блоки якщо є
        if content.startswith("```"):
            lines = content.split('\n')
            content = '\n'.join(lines[1:-1]) if len(lines) > 2 else content
            content = content.replace("```json", "").replace("```", "").strip()
        
        # Знайти JSON об'єкт у тексті
        # Шукаємо від першої { до останньої }
        start_idx = content.find('{')
        end_idx = content.rfind('}')
        
        if start_idx == -1 or end_idx == -1:
            raise ValueError(f"No JSON object found in response: {content}")
        
        json_str = content[start_idx:end_idx+1]
        
        # Парсити JSON
        question_data = json.loads(json_str)
        
        # Валідація
        required_keys = ["question", "wrong_answers", "answer"]
        if not all(key in question_data for key in required_keys):
            raise ValueError(f"Missing required keys in response: {question_data}")
        
        if not isinstance(question_data["wrong_answers"], list) or len(question_data["wrong_answers"]) != 4:
            raise ValueError(f"wrong_answers must be a list of 4 items: {question_data}")
        
        return question_data
        
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON from: {content[:200]}...")
        print(f"Error: {e}")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

async def add_topics_to_db(db: DB):
    """Додати всі теми до бази даних"""
    print("Adding topics to database...")
    for topic, config in TOPICS_CONFIG.items():
        await db.add_topic(topic, config["description"])
        print(f"  ✓ Added topic: {topic}")

async def generate_and_add_questions(db: DB, topic: str, level: str, count: int):
    """Згенерувати та додати питання до БД"""
    print(f"\nGenerating {count} questions for {topic} - {level}...")
    
    success_count = 0
    failed_count = 0
    
    for i in range(count):
        print(f"  Generating question {i+1}/{count}...", end=" ")
        
        question_data = generate_question_with_gpt(topic, level)
        
        if question_data:
            try:
                # Визначити складність питання на основі рівня
                level_difficulty = {
                    "A1": 1.5, "A2": 2.0, "B1": 2.5,
                    "B2": 3.5, "C1": 4.0, "C2": 4.5
                }.get(level, 2.5)
                
                await db.add_question(
                    question=question_data["question"],
                    wrong_answers=question_data["wrong_answers"],
                    answer=question_data["answer"],
                    explanation=question_data.get("explanation"),  # Додати пояснення
                    topic=topic,
                    level_english=level,
                    level_question=level_difficulty
                )
                success_count += 1
                print("✓")
            except Exception as e:
                print(f"✗ (DB Error: {e})")
                failed_count += 1
        else:
            print("✗ (Generation failed)")
            failed_count += 1
        
        # Невелика затримка між запитами
        await asyncio.sleep(1)
    
    print(f"  Results: {success_count} success, {failed_count} failed")
    return success_count, failed_count

async def main():
    """Головна функція"""
    print("=" * 60)
    print("GPT Question Generator for English Learning Bot")
    print("=" * 60)
    
    # Підключення до БД
    print("\nConnecting to database...")
    connection = Connection()
    await connection.connect()
    db = DB(connection.session_maker)
    print("✓ Connected to database")
    
    # Додати теми
    await add_topics_to_db(db)
    
    # Генерація питань
    total_success = 0
    total_failed = 0
    
    for topic, config in TOPICS_CONFIG.items():
        print(f"\n{'='*60}")
        print(f"Topic: {topic}")
        print(f"{'='*60}")
        
        for level in config["levels"]:
            success, failed = await generate_and_add_questions(
                db, topic, level, config["questions_per_level"]
            )
            total_success += success
            total_failed += failed
    
    # Підсумок
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Total questions generated: {total_success}")
    print(f"Total failures: {total_failed}")
    print(f"Success rate: {total_success/(total_success+total_failed)*100:.1f}%")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())
