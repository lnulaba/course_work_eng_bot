from g4f.client import Client

client = Client()

# text = """Згенеруй json з 1 питання англійською мовою на тему часи. а також відповідь який це час у форматі {"question": "тут питання", "answer": "тут відповідь"}"""
text = """Згенеруй json з 1 питання англійською мовою на тему часи, де потрібно поставити слово в правильний час, також напиши 4 не правильні варіанти відповіді. у форматі {"question": "тут питання", "options": ["варіант1", "варіант2", "варіант3", "варіант4", ], "answer": "правильний варіант"}"""

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": text}],
    web_search=False
)

print(response.choices[0].message.content)