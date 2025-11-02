import asyncio
import aiomysql

# створити клас для роботи з базою даних
# --------------- Table: users -------------------
# | id | user_id | username | first_name | last_name | registration_date | user_progress_id |
# | 1 | 12345 | johndoe | John | Doe | 2024-09-15 | 1 |


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


class DB():
    def __init__(self, connection):
        self.connection = connection
        self.create_users_table()

    async def create_users_table(self):
        async with self.connection.cursor() as cursor:
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT UNIQUE,
                    username VARCHAR(255),
                    first_name VARCHAR(255),
                    last_name VARCHAR(255),
                    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    user_progress_id INT,
                    tg_id BIGINT,
                    tg_premium BOOLEAN,
                    tg_lang VARCHAR(10)
                );
            """)
            await self.connection.commit()

    async def add_user(self, user_id, username, first_name, last_name, tg_id, tg_premium, tg_lang):
        async with self.connection.cursor() as cursor:
            await cursor.execute("""
                INSERT INTO users (user_id, username, first_name, last_name, tg_id, tg_premium, tg_lang)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE username=VALUES(username), first_name=VALUES(first_name), last_name=VALUES(last_name);
            """, (user_id, username, first_name, last_name, tg_id, tg_premium, tg_lang))
            await self.connection.commit()

    async def get_user(self, user_id):
        async with self.connection.cursor() as cursor:
            await cursor.execute("SELECT * FROM users WHERE user_id = %s;", (user_id,))
            return await cursor.fetchone()



