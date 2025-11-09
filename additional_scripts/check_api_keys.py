import asyncio
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

async def check_key(name: str, key: str) -> tuple:
    """Перевірити один ключ"""
    print(f"Перевіряю {name}...", end=" ", flush=True)
    try:
        client = AsyncOpenAI(
            base_url="https://api.aimlapi.com/v1",
            api_key=key,
        )
        await asyncio.wait_for(
            client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=5
            ),
            timeout=10
        )
        print("✅ Працює")
        return (name, key, True, "Працює")
    except asyncio.TimeoutError:
        print("⏱️ Timeout")
        return (name, key, False, "Timeout")
    except Exception as e:
        error_str = str(e).lower()
        if "401" in error_str or "unauthorized" in error_str:
            print("❌ Невалідний ключ")
            return (name, key, False, "Невалідний ключ")
        elif "429" in error_str or "rate limit" in error_str:
            print("⚠️ Ліміт вичерпано")
            return (name, key, False, "Ліміт вичерпано")
        else:
            print(f"❌ Помилка")
            return (name, key, False, f"Помилка: {str(e)[:30]}")

async def main():
    print("=" * 60)
    print("Перевірка API ключів aimlapi")
    print("=" * 60)
    print()
    
    results = []
    for name, key in api_keys.items():
        result = await check_key(name, key)
        results.append(result)
    
    print()
    print("=" * 60)
    print("Детальний звіт:")
    print("=" * 60)
    
    working_keys = {}
    failed_keys = {}
    
    for name, key, is_working, status in results:
        status_icon = "✅" if is_working else "❌"
        print(f"{status_icon} {name:12} | {status}")
        
        if is_working:
            working_keys[name] = key
        else:
            failed_keys[name] = status
    
    print()
    print("=" * 60)
    print(f"Підсумок: {len(working_keys)} працюють / {len(failed_keys)} не працюють з {len(api_keys)}")
    print("=" * 60)
    print()
    
    if working_keys:
        print("Робочі API ключі:")
        print("-" * 60)
        print("api_keys = {")
        for i, (name, key) in enumerate(working_keys.items()):
            comma = "," if i < len(working_keys) - 1 else ""
            print(f'    "{name}": "{key}"{comma}')
        print("}")
        print()
    else:
        print("⚠️  УВАГА: Жоден ключ не працює!")
    
    if failed_keys:
        print("\nНеробочі ключі:")
        print("-" * 60)
        for name, reason in failed_keys.items():
            print(f"  ❌ {name:12} - {reason}")

if __name__ == "__main__":
    asyncio.run(main())
