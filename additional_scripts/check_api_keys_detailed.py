import asyncio
import json
from openai import AsyncOpenAI

api_keys = {
    "my": "6bd60986ac8544d08311d5f0a1736393",
    "github1": "f0af93f61ad44ceeb26a4aca6be8e75c",
    "github2": "aa4c891e0d7d4491a919859bbb33b4b4",
    "github3": "74b0c0abd2294719ba29967c27bde367",
    "github4": "a7caa007814440618e14d45e42bd5450",
    "github5": "0710951b319a4cd79e155a8e40413658",
    "github6": "7ae3a9a75e99458cb771a2e52134e8cb",
    "github7": "09c8c09c82764e73a906a8f353115bec",
    "github8": "8df72ab4814643ca897ee213f4d2b054",
    "github9": "afd78080d3314927bc2d9ffc44ae6215",
    "github10": "05eaba6dd95047d4bb17657d26f71cac",
    "github11": "a4e0c569dfe04440a9dc81720921d809",
    "github12": "8b10e507d0ae4eeb9c591d3da3273e22",
    "github13": "748552329098444c9830a0b60ce48373",
    "github14": "417c93a52af34fe985efe1c9bfbb5a06",
    "github15": "31b33472c40d42e0a90aa12f31c5f17c",
    "github16": "a84731691b2042dcaf203671ac44126e"
}

async def check_key_detailed(name: str, key: str) -> dict:
    """Детально перевірити один ключ"""
    print(f"\n{'='*60}")
    print(f"Перевірка ключа: {name}")
    print(f"{'='*60}")
    
    try:
        client = AsyncOpenAI(
            base_url="https://api.aimlapi.com/v1",
            api_key=key,
        )
        
        response = await asyncio.wait_for(
            client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": "Say OK"}],
                max_tokens=5
            ),
            timeout=15
        )
        
        # Успішна відповідь
        result = {
            "name": name,
            "key": key,
            "status": "✅ Працює",
            "working": True,
            "response": {
                "id": response.id,
                "model": response.model,
                "content": response.choices[0].message.content,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else None,
                    "completion_tokens": response.usage.completion_tokens if response.usage else None,
                    "total_tokens": response.usage.total_tokens if response.usage else None
                }
            }
        }
        
        print(f"✅ Статус: Працює")
        print(f"📝 Відповідь: {response.choices[0].message.content}")
        print(f"📊 Токени: {response.usage.total_tokens if response.usage else 'N/A'}")
        
        return result
        
    except asyncio.TimeoutError:
        result = {
            "name": name,
            "key": key,
            "status": "⏱️ Timeout",
            "working": False,
            "error": "Request timeout after 15 seconds"
        }
        print(f"⏱️ Статус: Timeout")
        return result
        
    except Exception as e:
        error_str = str(e)
        error_dict = {}
        
        # Спробувати парсити JSON помилку
        try:
            # Шукаємо JSON у тексті помилки
            if '{' in error_str and '}' in error_str:
                json_start = error_str.find('{')
                json_end = error_str.rfind('}') + 1
                json_str = error_str[json_start:json_end]
                error_dict = json.loads(json_str)
        except:
            pass
        
        # Визначити тип помилки
        if "401" in error_str or "unauthorized" in error_str.lower():
            status = "❌ Невалідний ключ"
            error_type = "Unauthorized"
        elif "429" in error_str or "rate limit" in error_str.lower() or "quota" in error_str.lower():
            status = "⚠️ Ліміт вичерпано"
            error_type = "Rate Limit / Quota Exceeded"
        elif "403" in error_str or "forbidden" in error_str.lower():
            status = "🚫 Доступ заборонено"
            error_type = "Forbidden"
        else:
            status = "❌ Помилка"
            error_type = "Unknown Error"
        
        result = {
            "name": name,
            "key": key,
            "status": status,
            "working": False,
            "error_type": error_type,
            "error_message": error_str,
            "error_details": error_dict if error_dict else None
        }
        
        print(f"{status}")
        print(f"🔍 Тип помилки: {error_type}")
        print(f"📄 Повідомлення: {error_str[:400]}")
        
        if error_dict:
            print(f"📋 Деталі JSON:")
            print(json.dumps(error_dict, indent=2, ensure_ascii=False))
        
        return result

async def main():
    print("=" * 60)
    print("ДЕТАЛЬНА ПЕРЕВІРКА API КЛЮЧІВ AIMLAPI")
    print("=" * 60)
    
    all_results = []
    
    for name, key in api_keys.items():
        result = await check_key_detailed(name, key)
        all_results.append(result)
        await asyncio.sleep(0.5)  # Невелика затримка між запитами
    
    # Підсумок
    print("\n" + "=" * 60)
    print("ПІДСУМКОВИЙ ЗВІТ")
    print("=" * 60)
    
    working_keys = {}
    rate_limited_keys = []
    invalid_keys = []
    other_errors = []
    
    for result in all_results:
        if result["working"]:
            working_keys[result["name"]] = result["key"]
        elif "Ліміт" in result["status"]:
            rate_limited_keys.append(result["name"])
        elif "Невалідний" in result["status"]:
            invalid_keys.append(result["name"])
        else:
            other_errors.append(result["name"])
    
    print(f"\n📊 Статистика:")
    print(f"  ✅ Працюють: {len(working_keys)}")
    print(f"  ⚠️ Ліміт вичерпано: {len(rate_limited_keys)}")
    print(f"  ❌ Невалідні: {len(invalid_keys)}")
    print(f"  ❓ Інші помилки: {len(other_errors)}")
    print(f"  📋 Всього: {len(api_keys)}")
    
    if working_keys:
        print(f"\n✅ РОБОЧІ КЛЮЧІ ({len(working_keys)}):")
        print("-" * 60)
        print("api_keys = {")
        for i, (name, key) in enumerate(working_keys.items()):
            comma = "," if i < len(working_keys) - 1 else ""
            print(f'    "{name}": "{key}"{comma}')
        print("}")
    
    if rate_limited_keys:
        print(f"\n⚠️ КЛЮЧІ З ВИЧЕРПАНИМ ЛІМІТОМ ({len(rate_limited_keys)}):")
        print("-" * 60)
        for name in rate_limited_keys:
            print(f"  • {name}")
    
    if invalid_keys:
        print(f"\n❌ НЕВАЛІДНІ КЛЮЧІ ({len(invalid_keys)}):")
        print("-" * 60)
        for name in invalid_keys:
            print(f"  • {name}")
    
    if other_errors:
        print(f"\n❓ ІНШІ ПОМИЛКИ ({len(other_errors)}):")
        print("-" * 60)
        for name in other_errors:
            print(f"  • {name}")
    
    # Зберегти детальний звіт у JSON
    with open("api_keys_detailed_report.json", "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Детальний звіт збережено у: api_keys_detailed_report.json")

if __name__ == "__main__":
    asyncio.run(main())
