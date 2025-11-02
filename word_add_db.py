# у папці list_words є файли  A0.json - C2.json з словами для кожного рівня потрібно додати в базу даних ці слова
import json

from db import Connection
from models import Words
import asyncio

# формати json файлів зі словами
# {
#     "hello": "привіт",
#     "goodbye": "до побачення",
#     "please": "будь ласка",
#     "thank you": "дякую",
#     ...
# }

async def add_words_to_db(level):
    # підключення до бази даних
    connection = Connection()
    await connection.connect()
    db = connection.engine
    async_session = connection.session_maker

    # шлях до файлу зі словами
    file_path = f'list_words/{level}.json'

    # читання файлу зі словами
    with open(file_path, 'r', encoding='utf-8') as file:
        words_data = json.load(file)

    # додавання слів до бази даних
    async with async_session() as session:
        for word, translation in words_data.items():
            new_word = Words(
                word=word,
                translation=translation,
                level_english=level,
                check_admin=False
            )
            session.add(new_word)
        await session.commit()
    print(f"Words for level {level} added to the database.")

if __name__ == "__main__":
    # levels = ["A0", "A1", "A2", "B1", "B2", "C1", "C2"]
    levels = ["C2"]
    loop = asyncio.get_event_loop()
    for level in levels:
        loop.run_until_complete(add_words_to_db(level))