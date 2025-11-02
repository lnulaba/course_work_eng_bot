"""
Контролери для English Learning Bot
Реалізація алгоритмів згідно з діаграмою активності
"""

import json
import asyncio
import random
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import openai
from aiogram import types

class UserController:
    """Контролер для управління користувачами"""
    
    def __init__(self, db):
        self.db = db
    
    async def handle_user_registration(self, message: types.Message) -> Tuple[bool, Dict]:
        """
        Алгоритм реєстрації користувача згідно з блок-схемою 1
        Повертає: (is_new_user, user_data)
        """
        telegram_id = message.from_user.id
        username = message.from_user.username
        full_name = f"{message.from_user.first_name or ''} {message.from_user.last_name or ''}".strip()
        
        # Перевірити чи користувач існує
        user = await self.db.get_user(telegram_id)
        
        if user:
            # Існуючий користувач
            if user['is_active']:
                return False, user
            else:
                # Заблокований акаунт
                return False, {'blocked': True}
        
        # Новий користувач - реєстрація
        registration_success = await self.db.register_user(telegram_id, username, full_name)
        
        if registration_success:
            # Отримати створеного користувача
            user = await self.db.get_user(telegram_id)
            return True, user
        else:
            return False, {'error': 'registration_failed'}

class WordLearningController:
    """Контролер для вивчення слів"""
    
    def __init__(self, db):
        self.db = db
        self.active_sessions = {}  # session_id -> session_data
    
    async def start_word_learning(self, user_id: int, level: str) -> Dict:
        """
        Алгоритм вивчення слів згідно з блок-схемою 3
        """
        # Завантажити слова за рівнем
        words = await self.db.get_words_by_level(level, 20)
        
        if not words:
            return {
                'success': False,
                'message': "Слова для вашого рівня не знайдені"
            }
        
        # Створити сесію вивчення
        session_id = await self.db.create_word_session(user_id)
        
        # Ініціалізувати сесію
        session_data = {
            'session_id': session_id,
            'user_id': user_id,
            'words': words,
            'current_word': 0,
            'known_words': 0,
            'unknown_words': 0,
            'start_time': datetime.now(),
            'unknown_word_ids': []
        }
        
        self.active_sessions[user_id] = session_data
        
        return {
            'success': True,
            'session_data': session_data,
            'current_word': words[0] if words else None,
            'progress': f"1/{len(words)}"
        }
    
    async def process_word_answer(self, user_id: int, knows_word: bool) -> Dict:
        """Обробити відповідь користувача на слово"""
        if user_id not in self.active_sessions:
            return {'error': 'no_active_session'}
        
        session = self.active_sessions[user_id]
        current_word_data = session['words'][session['current_word']]
        
        if knows_word:
            session['known_words'] += 1
            response = {
                'result': 'correct',
                'message': "Чудово! Продовжуємо",
                'feedback_type': 'positive'
            }
        else:
            session['unknown_words'] += 1
            session['unknown_word_ids'].append(current_word_data['word_id'])
            response = {
                'result': 'unknown',
                'message': "Запам'ятай це слово!",
                'word': current_word_data['word'],
                'translation': current_word_data['translation'],
                'audio_file': current_word_data['file_audio'],
                'feedback_type': 'learning'
            }
        
        # Перейти до наступного слова
        session['current_word'] += 1
        
        # Перевірити чи це останнє слово
        if session['current_word'] >= len(session['words']):
            return await self.complete_word_session(user_id)
        
        # Повернути наступне слово
        next_word = session['words'][session['current_word']]
        response.update({
            'next_word': next_word,
            'progress': f"{session['current_word'] + 1}/{len(session['words'])}"
        })
        
        return response
    
    async def complete_word_session(self, user_id: int) -> Dict:
        """Завершити сесію вивчення слів"""
        if user_id not in self.active_sessions:
            return {'error': 'no_active_session'}
        
        session = self.active_sessions[user_id]
        
        # Розрахувати статистику
        total_words = len(session['words'])
        known_words = session['known_words']
        unknown_words = session['unknown_words']
        accuracy = (known_words / total_words) * 100
        session_duration = datetime.now() - session['start_time']
        
        # Оновити базу даних
        await self.db.complete_word_session(
            session['session_id'], 
            known_words, 
            total_words
        )
        
        await self.db.update_user_progress(
            user_id, 
            known_words, 
            total_words
        )
        
        # Підготувати результати
        results = {
            'session_completed': True,
            'total_words': total_words,
            'known_words': known_words,
            'unknown_words': unknown_words,
            'accuracy': round(accuracy, 1),
            'session_duration': str(session_duration).split('.')[0],  # Без мікросекунд
            'has_unknown_words': unknown_words > 0
        }
        
        # Рекомендації на основі результатів
        if accuracy >= 80:
            results['performance_level'] = 'excellent'
            results['message'] = "🏆 Відмінний результат!"
            results['suggestion'] = "Можливо, готовий до наступного рівня?"
        elif accuracy < 50:
            results['performance_level'] = 'needs_practice'
            results['message'] = "📚 Потрібно більше практики"
            results['suggestion'] = "Рекомендуємо повторити незнайомі слова"
        else:
            results['performance_level'] = 'good'
            results['message'] = "👍 Хороший результат!"
            results['suggestion'] = "Продовжуй в тому ж дусі!"
        
        # Видалити сесію з пам'яті
        del self.active_sessions[user_id]
        
        return results

class ChatGPTController:
    """Контролер для роботи з ChatGPT API"""
    
    def __init__(self, db, api_key: Optional[str] = None):
        self.db = db
        if api_key:
            openai.api_key = api_key
        self.available = api_key is not None
    
    async def generate_test_questions(self, topic_name: str, level: str, count: int = 20) -> Dict:
        """
        Алгоритм генерації тестів через ChatGPT згідно з блок-схемою 2
        """
        if not self.available:
            return await self.fallback_to_database_questions(topic_name, level, count)
        
        try:
            # Формування промпту
            prompt = f"""
            Generate exactly {count} English test questions about {topic_name} 
            for {level} level students.
            
            Requirements:
            - Multiple choice format (A, B, C, D)
            - Questions in English
            - Appropriate difficulty for {level} level
            - Include grammar, vocabulary, and comprehension
            - Return as JSON array
            
            JSON format:
            [
              {{
                "question": "She ___ to work every day.",
                "options": {{
                  "A": "go",
                  "B": "goes", 
                  "C": "going",
                  "D": "gone"
                }},
                "correct_answer": "B",
                "explanation": "Present Simple 3rd person singular"
              }}
            ]
            """
            
            # Виклик ChatGPT API
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an English teacher creating tests"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=3000
            )
            
            # Парсинг відповіді
            content = response.choices[0].message.content
            questions = json.loads(content)
            
            if len(questions) == count:
                return {
                    'success': True,
                    'questions': questions,
                    'source': 'chatgpt'
                }
            else:
                return {
                    'success': False,
                    'error': 'insufficient_questions',
                    'received': len(questions),
                    'expected': count
                }
                
        except Exception as e:
            print(f"ChatGPT API Error: {e}")
            return await self.fallback_to_database_questions(topic_name, level, count)
    
    async def fallback_to_database_questions(self, topic_name: str, level: str, count: int) -> Dict:
        """Резервний варіант - використати готові питання з БД"""
        # Тут буде логіка отримання готових питань з бази даних
        # Поки що повертаємо помилку
        return {
            'success': False,
            'error': 'api_unavailable',
            'message': 'ChatGPT недоступний, готові питання не знайдені'
        }

class TestController:
    """Контролер для проведення тестів"""
    
    def __init__(self, db, chatgpt_controller):
        self.db = db
        self.chatgpt = chatgpt_controller
        self.active_tests = {}  # user_id -> test_data
    
    async def start_ai_test(self, user_id: int, topic_id: int, topic_name: str, level: str) -> Dict:
        """Початок тесту згенерованого AI"""
        # Генерувати питання через ChatGPT
        generation_result = await self.chatgpt.generate_test_questions(topic_name, level, 20)
        
        if not generation_result['success']:
            return generation_result
        
        questions = generation_result['questions']
        
        # Зберегти питання в БД
        question_ids = await self.db.save_ai_questions(topic_id, questions)
        
        # Створити сесію тестування
        session_id = await self.db.create_test_session(user_id, 'ai_generated_test')
        
        # Ініціалізувати тест
        test_data = {
            'session_id': session_id,
            'user_id': user_id,
            'questions': questions,
            'question_ids': question_ids,
            'current_question': 0,
            'correct_answers': 0,
            'start_time': datetime.now(),
            'answers': []
        }
        
        self.active_tests[user_id] = test_data
        
        return {
            'success': True,
            'test_started': True,
            'current_question': questions[0],
            'progress': f"1/{len(questions)}"
        }
    
    async def process_test_answer(self, user_id: int, answer: str) -> Dict:
        """Обробити відповідь на питання тесту"""
        if user_id not in self.active_tests:
            return {'error': 'no_active_test'}
        
        test = self.active_tests[user_id]
        current_q = test['questions'][test['current_question']]
        correct_answer = current_q['correct_answer']
        
        # Перевірити відповідь
        is_correct = answer.upper() == correct_answer.upper()
        
        if is_correct:
            test['correct_answers'] += 1
        
        # Зберегти відповідь
        test['answers'].append({
            'question_index': test['current_question'],
            'user_answer': answer,
            'correct_answer': correct_answer,
            'is_correct': is_correct
        })
        
        # Підготувати результат
        result = {
            'is_correct': is_correct,
            'correct_answer': correct_answer,
            'explanation': current_q.get('explanation', ''),
            'question_number': test['current_question'] + 1,
            'total_questions': len(test['questions'])
        }
        
        # Перейти до наступного питання
        test['current_question'] += 1
        
        # Перевірити чи тест завершено
        if test['current_question'] >= len(test['questions']):
            return await self.complete_test(user_id)
        
        # Повернути наступне питання
        next_question = test['questions'][test['current_question']]
        result.update({
            'next_question': next_question,
            'progress': f"{test['current_question'] + 1}/{len(test['questions'])}"
        })
        
        return result
    
    async def complete_test(self, user_id: int) -> Dict:
        """Завершити тест"""
        if user_id not in self.active_tests:
            return {'error': 'no_active_test'}
        
        test = self.active_tests[user_id]
        
        # Розрахувати результати
        total_questions = len(test['questions'])
        correct_answers = test['correct_answers']
        accuracy = (correct_answers / total_questions) * 100
        session_duration = datetime.now() - test['start_time']
        
        # Оновити базу даних
        await self.db.complete_test_session(
            test['session_id'],
            total_questions,
            correct_answers
        )
        
        await self.db.update_user_progress(
            user_id,
            correct_answers,
            total_questions
        )
        
        # Підготувати результати
        results = {
            'test_completed': True,
            'total_questions': total_questions,
            'correct_answers': correct_answers,
            'accuracy': round(accuracy, 1),
            'session_duration': str(session_duration).split('.')[0],
            'answers': test['answers']
        }
        
        # Аналіз результатів
        if accuracy >= 85:
            results['performance_level'] = 'excellent'
            results['message'] = "🏆 Відмінно! Ти справжній експерт!"
            results['suggestion'] = "Можливо, готовий до наступного рівня?"
            results['level_up_ready'] = True
        elif accuracy < 60:
            results['performance_level'] = 'needs_practice'
            results['message'] = "📚 Рекомендую більше практики з цієї теми"
            results['suggestion'] = "Повтори слабкі місця"
            results['level_up_ready'] = False
        else:
            results['performance_level'] = 'good'
            results['message'] = "👍 Хороший результат!"
            results['suggestion'] = "Продовжуй навчання"
            results['level_up_ready'] = False
        
        # Видалити тест з пам'яті
        del self.active_tests[user_id]
        
        return results

class StatisticsController:
    """Контролер для статистики та прогресу"""
    
    def __init__(self, db):
        self.db = db
    
    async def get_user_statistics(self, user_id: int) -> Dict:
        """
        Алгоритм відстеження прогресу згідно з блок-схемою 4
        """
        # Отримати основну статистику
        stats = await self.db.get_user_statistics(user_id)
        settings = await self.db.get_user_settings(user_id)
        
        if not stats:
            return {'error': 'user_not_found'}
        
        # Розрахувати додаткову статистику
        today_progress = await self.get_today_progress(user_id)
        weekly_activity = await self.get_weekly_activity(user_id)
        achievements = await self.calculate_achievements(stats)
        recommendations = await self.generate_recommendations(user_id, stats)
        
        return {
            'user_stats': stats,
            'today_progress': today_progress,
            'weekly_activity': weekly_activity,
            'achievements': achievements,
            'recommendations': recommendations,
            'daily_goal': settings.get('daily_goal', 50),
            'level_up_ready': await self.check_level_up_readiness(stats)
        }
    
    async def get_today_progress(self, user_id: int) -> Dict:
        """Отримати прогрес за сьогодні"""
        # Тут буде логіка отримання прогресу за сьогодні
        # Поки що заглушка
        return {
            'questions_today': 0,
            'sessions_today': 0,
            'goal_progress': 0
        }
    
    async def get_weekly_activity(self, user_id: int) -> List[Dict]:
        """Отримати активність за тиждень"""
        # Тут буде логіка отримання активності за тиждень
        return []
    
    async def calculate_achievements(self, stats: Dict) -> List[str]:
        """Розрахувати досягнення користувача"""
        achievements = []
        
        if stats.get('total_sessions', 0) >= 10:
            achievements.append("🎓 Активний учень")
        
        if stats.get('accuracy', 0) >= 90:
            achievements.append("🏆 Експерт")
        
        if stats.get('total_questions_answered', 0) >= 1000:
            achievements.append("📚 Тисяча питань")
        
        level = stats.get('level_english', 'A0')
        if level in ['B2', 'C1', 'C2']:
            achievements.append("🚀 Просунутий рівень")
        
        return achievements
    
    async def generate_recommendations(self, user_id: int, stats: Dict) -> List[str]:
        """Генерувати рекомендації для користувача"""
        recommendations = []
        
        accuracy = stats.get('accuracy', 0)
        
        if accuracy < 70:
            recommendations.append("📖 Рекомендую повторити основи граматики")
            recommendations.append("📚 Вивчити більше слів базового рівня")
        
        if stats.get('total_questions_answered', 0) < 100:
            recommendations.append("🎯 Спробуй пройти більше тестів для кращого результату")
        
        return recommendations
    
    async def check_level_up_readiness(self, stats: Dict) -> bool:
        """Перевірити готовність до підвищення рівня"""
        accuracy = stats.get('accuracy', 0)
        total_questions = stats.get('total_questions_answered', 0)
        
        return accuracy >= 80 and total_questions >= 100

class SettingsController:
    """Контролер для налаштувань"""
    
    def __init__(self, db):
        self.db = db
    
    async def get_user_settings(self, user_id: int) -> Dict:
        """Отримати налаштування користувача"""
        settings = await self.db.get_user_settings(user_id)
        user = await self.db.get_user(user_id)
        
        if user:
            settings['level_english'] = user.get('level_english', 'A0')
        
        return settings
    
    async def update_language(self, user_id: int, language: str) -> bool:
        """Оновити мову інтерфейсу"""
        if language in ['UA', 'EN', 'RU', 'PL']:
            await self.db.update_user_settings(user_id, preferred_language=language)
            return True
        return False
    
    async def update_daily_goal(self, user_id: int, goal: int) -> bool:
        """Оновити щоденну ціль"""
        if 10 <= goal <= 500:
            await self.db.update_user_settings(user_id, daily_goal=goal)
            return True
        return False
    
    async def update_notification_time(self, user_id: int, time_str: str) -> bool:
        """Оновити час нагадування"""
        try:
            # Валідація формату часу HH:MM
            time_parts = time_str.split(':')
            if len(time_parts) == 2:
                hour, minute = int(time_parts[0]), int(time_parts[1])
                if 0 <= hour <= 23 and 0 <= minute <= 59:
                    await self.db.update_user_settings(user_id, notification_time=time_str)
                    return True
        except ValueError:
            pass
        return False
    
    async def toggle_sound(self, user_id: int) -> bool:
        """Переключити звукові ефекти"""
        settings = await self.db.get_user_settings(user_id)
        current_sound = settings.get('sound_enabled', True)
        new_sound = not current_sound
        
        await self.db.update_user_settings(user_id, sound_enabled=new_sound)
        return new_sound
