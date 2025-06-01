from telegram import Update
from telegram.ext import ContextTypes
from database import DatabaseManager
import logging


class UserHandler:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработка команды /start"""
        user = update.effective_user
        
        # Проверяем, есть ли пользователь в базе данных
        try:
            employee = self.db_manager.get_employee_by_telegram_id(user.id)
            if not employee:
                # Регистрируем нового пользователя
                from ..models.department import Employee
                new_employee = Employee(
                    telegram_id=user.id,
                    username=user.username,
                    full_name=f"{user.first_name} {user.last_name or ''}".strip(),
                    email=None,
                    department_id=None,
                    position=None,
                    is_active=True
                )
                self.db_manager.add_employee(new_employee)
                self.logger.info(f"Зарегистрирован новый пользователь: {user.id}")
        except Exception as e:
            self.logger.error(f"Ошибка при регистрации пользователя: {e}")
        
        welcome_text = (
            f"👋 Привет, {user.first_name}!\n\n"
            "🤖 Я бот для сбора еженедельных отчетов.\n\n"
            "📋 Доступные команды:\n"
            "• /report - создать новый отчет\n"
            "• /help - помощь\n"
            "• /status - статус отчетов\n\n"
            "Выберите действие:"
        )
        
        await update.message.reply_text(welcome_text)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработка команды /help"""
        help_text = (
            "📖 **Помощь по использованию бота**\n\n"
            "🤖 Этот бот предназначен для сбора еженедельных отчетов сотрудников.\n\n"
            "📋 **Доступные команды:**\n"
            "• `/start` - начать работу с ботом\n"
            "• `/report` - создать новый еженедельный отчет\n"
            "• `/status` - проверить статус ваших отчетов\n"
            "• `/help` - показать эту справку\n\n"
            "📝 **Как создать отчет:**\n"
            "1. Используйте команду `/report`\n"
            "2. Следуйте инструкциям бота\n"
            "3. Заполните все необходимые поля\n"
            "4. Подтвердите отправку отчета\n\n"
            "❓ **Нужна помощь?**\n"
            "Обратитесь к администратору или в службу поддержки."
        )
        
        await update.message.reply_text(help_text, parse_mode='Markdown')

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработка команды /status"""
        user_id = update.effective_user.id
        
        try:
            # Получаем отчеты пользователя из базы данных
            reports = self.db_manager.get_reports_by_user(user_id)
            
            if not reports:
                status_text = (
                    "📊 **Статус ваших отчетов**\n\n"
                    "❌ У вас пока нет отчетов.\n\n"
                    "Используйте команду `/report` для создания первого отчета."
                )
            else:
                status_text = "📊 **Статус ваших отчетов**\n\n"
                
                # Показываем последние 5 отчетов
                for report in reports[-5:]:
                    date_str = report.submitted_at.strftime('%d.%m.%Y %H:%M') if report.submitted_at else 'не отправлен'
                    week_str = f"{report.week_start.strftime('%d.%m')} - {report.week_end.strftime('%d.%m.%Y')}"
                    status_icon = "⚠️" if report.is_late else "✅"
                    
                    status_text += f"{status_icon} **Неделя {week_str}**\n"
                    status_text += f"   📅 Отправлен: {date_str}\n\n"
                
                # Статистика
                total_reports = len(reports)
                late_reports = sum(1 for r in reports if r.is_late)
                on_time_reports = total_reports - late_reports
                
                status_text += "📈 **Статистика:**\n"
                status_text += f"• Всего отчетов: {total_reports}\n"
                status_text += f"• Вовремя: {on_time_reports}\n"
                status_text += f"• С опозданием: {late_reports}\n"
            
            await update.message.reply_text(status_text, parse_mode='Markdown')
            
        except Exception as e:
            self.logger.error(f"Ошибка получения статуса отчетов: {e}")
            await update.message.reply_text(
                "❌ Произошла ошибка при получении статуса отчетов. "
                "Попробуйте позже."
            )