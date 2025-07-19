import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import TelegramError, BadRequest, Forbidden
from loguru import logger

from config import settings
from models.report import WeeklyReport
from models.department import Employee

class TelegramService:
    """Сервис для работы с Telegram API"""
    
    def __init__(self, bot: Bot):
        self.bot = bot
        self.group_chat_id = settings.group_chat_id
        self.thread_id = settings.thread_id
    
    async def send_message_safe(self, chat_id: int, text: str, 
                               reply_markup: Optional[InlineKeyboardMarkup] = None,
                               parse_mode: str = 'HTML') -> bool:
        """Безопасная отправка сообщения с обработкой ошибок"""
        try:
            await self.bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
            return True
        except Forbidden:
            logger.warning(f"Пользователь {chat_id} заблокировал бота")
            return False
        except BadRequest as e:
            logger.error(f"Ошибка отправки сообщения пользователю {chat_id}: {e}")
            return False
        except TelegramError as e:
            logger.error(f"Telegram ошибка при отправке сообщения {chat_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Неожиданная ошибка при отправке сообщения {chat_id}: {e}")
            return False
    
    async def send_report_to_group(self, report: WeeklyReport) -> bool:
        """Отправка отчета в групповой чат"""
        try:
            # Форматируем отчет для отправки
            formatted_report = self._format_report_for_group(report)
            
            # Отправляем в группу
            if self.thread_id:
                # Если указан thread_id, отправляем в тред
                await self.bot.send_message(
                    chat_id=self.group_chat_id,
                    text=formatted_report,
                    message_thread_id=self.thread_id,
                    parse_mode='HTML'
                )
            else:
                # Обычное сообщение в группу
                await self.bot.send_message(
                    chat_id=self.group_chat_id,
                    text=formatted_report,
                    parse_mode='HTML'
                )
            
            logger.info(f"Отчет пользователя {report.user_id} отправлен в группу")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка отправки отчета в группу: {e}")
            return False
    
    def _format_report_for_group(self, report: WeeklyReport) -> str:
        """Форматирование отчета для группового чата"""
        # Эмодзи для украшения
        status_emoji = {
            'submitted': '📋',
            'processed': '✅',
            'draft': '📝'
        }
        
        emoji = status_emoji.get(report.status, '📄')
        
        formatted = f"""{emoji} <b>Еженедельный отчет</b>

👤 <b>Сотрудник:</b> {report.full_name}
📅 <b>Период:</b> {report.week_start.strftime('%d.%m.%Y')} - {report.week_end.strftime('%d.%m.%Y')}
🏢 <b>Отдел:</b> {report.department or 'Не указан'}
💼 <b>Должность:</b> {report.position or 'Не указана'}

📋 <b>Выполненные задачи:</b>
{self._format_text_block(report.completed_tasks)}

🎯 <b>Достижения:</b>
{self._format_text_block(report.achievements)}

⚠️ <b>Проблемы:</b>
{self._format_text_block(report.problems)}

📈 <b>Планы на следующую неделю:</b>
{self._format_text_block(report.next_week_plans)}
"""
        
        # Добавляем ИИ анализ если есть
        if hasattr(report, 'ai_summary') and report.ai_summary:
            formatted += f"\n🤖 <b>ИИ Анализ:</b>\n{self._format_text_block(report.ai_summary)}"
        
        # Добавляем время отправки
        submit_time = report.submitted_at or report.created_at
        if submit_time:
            formatted += f"\n⏰ <b>Отправлено:</b> {submit_time.strftime('%d.%m.%Y %H:%M')}"
        else:
            from datetime import datetime
            current_time = datetime.now()
            formatted += f"\n⏰ <b>Отправлено:</b> {current_time.strftime('%d.%m.%Y %H:%M')}"
        
        return formatted
    
    def _format_text_block(self, text: str, max_length: int = 500) -> str:
        """Форматирование текстового блока с ограничением длины"""
        if not text or text.strip() == "":
            return "<i>Не указано</i>"
        
        # Обрезаем текст если он слишком длинный
        if len(text) > max_length:
            text = text[:max_length] + "..."
        
        # Экранируем HTML символы
        text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        
        return text
    
    async def send_reminder_to_user(self, user_id: int, user_name: str) -> bool:
        """Отправка напоминания пользователю о необходимости сдать отчет"""
        reminder_text = f"""🔔 <b>Напоминание о еженедельном отчете</b>

Привет, {user_name}!

Не забудь сдать свой еженедельный отчет до {settings.report_deadline}.

Для создания отчета используй команду /report

📋 В отчете укажи:
• Выполненные задачи
• Достижения
• Возникшие проблемы
• Планы на следующую неделю

Спасибо за своевременность! 🙏"""
        
        return await self.send_message_safe(user_id, reminder_text)
    
    async def send_bulk_reminders(self, users: List[Employee]) -> Dict[str, int]:
        """Массовая отправка напоминаний"""
        results = {'sent': 0, 'failed': 0}
        
        for user in users:
            success = await self.send_reminder_to_user(user.user_id, user.full_name)
            if success:
                results['sent'] += 1
            else:
                results['failed'] += 1
            
            # Небольшая задержка между отправками
            await asyncio.sleep(0.5)
        
        logger.info(f"Отправлено напоминаний: {results['sent']}, неудачных: {results['failed']}")
        return results
    
    async def send_weekly_summary_to_admins(self, summary: str, admin_ids: List[int]) -> int:
        """Отправка еженедельной сводки администраторам"""
        summary_text = f"""📊 <b>Еженедельная сводка отчетов</b>

{summary}

📅 <b>Сформировано:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}"""
        
        sent_count = 0
        for admin_id in admin_ids:
            if await self.send_message_safe(admin_id, summary_text):
                sent_count += 1
            await asyncio.sleep(0.3)
        
        return sent_count
    
    async def send_report_confirmation(self, user_id: int, report: WeeklyReport) -> bool:
        """Отправка подтверждения о получении отчета"""
        confirmation_text = f"""✅ <b>Отчет принят!</b>

Спасибо, {report.full_name}!

Твой еженедельный отчет за период {report.week_start.strftime('%d.%m.%Y')} - {report.week_end.strftime('%d.%m.%Y')} успешно получен и будет обработан.

📋 <b>Краткая информация:</b>
• Задачи: {len(report.completed_tasks.split('\n')) if report.completed_tasks else 0} пунктов
• Достижения: {'✓' if report.achievements.strip() else '✗'}
• Проблемы: {'✓' if report.problems.strip() else '✗'}
• Планы: {'✓' if report.next_week_plans.strip() else '✗'}

🤖 Отчет будет автоматически проанализирован и отправлен руководству.

Удачной рабочей недели! 🚀"""
        
        return await self.send_message_safe(user_id, confirmation_text)
    
    async def send_error_notification(self, user_id: int, error_message: str) -> bool:
        """Отправка уведомления об ошибке"""
        error_text = f"""❌ <b>Произошла ошибка</b>

{error_message}

Пожалуйста, попробуй еще раз или обратись к администратору.

Для получения помощи используй команду /help"""
        
        return await self.send_message_safe(user_id, error_text)
    
    async def send_admin_notification(self, admin_ids: List[int], message: str) -> int:
        """Отправка уведомления администраторам"""
        admin_text = f"""🔧 <b>Уведомление администратора</b>

{message}

⏰ {datetime.now().strftime('%d.%m.%Y %H:%M')}"""
        
        sent_count = 0
        for admin_id in admin_ids:
            if await self.send_message_safe(admin_id, admin_text):
                sent_count += 1
            await asyncio.sleep(0.2)
        
        return sent_count
    
    async def get_chat_member_count(self, chat_id: int) -> Optional[int]:
        """Получение количества участников чата"""
        try:
            member_count = await self.bot.get_chat_member_count(chat_id)
            return member_count
        except Exception as e:
            logger.error(f"Ошибка получения количества участников чата {chat_id}: {e}")
            return None
    
    async def check_bot_permissions(self, chat_id: int) -> Dict[str, bool]:
        """Проверка прав бота в чате"""
        try:
            bot_member = await self.bot.get_chat_member(chat_id, self.bot.id)
            
            permissions = {
                'can_send_messages': getattr(bot_member, 'can_send_messages', False),
                'can_send_media_messages': getattr(bot_member, 'can_send_media_messages', False),
                'can_pin_messages': getattr(bot_member, 'can_pin_messages', False),
                'can_delete_messages': getattr(bot_member, 'can_delete_messages', False),
                'is_admin': bot_member.status in ['administrator', 'creator']
            }
            
            return permissions
            
        except Exception as e:
            logger.error(f"Ошибка проверки прав бота в чате {chat_id}: {e}")
            return {}
    
    def create_report_keyboard(self) -> InlineKeyboardMarkup:
        """Создание клавиатуры для работы с отчетами"""
        keyboard = [
            [InlineKeyboardButton("📝 Создать отчет", callback_data="create_report")],
            [InlineKeyboardButton("📊 Мой статус", callback_data="my_status")],
            [InlineKeyboardButton("❓ Помощь", callback_data="help")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def create_admin_keyboard(self) -> InlineKeyboardMarkup:
        """Создание клавиатуры для администраторов"""
        keyboard = [
            [InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")],
            [InlineKeyboardButton("📋 Все отчеты", callback_data="admin_reports")],
            [InlineKeyboardButton("🔔 Напоминания", callback_data="admin_reminders")],
            [InlineKeyboardButton("👥 Пользователи", callback_data="admin_users")],
            [InlineKeyboardButton("📤 Экспорт", callback_data="admin_export")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    async def send_typing_action(self, chat_id: int) -> bool:
        """Отправка действия 'печатает'"""
        try:
            await self.bot.send_chat_action(chat_id, 'typing')
            return True
        except Exception as e:
            logger.debug(f"Не удалось отправить typing action для {chat_id}: {e}")
            return False
    
    async def delete_message_safe(self, chat_id: int, message_id: int) -> bool:
        """Безопасное удаление сообщения"""
        try:
            await self.bot.delete_message(chat_id, message_id)
            return True
        except Exception as e:
            logger.debug(f"Не удалось удалить сообщение {message_id} в чате {chat_id}: {e}")
            return False
    
    async def edit_message_safe(self, chat_id: int, message_id: int, text: str,
                               reply_markup: Optional[InlineKeyboardMarkup] = None) -> bool:
        """Безопасное редактирование сообщения"""
        try:
            await self.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            return True
        except Exception as e:
            logger.debug(f"Не удалось отредактировать сообщение {message_id} в чате {chat_id}: {e}")
            return False