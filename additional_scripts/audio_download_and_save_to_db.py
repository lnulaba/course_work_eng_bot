import asyncio
import aiohttp
import os
from pathlib import Path
import sys

# Add parent directory to path to import db module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import Connection, DB
from sqlalchemy import select, update
from models import Words


async def fetch_word_data(session: aiohttp.ClientSession, word: str, max_retries: int = 3) -> dict:
    """Fetch word data from dictionary API with retry logic"""
    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
    
    for attempt in range(max_retries):
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    return data[0] if isinstance(data, list) and len(data) > 0 else None
                elif response.status == 404:
                    print(f"✗ Word '{word}' not found in API", 404)
                    return None
                else:
                    print(f"✗ API error for '{word}': HTTP {response.status}")
                    if attempt < max_retries - 1:
                        print(f"  Waiting 5 seconds before retry ({attempt + 1}/{max_retries})...")
                        await asyncio.sleep(5)
                    else:
                        print(f"  Failed after {max_retries} attempts")
                        return None
        except Exception as e:
            print(f"✗ Error fetching data for '{word}': {e}")
            if attempt < max_retries - 1:
                print(f"  Waiting 5 seconds before retry ({attempt + 1}/{max_retries})...")
                await asyncio.sleep(5)
            else:
                print(f"  Failed after {max_retries} attempts")
                return None
    
    return None


async def download_audio(session: aiohttp.ClientSession, url: str, word: str, audio_folder: Path, max_retries: int = 3) -> str:
    """Download audio file and return local path with retry logic"""
    
    for attempt in range(max_retries):
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    # Create safe filename
                    safe_word = "".join(c for c in word if c.isalnum() or c in (' ', '-', '_')).strip()
                    filename = f"{safe_word}.mp3"
                    filepath = audio_folder / filename
                    
                    # Save audio file
                    with open(filepath, 'wb') as f:
                        f.write(await response.read())
                    
                    print(f"✓ Downloaded audio for '{word}'")
                    relative_path = filename
                    return relative_path
                else:
                    print(f"✗ Failed to download audio for '{word}': HTTP {response.status}")
                    if attempt < max_retries - 1:
                        print(f"  Waiting 10 seconds before retry ({attempt + 1}/{max_retries})...")
                        await asyncio.sleep(10)
                    else:
                        print(f"  Failed after {max_retries} attempts")
                        return None
        except Exception as e:
            print(f"✗ Error downloading audio for '{word}': {e}")
            if attempt < max_retries - 1:
                print(f"  Waiting 10 seconds before retry ({attempt + 1}/{max_retries})...")
                await asyncio.sleep(10)
            else:
                print(f"  Failed after {max_retries} attempts")
                return None
    
    return None


async def process_word(session: aiohttp.ClientSession, db: DB, word_obj, audio_folder: Path):
    """Process single word: fetch data, download audio, update database"""
    word = word_obj.word
    word_id = word_obj.word_id
    
    print(f"\nProcessing: {word}")
    
    # Fetch word data from API
    word_data = await fetch_word_data(session, word)
    if not word_data:
        return
    
    # Find UK audio URL
    uk_audio_url = None
    phonetics = word_data.get('phonetics', [])
    
    for phonetic in phonetics:
        audio_url = phonetic.get('audio', '')
        # Check if this is UK pronunciation
        if 'uk' in audio_url.lower() and audio_url:
            uk_audio_url = audio_url
            break
    
    # If no UK audio found, try any audio
    if not uk_audio_url:
        for phonetic in phonetics:
            audio_url = phonetic.get('audio', '')
            if audio_url:
                uk_audio_url = audio_url
                break
    
    if not uk_audio_url:
        print(f"  No audio found for '{word}'")
        return
    
    # Download audio
    audio_path = await download_audio(session, uk_audio_url, word, audio_folder)
    
    if audio_path:
        # Update database with audio path
        success = await db.update_word_audio_path(word_id, audio_path)
        if success:
            print(f"  Updated database for '{word}'")


async def main():
    """Main function"""
    # Initialize database connection
    conn = Connection()
    await conn.connect()
    db = DB(conn.session_maker)
    
    # Create audio folder if it doesn't exist
    audio_folder = Path(__file__).parent.parent / "files" / "audios"
    audio_folder.mkdir(parents=True, exist_ok=True)
    print(f"Audio folder: {audio_folder}")
    
    # Fetch words without audio from database
    all_words = await db.get_words_without_audio()
    
    print(f"\nTotal words to process: {len(all_words)}")
    
    # Process words with rate limiting
    async with aiohttp.ClientSession() as session:
        for i, word_obj in enumerate(all_words, 1):
            print(f"\n[{i}/{len(all_words)}]", end=" ")
            await process_word(session, db, word_obj, audio_folder)
            
            # Rate limiting - wait 0.5 seconds between requests
            if i < len(all_words):
                await asyncio.sleep(0.3)
    
    print("\n\n✓ Processing complete!")


if __name__ == "__main__":
    asyncio.run(main())
