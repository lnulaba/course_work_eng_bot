import logging
import asyncio
from datetime import datetime, timedelta
from openai import OpenAI, AsyncOpenAI

# Конфігурація ключів
api_keys = {
    "my": "6bd60986ac8544d08311d5f0a1736393",
    "github1": "f0af93f61ad44ceeb26a4aca6be8e75c",
    "github3": "74b0c0abd2294719ba29967c27bde367",
    "github5": "0710951b319a4cd79e155a8e40413658",
    "github7": "09c8c09c82764e73a906a8f353115bec",
    "github8": "8df72ab4814643ca897ee213f4d2b054",
    "github9": "afd78080d3314927bc2d9ffc44ae6215",
    "github10": "05eaba6dd95047d4bb17657d26f71cac",
    "github11": "a4e0c569dfe04440a9dc81720921d809",
    "github12": "8b10e507d0ae4eeb9c591d3da3273e22",
    "github14": "417c93a52af34fe985efe1c9bfbb5a06",
    "github15": "31b33472c40d42e0a90aa12f31c5f17c",
    "github16": "a84731691b2042dcaf203671ac44126e",
    "github4": "a7caa007814440618e14d45e42bd5450",
}

AIMLAPI_BASE_URL = "https://api.aimlapi.com/v1"

# Словник з часом вичерпання кожного ключа
exhausted_keys_time = {}

def is_key_available(key_name: str) -> bool:
    """Перевірити, чи доступний ключ (пройшла година після вичерпання)"""
    if key_name not in exhausted_keys_time:
        return True
    
    exhausted_time = exhausted_keys_time[key_name]
    current_time = datetime.now()
    
    # Якщо пройшла година - ключ знову доступний
    if current_time - exhausted_time >= timedelta(hours=1):
        del exhausted_keys_time[key_name]
        logging.info(f"🔄 Key {key_name} is available again after 1 hour cooldown")
        print(f"🔄 Ключ {key_name} знову доступний після охолодження")
        return True
    
    return False

def mark_key_exhausted(key_name: str):
    """Позначити ключ як вичерпаний"""
    exhausted_keys_time[key_name] = datetime.now()
    logging.warning(f"⚠️ Key {key_name} marked as exhausted until {datetime.now() + timedelta(hours=1)}")

async def ask_ai_async(prompt: str, model: str = "gpt-4o") -> str:
    """
    Асинхронний запит до AI з автоматичною ротацією ключів
    
    Args:
        prompt: Текст запиту
        model: Модель AI (за замовчуванням gpt-4o)
    
    Returns:
        Відповідь від AI
    """
    for key_name, api_key in api_keys.items():
        # Пропустити вичерпані ключі (якщо не пройшла година)
        if not is_key_available(key_name):
            time_left = timedelta(hours=1) - (datetime.now() - exhausted_keys_time[key_name])
            minutes_left = int(time_left.total_seconds() / 60)
            logging.debug(f"⏳ Key {key_name} still on cooldown ({minutes_left} minutes left)")
            continue
        
        try:
            client = AsyncOpenAI(
                base_url=AIMLAPI_BASE_URL,
                api_key=api_key,
            )
            response = await client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )
            logging.info(f"✓ Response from aimlapi (key: {key_name})")
            print(f"🤖 AI Provider: aimlapi (key: {key_name})")
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            error_str = str(e).lower()
            
            # Перевірка на вичерпання ліміту
            if "429" in error_str or "rate limit" in error_str or "quota" in error_str:
                mark_key_exhausted(key_name)
                logging.warning(f"⚠️ Key {key_name} rate limit exceeded, will retry in 1 hour")
                print(f"⚠️ Ліміт ключа {key_name} вичерпано, спробує через годину...")
                continue
            
            # Інші помилки - пробуємо наступний ключ
            logging.warning(f"⚠️ Key {key_name} error: {str(e)[:50]}, trying next key...")
            print(f"⚠️ Помилка з ключем {key_name}, пробую наступний...")
            continue
    
    # Якщо всі ключі вичерпані
    available_keys = sum(1 for k in api_keys.keys() if is_key_available(k))
    logging.error(f"❌ All API keys exhausted or failed (0/{len(api_keys)} available)")
    raise Exception(f"Всі API ключі тимчасово недоступні. Доступних ключів: {available_keys}/{len(api_keys)}. Спробуйте через годину.")

def ask_ai_sync(prompt: str, model: str = "gpt-4o") -> str:
    """
    Синхронний запит до AI з автоматичною ротацією ключів
    
    Args:
        prompt: Текст запиту
        model: Модель AI (за замовчуванням gpt-4o)
    
    Returns:
        Відповідь від AI
    """
    for key_name, api_key in api_keys.items():
        # Пропустити вичерпані ключі (якщо не пройшла година)
        if not is_key_available(key_name):
            time_left = timedelta(hours=1) - (datetime.now() - exhausted_keys_time[key_name])
            minutes_left = int(time_left.total_seconds() / 60)
            logging.debug(f"⏳ Key {key_name} still on cooldown ({minutes_left} minutes left)")
            continue
        
        try:
            client = OpenAI(
                base_url=AIMLAPI_BASE_URL,
                api_key=api_key,
            )
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )
            logging.info(f"✓ Response from aimlapi (key: {key_name})")
            print(f"🤖 AI Provider: aimlapi (key: {key_name})")
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            error_str = str(e).lower()
            
            # Перевірка на вичерпання ліміту
            if "429" in error_str or "rate limit" in error_str or "quota" in error_str:
                mark_key_exhausted(key_name)
                logging.warning(f"⚠️ Key {key_name} rate limit exceeded, will retry in 1 hour")
                print(f"⚠️ Ліміт ключа {key_name} вичерпано, спробує через годину...")
                continue
            
            # Інші помилки - пробуємо наступний ключ
            logging.warning(f"⚠️ Key {key_name} error: {str(e)[:50]}, trying next key...")
            print(f"⚠️ Помилка з ключем {key_name}, пробую наступний...")
            continue
    
    # Якщо всі ключі вичерпані
    available_keys = sum(1 for k in api_keys.keys() if is_key_available(k))
    logging.error(f"❌ All API keys exhausted or failed (0/{len(api_keys)} available)")
    raise Exception(f"Всі API ключі тимчасово недоступні. Доступних ключів: {available_keys}/{len(api_keys)}. Спробуйте через годину.")

def get_keys_status() -> dict:
    """Отримати статус всіх ключів"""
    status = {
        "total": len(api_keys),
        "available": 0,
        "exhausted": 0,
        "keys": {}
    }
    
    for key_name in api_keys.keys():
        if is_key_available(key_name):
            status["available"] += 1
            status["keys"][key_name] = "available"
        else:
            status["exhausted"] += 1
            time_left = timedelta(hours=1) - (datetime.now() - exhausted_keys_time[key_name])
            minutes_left = int(time_left.total_seconds() / 60)
            status["keys"][key_name] = f"exhausted ({minutes_left} min left)"
    
    return status

def reset_exhausted_keys():
    """Скинути список вичерпаних ключів вручну"""
    global exhausted_keys_time
    exhausted_keys_time.clear()
    logging.info("🔄 All exhausted keys have been manually reset")

