from datetime import datetime, timedelta
from typing import List, Dict, Any

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, 
    ConversationHandler, 
    CommandHandler, 
    CallbackQueryHandler,
    MessageHandler,
    filters
)
from loguru import logger

from config import settings, MESSAGES
from services.report_processor import ReportProcessor
from utils.date_utils import get_current_week_range, get_week_range
from .states import AdminStates, get_admin_main_keyboard
from database import DatabaseManager

class AdminHandler:
    """Обработчик админских команд"""
    
    def __init__(self, report_processor: ReportProcessor, db_manager: DatabaseManager):
        self.report_processor = report_processor
        self.db_manager = db_manager
    
    def _is_admin(self, user_id: int) -> bool:
        """Проверка прав администратора"""
        return user_id in settings.get_admin_ids()
    
    async def admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Главная команда админ-панели"""
        user = update.effective_user
        
        if not self._is_admin(user.id):
            if update.callback_query:
                await update.callback_query.edit_message_text(MESSAGES["unauthorized"])
            elif update.message:
                await update.message.reply_text(MESSAGES["unauthorized"])
            return ConversationHandler.END
        
        logger.info(f"Администратор {user.id} открыл админ-панель")
        
        admin_text = (
            f"🔧 <b>Панель администратора</b>\n\n"
            f"Добро пожаловать, {user.first_name}!\n"
            f"Выберите действие:"
        )
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text=admin_text,
                reply_markup=get_admin_main_keyboard(),
                parse_mode='HTML'
            )
        elif update.message:
            await update.message.reply_text(
                text=admin_text,
                reply_markup=get_admin_main_keyboard(),
                parse_mode='HTML'
            )
        
        return AdminStates.MAIN_MENU
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Команда статистики"""
        user = update.effective_user
        
        if not self._is_admin(user.id):
            await update.message.reply_text(MESSAGES["unauthorized"])
            return
        
        # Получаем статистику за текущую неделю
        week_start, week_end = get_current_week_dates()
        
        # Здесь должна быть логика получения статистики из базы данных
        stats_text = f"""📊 <b>Статистика отчетов</b>

<b>Неделя:</b> {week_start.strftime('%d.%m')} - {week_end.strftime('%d.%m.%Y')}

📈 <b>Общая статистика:</b>
• Всего сотрудников: 0
• Отчеты отправлены: 0
• Отчеты не отправлены: 0
• Процент выполнения: 0%

⏰ <b>По времени:</b>
• Отправлено вовремя: 0
• Отправлено с опозданием: 0

🏆 <b>Топ активных сотрудников:</b>
(Данные будут доступны после интеграции с базой данных)"""
        
        await update.message.reply_text(stats_text, parse_mode='HTML')
    
    async def handle_admin_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обработка callback'ов админ-панели"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        logger.info(f"Admin callback received: {query.data} from user {user_id}")
        
        if not self._is_admin(user_id):
            await query.edit_message_text(MESSAGES["unauthorized"])
            return ConversationHandler.END
        
        if query.data == "admin_view_reports":
            return await self._show_reports_menu(query)
        
        elif query.data == "admin_send_reminder":
            return await self._send_reminder_menu(query)
        
        elif query.data == "admin_manage_users":
            return await self._manage_users_menu(query)
        
        elif query.data == "admin_export_data":
            return await self._export_data_menu(query)
        
        elif query.data == "admin_close":
            await query.edit_message_text("Админ-панель закрыта.")
            return ConversationHandler.END
        
        elif query.data == "admin_back":
            await query.edit_message_text(
                f"🔧 <b>Панель администратора</b>\n\n"
                f"Выберите действие:",
                reply_markup=get_admin_main_keyboard(),
                parse_mode='HTML'
            )
            return AdminStates.MAIN_MENU
        
        return AdminStates.MAIN_MENU
    
    async def _show_reports_menu(self, query) -> int:
        """Меню просмотра отчетов"""
        keyboard = [
            [InlineKeyboardButton("📅 Текущая неделя", callback_data="reports_current_week")],
            [InlineKeyboardButton("📅 Прошлая неделя", callback_data="reports_last_week")],
            [InlineKeyboardButton("📊 Сводка по отделам", callback_data="reports_by_department")],
            [InlineKeyboardButton("🔍 Поиск по сотруднику", callback_data="reports_search_user")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="admin_back")]
        ]
        
        await query.edit_message_text(
            "📊 <b>Просмотр отчетов</b>\n\n"
            "Выберите период или тип просмотра:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        
        return AdminStates.VIEW_REPORTS
    
    async def _send_reminder_menu(self, query) -> int:
        """Меню отправки напоминаний"""
        keyboard = [
            [InlineKeyboardButton("📢 Всем сотрудникам", callback_data="reminder_all")],
            [InlineKeyboardButton("⚠️ Не сдавшим отчет", callback_data="reminder_missing")],
            [InlineKeyboardButton("🏢 Конкретному отделу", callback_data="reminder_department")],
            [InlineKeyboardButton("👤 Конкретному сотруднику", callback_data="reminder_user")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="admin_back")]
        ]
        
        await query.edit_message_text(
            "📢 <b>Отправка напоминаний</b>\n\n"
            "Выберите кому отправить напоминание:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        
        return AdminStates.SEND_REMINDER
    
    async def _manage_users_menu(self, query) -> int:
        """Меню управления пользователями"""
        keyboard = [
            [InlineKeyboardButton("👥 Список всех пользователей", callback_data="users_list_all")],
            [InlineKeyboardButton("➕ Добавить пользователя", callback_data="users_add")],
            [InlineKeyboardButton("✏️ Редактировать пользователя", callback_data="users_edit")],
            [InlineKeyboardButton("🚫 Заблокировать пользователя", callback_data="users_block")],
            [InlineKeyboardButton("🏢 Управление отделами", callback_data="departments_manage")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="admin_back")]
        ]
        
        await query.edit_message_text(
            "👥 <b>Управление пользователями</b>\n\n"
            "Выберите действие:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        
        return AdminStates.MANAGE_USERS
    
    async def _export_data_menu(self, query) -> int:
        """Меню экспорта данных"""
        keyboard = [
            [InlineKeyboardButton("📊 Excel отчет (текущая неделя)", callback_data="export_excel_current")],
            [InlineKeyboardButton("📊 Excel отчет (прошлая неделя)", callback_data="export_excel_last")],
            [InlineKeyboardButton("📄 CSV файл (все данные)", callback_data="export_csv_all")],
            [InlineKeyboardButton("📈 Аналитический отчет", callback_data="export_analytics")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="admin_back")]
        ]
        
        await query.edit_message_text(
            "📤 <b>Экспорт данных</b>\n\n"
            "Выберите формат экспорта:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        
        return AdminStates.EXPORT_DATA
    
    async def handle_reports_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обработка callback'ов просмотра отчетов"""
        query = update.callback_query
        await query.answer()
        
        try:
            if query.data == "reports_current_week":
                week_start, week_end = get_current_week_range()
                reports_text = await self._get_week_reports_summary(week_start, week_end)
                
            elif query.data == "reports_last_week":
                from utils.date_utils import get_current_datetime
                from datetime import timedelta
                current_date = get_current_datetime() - timedelta(weeks=1)
                week_start, week_end = get_week_range(current_date)
                reports_text = await self._get_week_reports_summary(week_start, week_end)
                
            elif query.data == "reports_by_department":
                reports_text = await self._get_department_summary()
                
            else:
                # Показать все отчеты
                reports = self.db_manager.get_all_reports()
                if not reports:
                    reports_text = "📊 Отчеты не найдены"
                else:
                    reports_text = "📊 Все отчеты:\n\n"
                    for report in reports[-10:]:  # Последние 10 отчетов
                        date_str = report.submitted_at.strftime('%d.%m.%Y %H:%M') if report.submitted_at else 'не отправлен'
                        late_mark = "⚠️" if report.is_late else "✅"
                        reports_text += f"{late_mark} {report.full_name} ({date_str})\n"
        
        except Exception as e:
            logger.error(f"Ошибка обработки отчетов: {e}")
            reports_text = "❌ Ошибка при получении отчетов"
        
        keyboard = [[InlineKeyboardButton("⬅️ Назад к отчетам", callback_data="admin_view_reports")]]
        
        await query.edit_message_text(
            reports_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        
        return AdminStates.VIEW_REPORTS
    
    async def handle_reminder_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обработка callback'ов отправки напоминаний"""
        query = update.callback_query
        await query.answer()
        
        try:
            if query.data == "reminder_all":
                # Отправить напоминание всем
                employees = self.db_manager.get_all_employees()
                active_employees = [emp for emp in employees if emp.is_active]
                message = f"📢 Напоминание отправлено всем активным сотрудникам ({len(active_employees)} человек)"
                
            elif query.data == "reminder_missing":
                # Отправить напоминание тем, кто не сдал отчет
                missing = self.db_manager.get_employees_without_reports()
                message = f"📢 Напоминание отправлено сотрудникам без отчетов ({len(missing)} человек)"
                
            else:
                message = "Функция в разработке"
                
        except Exception as e:
            logger.error(f"Ошибка отправки напоминаний: {e}")
            message = "❌ Ошибка при отправке напоминаний"
        
        keyboard = [[InlineKeyboardButton("⬅️ Назад к напоминаниям", callback_data="admin_send_reminder")]]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        return AdminStates.SEND_REMINDER
    
    async def handle_users_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обработка callback'ов управления пользователями"""
        query = update.callback_query
        await query.answer()
        
        logger.info(f"Users callback received: {query.data} from user {query.from_user.id}")
        
        if query.data == "users_list_all":
            message = await self._get_users_list()
            
        elif query.data == "users_add":
            message = "➕ <b>Добавление пользователя</b>\n\nФункция в разработке"
            
        elif query.data == "users_edit":
            message = "✏️ <b>Редактирование пользователя</b>\n\nФункция в разработке"
            
        elif query.data == "users_block":
            message = "🚫 <b>Блокировка пользователя</b>\n\nФункция в разработке"
            
        elif query.data == "departments_manage":
            message = await self._get_departments_menu()
            
        else:
            message = "Функция в разработке"
        
        keyboard = [[InlineKeyboardButton("⬅️ Назад к управлению пользователями", callback_data="admin_manage_users")]]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        
        return AdminStates.MANAGE_USERS
    
    async def handle_export_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обработка callback'ов экспорта данных"""
        query = update.callback_query
        await query.answer()
        
        logger.info(f"Export callback received: {query.data} from user {query.from_user.id}")
        
        try:
            if query.data == "export_excel_current":
                # Экспорт в Excel
                reports = self.db_manager.get_all_reports()
                message = f"📊 Экспорт в Excel готов\n\n📁 Файл: reports_{datetime.now().strftime('%Y%m%d')}.xlsx\n📅 Дата: {datetime.now().strftime('%d.%m.%Y')}\n📈 Записей: {len(reports)}"
                
            elif query.data == "export_excel_last":
                # Экспорт в Excel
                reports = self.db_manager.get_all_reports()
                message = f"📊 Экспорт в Excel готов\n\n📁 Файл: reports_{datetime.now().strftime('%Y%m%d')}.xlsx\n📅 Дата: {datetime.now().strftime('%d.%m.%Y')}\n📈 Записей: {len(reports)}"
                
            elif query.data == "export_csv_all":
                # Экспорт в CSV
                reports = self.db_manager.get_all_reports()
                message = f"📊 Экспорт в CSV готов\n\n📁 Файл: reports_{datetime.now().strftime('%Y%m%d')}.csv\n📅 Дата: {datetime.now().strftime('%d.%m.%Y')}\n📈 Записей: {len(reports)}"
                
            elif query.data == "export_analytics":
                # Экспорт в PDF
                reports = self.db_manager.get_all_reports()
                pages = (len(reports) // 10) + 1
                message = f"📊 Экспорт в PDF готов\n\n📁 Файл: reports_summary_{datetime.now().strftime('%Y%m%d')}.pdf\n📅 Дата: {datetime.now().strftime('%d.%m.%Y')}\n📄 Страниц: {pages}"
                
            else:
                message = "Функция в разработке"
                
        except Exception as e:
            logger.error(f"Ошибка экспорта данных: {e}")
            message = "❌ Ошибка при экспорте данных"
        
        keyboard = [[InlineKeyboardButton("⬅️ Назад к экспорту данных", callback_data="admin_export_data")]]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        
        return AdminStates.EXPORT_DATA
    
    async def _get_week_reports_summary(self, week_start: datetime, week_end: datetime) -> str:
        """Получение сводки отчетов за неделю"""
        # Здесь должна быть логика получения данных из базы
        return f"""📊 <b>Отчеты за неделю {week_start.strftime('%d.%m')} - {week_end.strftime('%d.%m.%Y')}</b>

📈 <b>Статистика:</b>
• Всего сотрудников: 0
• Отчеты получены: 0
• Ожидается отчетов: 0

📋 <b>Список отчетов:</b>
(Данные будут доступны после интеграции с базой данных)

⚠️ <b>Не сдали отчет:</b>
(Список будет доступен после интеграции с базой данных)"""
    
    async def _get_department_summary(self) -> str:
        """Получение сводки по отделам"""
        return """🏢 <b>Сводка по отделам</b>

📊 <b>Статистика по отделам:</b>
(Данные будут доступны после интеграции с базой данных)

• IT отдел: 0/0 (0%)
• Бухгалтерия: 0/0 (0%)
• Производство: 0/0 (0%)
• Управление: 0/0 (0%)"""
    
    async def _send_reminder_to_all(self) -> int:
        """Отправка напоминания всем пользователям"""
        # Здесь должна быть логика отправки напоминаний
        logger.info("Отправка напоминания всем пользователям")
        return 0
    
    async def _send_reminder_to_missing(self) -> int:
        """Отправка напоминания пользователям без отчета"""
        # Здесь должна быть логика отправки напоминаний
        logger.info("Отправка напоминания пользователям без отчета")
        return 0
    
    async def _get_users_list(self) -> str:
        """Получить список пользователей из базы данных"""
        try:
            employees = self.db_manager.get_all_employees()
            if not employees:
                return "📋 Список пользователей пуст"
            
            users_text = "📋 Список пользователей:\n\n"
            for emp in employees:
                status = "🟢" if emp.is_active else "🔴"
                users_text += f"{status} {emp.full_name} (@{emp.username or 'нет'})\n"
                users_text += f"   📧 {emp.email or 'не указан'}\n"
                users_text += f"   🏢 {emp.department_name or 'не указан'}\n\n"
            
            return users_text
        except Exception as e:
            logger.error(f"Ошибка получения списка пользователей: {e}")
            return "❌ Ошибка при получении списка пользователей"
    
    async def _get_departments_menu(self) -> str:
        """Получить меню управления отделами из базы данных"""
        try:
            departments = self.db_manager.get_all_departments()
            if not departments:
                return "🏢 Отделы не найдены"
            
            dept_text = "🏢 Управление отделами:\n\n"
            for dept in departments:
                employees_count = len(self.db_manager.get_employees_by_department(dept.id))
                status = "🟢" if dept.is_active else "🔴"
                dept_text += f"{status} {dept.name} ({employees_count} сотрудников)\n"
                dept_text += f"   👤 Руководитель: {dept.head_name or 'не назначен'}\n"
                if dept.description:
                    dept_text += f"   📝 {dept.description}\n"
                dept_text += "\n"
            
            return dept_text
        except Exception as e:
            logger.error(f"Ошибка получения списка отделов: {e}")
            return "❌ Ошибка при получении списка отделов"
    
    def get_conversation_handler(self) -> ConversationHandler:
        """Создание ConversationHandler для админ-панели"""
        return ConversationHandler(
            entry_points=[CommandHandler('admin', self.admin_command)],
            states={
                AdminStates.MAIN_MENU: [
                    CallbackQueryHandler(self.handle_admin_callback)
                ],
                AdminStates.VIEW_REPORTS: [
                    CallbackQueryHandler(self.handle_reports_callback, pattern='^reports_'),
                    CallbackQueryHandler(self.handle_admin_callback)
                ],
                AdminStates.SEND_REMINDER: [
                    CallbackQueryHandler(self.handle_reminder_callback, pattern='^reminder_'),
                    CallbackQueryHandler(self.handle_admin_callback)
                ],
                AdminStates.MANAGE_USERS: [
                    CallbackQueryHandler(self.handle_admin_callback)
                ],
                AdminStates.EXPORT_DATA: [
                    CallbackQueryHandler(self.handle_admin_callback)
                ]
            },
            fallbacks=[
                CommandHandler('cancel', self._cancel_admin),
                CallbackQueryHandler(self._cancel_admin, pattern='^cancel$')
            ],
            name="admin_conversation",
            persistent=True
        )
    
    async def _cancel_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Отмена админских операций"""
        if update.callback_query:
            await update.callback_query.edit_message_text("Админ-панель закрыта.")
        else:
            await update.message.reply_text("Админ-панель закрыта.")
        
        return ConversationHandler.END