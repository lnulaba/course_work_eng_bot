import asyncio
import logging
from datetime import datetime
from aiogram import Bot

class ReminderScheduler:
    def __init__(self, bot: Bot, db):
        self.bot = bot
        self.db = db
        self.is_running = False
    
    async def send_daily_reminder(self, user_tg_id: int, user_name: str):
        """Відправити щоденне нагадування користувачу"""
        try:
            # Отримати прогрес користувача по tg_id
            user = await self.db.find_user_by_telegram_id(user_tg_id)
            if not user:
                return
            
            progress = await self.db.get_user_progress(user.user_id)
            if not progress:
                message_text = (
                    f"☀️ Доброго ранку, {user_name}! 👋\n\n"
                    f"🎓 Час пройти тестування для визначення вашого рівня англійської!\n\n"
                    f"Почніть навчання прямо зараз! 🚀"
                )
            else:
                limits = await self.db.get_user_limits(user.user_id)
                
                words_remaining = limits['words'] - progress.words_studied_today
                questions_remaining = limits['questions'] - progress.questions_answered_today
                
                if words_remaining <= 0 and questions_remaining <= 0:
                    message_text = (
                        f"🎉 Чудово, {user_name}!\n\n"
                        f"Ви вже виконали всі завдання на сьогодні!\n"
                        f"✅ Слів вивчено: {progress.words_studied_today}/{limits['words']}\n"
                        f"✅ Питань пройдено: {progress.questions_answered_today}/{limits['questions']}\n\n"
                        f"Повертайтесь завтра! 📚"
                    )
                else:
                    message_text = (
                        f"☀️ Доброго ранку, {user_name}! 👋\n\n"
                        f"📚 <b>Щоденне навчання чекає на вас!</b>\n\n"
                        f"📊 Ваш прогрес сьогодні:\n"
                    )
                    
                    if words_remaining > 0:
                        message_text += f"  📝 Слів залишилось: {words_remaining}/{limits['words']}\n"
                    else:
                        message_text += f"  ✅ Слова завершено: {progress.words_studied_today}/{limits['words']}\n"
                    
                    if questions_remaining > 0:
                        message_text += f"  ❓ Питань залишилось: {questions_remaining}/{limits['questions']}\n"
                    else:
                        message_text += f"  ✅ Питання завершено: {progress.questions_answered_today}/{limits['questions']}\n"
                    
                    message_text += (
                        f"\n🎯 Рівень: {progress.level_english}\n"
                        f"📈 Точність: {progress.accuracy:.1f}%\n\n"
                        f"Почніть навчання прямо зараз! 🚀"
                    )
            
            await self.bot.send_message(
                chat_id=user_tg_id,
                text=message_text,
                parse_mode="HTML"
            )
            
            logging.info(f"Reminder sent to user {user_tg_id}")
        
        except Exception as e:
            logging.error(f"Error sending reminder to {user_tg_id}: {e}")
    
    async def check_and_send_reminders(self):
        """Перевірити час і відправити нагадування"""
        try:
            current_time = datetime.now().strftime("%H:%M")
            
            # Отримати користувачів для нагадування
            users = await self.db.get_users_for_reminder(current_time)
            
            if users:
                logging.info(f"Found {len(users)} users for reminder at {current_time}")
                
                for user in users:
                    await self.send_daily_reminder(user.tg_id, user.first_name)
                    # Невелика затримка між відправками
                    await asyncio.sleep(0.5)
        
        except Exception as e:
            logging.error(f"Error in check_and_send_reminders: {e}")
    
    async def start(self):
        """Запустити планувальник"""
        self.is_running = True
        logging.info("Reminder scheduler started")
        
        while self.is_running:
            try:
                await self.check_and_send_reminders()
                
                # Перевіряти кожну хвилину
                await asyncio.sleep(60)
            
            except Exception as e:
                logging.error(f"Error in scheduler loop: {e}")
                await asyncio.sleep(60)
    
    def stop(self):
        """Зупинити планувальник"""
        self.is_running = False
        logging.info("Reminder scheduler stopped")
