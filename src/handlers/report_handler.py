import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, 
    ConversationHandler, 
    CommandHandler, 
    MessageHandler, 
    CallbackQueryHandler,
    filters
)
from loguru import logger

from config import settings, MESSAGES
from services.report_processor import ReportProcessor
from services.ollama_service import OllamaService
from services.telegram_service import TelegramService
from services import TaskManager, TaskStatus
from models.report import WeeklyReport
from utils.date_utils import get_current_week_range, is_deadline_passed
from .states import ReportStates, get_report_confirmation_keyboard, get_cancel_keyboard
from database import DatabaseManager

class ReportHandler:
    """Обработчик команд для создания и отправки отчетов"""
    
    def __init__(self, report_processor: ReportProcessor, ollama_service: OllamaService, telegram_service: TelegramService, task_manager: TaskManager, db_manager: DatabaseManager):
        self.report_processor = report_processor
        self.ollama_service = ollama_service
        self.telegram_service = telegram_service
        self.task_manager = task_manager
        self.db_manager = db_manager
        self.user_reports: Dict[int, WeeklyReport] = {}
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /start"""
        user = update.effective_user
        logger.info(f"Пользователь {user.id} ({user.username}) запустил бота")
        
        # Импортируем здесь, чтобы избежать циклических импортов
        from .states import get_main_menu_keyboard
        
        is_admin = user.id in settings.get_admin_ids()
        
        welcome_text = (
            f"🏠 <b>Главное меню</b>\n\n"
            f"{MESSAGES['welcome']}\n\n"
            f"Выберите действие:"
        )
        
        await update.message.reply_text(
            text=welcome_text,
            reply_markup=get_main_menu_keyboard(is_admin),
            parse_mode='HTML'
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Показать справку по командам."""
        user = update.effective_user
        is_admin = user.id in settings.get_admin_ids()
        
        help_text = MESSAGES["help"]
        if not is_admin:
            # Убираем админские команды для обычных пользователей
            lines = help_text.split('\n')
            help_text = '\n'.join([line for line in lines if not line.startswith('/admin') and not line.startswith('/stats')])
        
        # Проверяем, вызван ли из callback query (из меню)
        if update.callback_query:
            from .states import get_back_to_main_keyboard
            await update.callback_query.message.reply_text(
                help_text,
                reply_markup=get_back_to_main_keyboard(),
                parse_mode='HTML'
            )
        else:
            await update.message.reply_text(
                help_text,
                parse_mode='HTML'
            )
    
    async def report_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Начать процесс создания отчета"""
        return await self.start_report_process(update, context)
    
    async def start_report_process(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Начать процесс создания отчета (может вызываться из меню или команды)"""
        user = update.effective_user
        logger.info(f"Пользователь {user.id} начал создание отчета")
        
        # Проверяем дедлайн
        if is_deadline_passed():
            message_text = (
                "⏰ Дедлайн для отправки отчетов уже прошел.\n\n"
                "Обратитесь к администратору для отправки отчета."
            )
            
            if update.callback_query:
                await update.callback_query.edit_message_text(
                    text=message_text,
                    reply_markup=get_cancel_keyboard()
                )
            else:
                await update.message.reply_text(
                    text=message_text,
                    reply_markup=get_cancel_keyboard()
                )
            return ConversationHandler.END
        
        # Получаем текущий период отчета
        start_date, end_date = get_current_week_range()
        
        # Проверяем, не отправлял ли пользователь уже отчет за этот период
        existing_report = self.report_processor.get_user_report_for_week(
            user.id, start_date
        )
        
        if existing_report:
            message_text = (
                f"📋 Вы уже отправили отчет за период {start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}.\n\n"
                "Используйте кнопку 'Статус отчета' для просмотра."
            )
            
            if update.callback_query:
                await update.callback_query.edit_message_text(
                    text=message_text,
                    reply_markup=get_cancel_keyboard()
                )
            else:
                await update.message.reply_text(
                    text=message_text,
                    reply_markup=get_cancel_keyboard()
                )
            return ConversationHandler.END
        
        # Создаем новый отчет
        report = WeeklyReport(
            user_id=user.id,
            username=user.username or "",
            full_name=user.full_name or f"{user.first_name} {user.last_name or ''}".strip(),
            week_start=start_date,
            week_end=end_date,
            completed_tasks="",  # Будет заполнено позже
            next_week_plans=""   # Будет заполнено позже
        )
        
        self.user_reports[user.id] = report
        
        from .states import get_departments_keyboard
        
        message_text = (
            f"📋 <b>Создание отчета</b>\n\n"
            f"Период: {start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}\n\n"
            f"Выберите ваш отдел:"
        )
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text=message_text,
                reply_markup=get_departments_keyboard(),
                parse_mode='HTML'
            )
        else:
            await update.message.reply_text(
                text=message_text,
                reply_markup=get_departments_keyboard(),
                parse_mode='HTML'
            )
        
        return ReportStates.WAITING_DEPARTMENT
    
    async def receive_department(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Получение отдела сотрудника через callback query"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        
        if user_id not in self.user_reports:
            await query.edit_message_text("Ошибка: отчет не найден. Начните заново с /report")
            return ConversationHandler.END
        
        # Извлекаем название отдела из callback_data
        if query.data.startswith("dept_"):
            department_name = query.data[5:]  # Убираем префикс "dept_"
            self.user_reports[user_id].department = department_name
            logger.info(f"Пользователь {user_id} выбрал отдел: {department_name}")
            
            await query.edit_message_text(
                f"✅ Отдел: <b>{department_name}</b>\n\n"
                "Теперь опишите выполненные задачи за неделю:\n\n"
                "Перечислите основные задачи, которые вы выполнили.",
                reply_markup=get_cancel_keyboard(),
                parse_mode='HTML'
            )
            
            return ReportStates.WAITING_TASKS
        else:
            await query.edit_message_text("Ошибка: неверный выбор отдела")
            return ConversationHandler.END
    
    async def receive_tasks(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Получение выполненных задач"""
        user_id = update.effective_user.id
        tasks_text = update.message.text
        
        if user_id not in self.user_reports:
            await update.message.reply_text("Ошибка: отчет не найден. Начните заново с /report")
            return ConversationHandler.END
        
        self.user_reports[user_id].completed_tasks = tasks_text
        logger.info(f"Пользователь {user_id} добавил задачи в отчет")
        
        await update.message.reply_text(
            "Отлично! Теперь расскажите о ваших достижениях и успехах за неделю:\n\n"
            "(Если достижений не было, напишите 'нет' или 'отсутствуют')",
            reply_markup=get_cancel_keyboard()
        )
        
        return ReportStates.WAITING_ACHIEVEMENTS
    
    async def receive_achievements(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Получение достижений"""
        user_id = update.effective_user.id
        achievements_text = update.message.text
        
        if user_id not in self.user_reports:
            await update.message.reply_text("Ошибка: отчет не найден. Начните заново с /report")
            return ConversationHandler.END
        
        self.user_reports[user_id].achievements = achievements_text
        logger.info(f"Пользователь {user_id} добавил достижения в отчет")
        
        await update.message.reply_text(
            "Хорошо! Теперь опишите проблемы или трудности, с которыми вы столкнулись:\n\n"
            "(Если проблем не было, напишите 'нет' или 'отсутствуют')",
            reply_markup=get_cancel_keyboard()
        )
        
        return ReportStates.WAITING_PROBLEMS
    
    async def receive_problems(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Получение проблем"""
        user_id = update.effective_user.id
        problems_text = update.message.text
        
        if user_id not in self.user_reports:
            await update.message.reply_text("Ошибка: отчет не найден. Начните заново с /report")
            return ConversationHandler.END
        
        self.user_reports[user_id].problems = problems_text
        logger.info(f"Пользователь {user_id} добавил проблемы в отчет")
        
        await update.message.reply_text(
            "Почти готово! Расскажите о ваших планах на следующую неделю:",
            reply_markup=get_cancel_keyboard()
        )
        
        return ReportStates.WAITING_PLANS
    
    async def receive_plans(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Получение планов"""
        user_id = update.effective_user.id
        plans_text = update.message.text
        
        if user_id not in self.user_reports:
            await update.message.reply_text("Ошибка: отчет не найден. Начните заново с /report")
            return ConversationHandler.END
        
        self.user_reports[user_id].next_week_plans = plans_text
        logger.info(f"Пользователь {user_id} добавил планы в отчет")
        
        # Показываем предварительный просмотр отчета
        report = self.user_reports[user_id]
        preview = self._format_report_preview(report)
        
        await update.message.reply_text(
            f"📋 <b>Предварительный просмотр отчета:</b>\n\n{preview}\n\n"
            "Проверьте информацию и подтвердите отправку:",
            reply_markup=get_report_confirmation_keyboard(),
            parse_mode='HTML'
        )
        
        return ReportStates.WAITING_CONFIRMATION
    
    async def confirm_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Подтверждение и отправка отчета"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        
        if query.data == "confirm_report":
            if user_id not in self.user_reports:
                await query.edit_message_text("Ошибка: отчет не найден. Начните заново с /report")
                return ConversationHandler.END
            
            report = self.user_reports[user_id]
            
            # Проверяем, есть ли уже активная задача для пользователя
            existing_task = self.task_manager.get_user_task(user_id)
            if existing_task and existing_task.status in [TaskStatus.PENDING, TaskStatus.RUNNING]:
                await query.edit_message_text("⚠️ У вас уже есть обрабатывающийся отчет. Пожалуйста, дождитесь завершения.")
                return ConversationHandler.END
            
            # Создаем callback для обновления прогресса
            async def progress_callback(task_info):
                try:
                    if task_info.status == TaskStatus.COMPLETED:
                        if task_info.result:
                            await query.edit_message_text(MESSAGES["report_created"])
                            logger.info(f"Отчет пользователя {user_id} успешно отправлен")
                        else:
                            await query.edit_message_text(MESSAGES["error_general"])
                            logger.error(f"Ошибка отправки отчета пользователя {user_id}")
                    elif task_info.status == TaskStatus.FAILED:
                        await query.edit_message_text(MESSAGES["error_general"])
                        logger.error(f"Ошибка при обработке отчета пользователя {user_id}: {task_info.error}")
                    elif task_info.status == TaskStatus.CANCELLED:
                        await query.edit_message_text("Обработка отчета была отменена.")
                except Exception as e:
                    logger.error(f"Ошибка в progress_callback: {e}")
            
            # Создаем асинхронную задачу для обработки отчета
            task_id = self.task_manager.create_task(
                user_id=user_id,
                coro=self._process_report_async(report, user_id),
                progress_callback=progress_callback
            )
            
            await query.edit_message_text("⏳ Обрабатываю отчет... Это может занять несколько минут.")
            logger.info(f"Создана задача {task_id} для обработки отчета пользователя {user_id}")
            
            # Очищаем временный отчет
            del self.user_reports[user_id]
                
        elif query.data == "edit_report":
            await query.edit_message_text(
                "Какую часть отчета вы хотите изменить?\n\n"
                "Начните заново с команды /report"
            )
            
        elif query.data == "cancel_report":
            if user_id in self.user_reports:
                del self.user_reports[user_id]
            await query.edit_message_text("Создание отчета отменено.")
        
        return ConversationHandler.END
    
    async def cancel_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Отмена создания отчета"""
        user_id = update.effective_user.id
        
        if user_id in self.user_reports:
            del self.user_reports[user_id]
        
        if update.callback_query:
            await update.callback_query.edit_message_text("Создание отчета отменено.")
        else:
            await update.message.reply_text("Создание отчета отменено.")
        return ConversationHandler.END
    
    async def _process_report_async(self, report: WeeklyReport, user_id: int) -> bool:
        """Асинхронная обработка отчета"""
        try:
            logger.info(f"Начинаем асинхронную обработку отчета пользователя {user_id}")
            
            # Обработка отчета через Ollama
            processed_report = await self.ollama_service.process_report(report)
            
            # Отправка в группу
            success = await self.telegram_service.send_report_to_group(processed_report)
            
            if success:
                logger.info(f"Отчет пользователя {user_id} успешно обработан и отправлен")
            else:
                logger.error(f"Ошибка отправки отчета пользователя {user_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Ошибка при асинхронной обработке отчета пользователя {user_id}: {e}")
            raise
    
    async def task_status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Показать статус текущей задачи пользователя"""
        user_id = update.effective_user.id
        
        task_info = self.task_manager.get_user_task(user_id)
        
        if not task_info:
            await update.message.reply_text("У вас нет активных задач.")
            return
        
        status_emoji = {
            TaskStatus.PENDING: "⏳",
            TaskStatus.RUNNING: "🔄", 
            TaskStatus.COMPLETED: "✅",
            TaskStatus.FAILED: "❌",
            TaskStatus.CANCELLED: "🚫"
        }
        
        status_text = {
            TaskStatus.PENDING: "Ожидает выполнения",
            TaskStatus.RUNNING: "Выполняется",
            TaskStatus.COMPLETED: "Завершена",
            TaskStatus.FAILED: "Ошибка",
            TaskStatus.CANCELLED: "Отменена"
        }
        
        message = f"{status_emoji[task_info.status]} <b>Статус задачи:</b> {status_text[task_info.status]}\n\n"
        message += f"📅 Создана: {task_info.created_at.strftime('%d.%m.%Y %H:%M')}\n"
        
        if task_info.started_at:
            message += f"🚀 Запущена: {task_info.started_at.strftime('%d.%m.%Y %H:%M')}\n"
        
        if task_info.completed_at:
            message += f"🏁 Завершена: {task_info.completed_at.strftime('%d.%m.%Y %H:%M')}\n"
        
        if task_info.progress_message:
            message += f"\n📝 {task_info.progress_message}"
        
        if task_info.error:
            message += f"\n❌ Ошибка: {task_info.error}"
        
        # Добавляем кнопку отмены для активных задач
        keyboard = None
        if task_info.status in [TaskStatus.PENDING, TaskStatus.RUNNING]:
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("🚫 Отменить задачу", callback_data=f"cancel_task_{task_info.task_id}")
            ]])
        
        await update.message.reply_text(message, parse_mode='HTML', reply_markup=keyboard)
    
    async def cancel_task_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработка отмены задачи"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        task_id = query.data.replace("cancel_task_", "")
        
        # Проверяем, что задача принадлежит пользователю
        task_info = self.task_manager.get_task_info(task_id)
        if not task_info or task_info.user_id != user_id:
            await query.edit_message_text("❌ Задача не найдена или не принадлежит вам.")
            return
        
        # Отменяем задачу
        if self.task_manager.cancel_task(task_id):
            await query.edit_message_text("🚫 Задача отменена.")
        else:
            await query.edit_message_text("❌ Не удалось отменить задачу.")
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Показать статус отчета пользователя."""
        user_id = update.effective_user.id
        
        try:
            # Получаем текущую неделю
            from utils.date_utils import get_current_week_range
            week_start, _ = get_current_week_range()
            
            # Получаем отчет пользователя за текущую неделю
            report = self.report_processor.get_user_report_for_week(user_id, week_start)
            
            if report:
                status_text = (
                    f"📊 <b>Статус вашего отчета:</b>\n\n"
                    f"📅 Дата отправки: {report.submitted_at.strftime('%d.%m.%Y %H:%M')}\n"
                    f"✅ Статус: {report.status}\n\n"
                    f"📝 <b>Краткое содержание:</b>\n"
                    f"• Выполненные задачи: {len(report.completed_tasks)} пунктов\n"
                    f"• Достижения: {len(report.achievements)} пунктов\n"
                    f"• Проблемы: {len(report.problems)} пунктов\n"
                    f"• Планы: {len(report.next_week_plans)} пунктов"
                )
            else:
                status_text = (
                    "📊 <b>Статус отчета:</b>\n\n"
                    "❌ Отчет еще не отправлен\n\n"
                    "Используйте кнопку 'Создать отчет' для создания отчета."
                )
            
            # Проверяем, вызван ли из callback query (из меню)
            if update.callback_query:
                from .states import get_back_to_main_keyboard
                await update.callback_query.message.reply_text(
                    status_text,
                    reply_markup=get_back_to_main_keyboard(),
                    parse_mode='HTML'
                )
            else:
                if not update.message:
                    logger.error("update.message is None in status_command")
                    return
                    
                await update.message.reply_text(
                    status_text,
                    parse_mode='HTML'
                )
            
        except Exception as e:
            logger.error(f"Ошибка при получении статуса отчета: {e}")
            error_text = "❌ Произошла ошибка при получении статуса отчета."
            
            if update.callback_query:
                from .states import get_back_to_main_keyboard
                await update.callback_query.message.reply_text(
                    error_text,
                    reply_markup=get_back_to_main_keyboard()
                )
            else:
                if not update.message:
                    logger.error("update.message is None in status_command error handler")
                    return
                    
                await update.message.reply_text(error_text)
    
    def _format_report_preview(self, report: WeeklyReport) -> str:
        """Форматирование предварительного просмотра отчета"""
        return f"""<b>Отчет за неделю {report.week_start.strftime('%d.%m')} - {report.week_end.strftime('%d.%m.%Y')}</b>

<b>👤 Сотрудник:</b> {report.full_name}
<b>📧 Username:</b> @{report.username}

<b>✅ Выполненные задачи:</b>
{report.completed_tasks}

<b>🏆 Достижения:</b>
{report.achievements}

<b>⚠️ Проблемы:</b>
{report.problems}

<b>📋 Планы на следующую неделю:</b>
{report.next_week_plans}"""
    
    def get_conversation_handler(self) -> ConversationHandler:
        """Создание ConversationHandler для отчетов"""
        return ConversationHandler(
            entry_points=[CommandHandler('report', self.report_command)],
            states={
                ReportStates.WAITING_TASKS: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_tasks)
                ],
                ReportStates.WAITING_ACHIEVEMENTS: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_achievements)
                ],
                ReportStates.WAITING_PROBLEMS: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_problems)
                ],
                ReportStates.WAITING_PLANS: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_plans)
                ],
                ReportStates.WAITING_CONFIRMATION: [
                    CallbackQueryHandler(self.confirm_report)
                ]
            },
            fallbacks=[
                CommandHandler('cancel', self.cancel_report),
                CallbackQueryHandler(self.cancel_report, pattern='^cancel$')
            ],
            name="report_conversation",
            persistent=True
        )