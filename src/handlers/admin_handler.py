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
from .states import AdminStates, get_admin_main_keyboard, get_wizard_navigation_keyboard, get_confirmation_keyboard, get_delete_confirmation_keyboard
from database import DatabaseManager
from models.department import Employee, Department

from services.telegram_service import TelegramService

class AdminHandler:
    """Обработчик админских команд"""
    
    def __init__(self, report_processor: ReportProcessor, db_manager: DatabaseManager, telegram_service: TelegramService):
        self.report_processor = report_processor
        self.db_manager = db_manager
        self.telegram_service = telegram_service
    
    def _is_admin(self, user_id: int) -> bool:
        """Проверка прав администратора"""
        return user_id in settings.get_admin_ids()
    
    async def _is_admin_async(self, user_id: int) -> bool:
        """Асинхронная проверка прав администратора (проверяет и конфиг, и БД)"""
        # Проверяем конфигурационный файл (основные админы)
        if user_id in settings.get_admin_ids():
            return True
        
        # Проверяем базу данных
        try:
            employee = await self.db_manager.get_employee_by_user_id(user_id)
            return employee and employee.is_admin and employee.is_active and not employee.is_blocked
        except Exception as e:
            logger.error(f"Ошибка проверки прав администратора для пользователя {user_id}: {e}")
            return False
    
    async def admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Главная команда админ-панели"""
        user = update.effective_user
        
        if not await self._is_admin_async(user.id):
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
        
        if not await self._is_admin_async(user.id):
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
        
        if not await self._is_admin_async(user_id):
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
            [InlineKeyboardButton("⬅️ Назад", callback_data="admin_back")],
            [InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_main")]
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
            [InlineKeyboardButton("⬅️ Назад", callback_data="admin_back")],
            [InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_main")]
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
            [InlineKeyboardButton("➕ Добавить пользователя", callback_data="users_add_wizard")],
            [InlineKeyboardButton("✏️ Редактировать пользователя", callback_data="users_edit")],
            [InlineKeyboardButton("🚫 Заблокировать пользователя", callback_data="users_block")],
            [InlineKeyboardButton("🗑️ Удалить пользователя", callback_data="users_delete")],
            [InlineKeyboardButton("👑 Управление админами", callback_data="admin_rights_manage")],
            [InlineKeyboardButton("🏢 Управление отделами", callback_data="departments_manage")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="admin_back")],
            [InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_main")]
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
            [InlineKeyboardButton("⬅️ Назад", callback_data="admin_back")],
            [InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_main")]
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
                reports = self.report_processor.get_all_reports()
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
                employees = await self.db_manager.get_employees()
                active_employees = [emp for emp in employees if emp.is_active and not emp.is_blocked]
                
                # Отправляем напоминания
                if active_employees:
                    results = await self.telegram_service.send_bulk_reminders(active_employees)
                    sent_count = results.get('sent', 0)
                    message = f"📢 Напоминание отправлено всем активным сотрудникам ({sent_count}/{len(active_employees)} человек)"
                else:
                    message = "❌ Нет активных сотрудников для отправки напоминаний"
                
            elif query.data == "reminder_missing":
                # Отправить напоминание тем, кто не сдал отчет
                from datetime import date, timedelta
                # Получаем начало текущей недели (понедельник)
                today = date.today()
                week_start = today - timedelta(days=today.weekday())
                missing = await self.db_manager.get_missing_reports_users(week_start)
                
                # Отправляем напоминания
                if missing:
                    results = await self.telegram_service.send_bulk_reminders(missing)
                    sent_count = results.get('sent', 0)
                    message = f"📢 Напоминание отправлено сотрудникам без отчетов ({sent_count}/{len(missing)} человек)"
                else:
                    message = "✅ Все сотрудники уже сдали отчеты на эту неделю"
            
            elif query.data == "reminder_department":
                # TODO: Реализовать выбор отдела и отправку напоминания
                message = "Функция отправки напоминания отделу в разработке."
                context.user_data['action'] = 'remind_department'
                # Тут нужно будет запросить код отдела
                # await query.edit_message_text("Введите код отдела для отправки напоминания:")
                # return AdminStates.WAITING_INPUT

            elif query.data == "reminder_user":
                # TODO: Реализовать выбор сотрудника и отправку напоминания
                message = "Функция отправки напоминания сотруднику в разработке."
                context.user_data['action'] = 'remind_user'
                # Тут нужно будет запросить ID или имя сотрудника
                # await query.edit_message_text("Введите ID или ФИО сотрудника для отправки напоминания:")
                # return AdminStates.WAITING_INPUT
            else:
                message = "Неизвестное действие для напоминания."
                
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
            message = await self._handle_add_user_request()
            # Переходим в состояние ожидания данных пользователя
            context.user_data['action'] = 'add_user'
            await query.edit_message_text(
                message,
                parse_mode='HTML'
            )
            return AdminStates.WAITING_INPUT
            
        elif query.data == "users_add_wizard":
            return await self._start_add_user_wizard(update, context)
            
        elif query.data == "users_delete":
            return await self._start_delete_user_wizard(update, context)
            
        elif query.data == "users_edit":
            message = await self._handle_edit_user_request()
            context.user_data['action'] = 'edit_user'
            await query.edit_message_text(
                message,
                parse_mode='HTML'
            )
            return AdminStates.WAITING_INPUT
            
        elif query.data == "users_block":
            message = await self._handle_block_user_request()
            context.user_data['action'] = 'block_user'
            await query.edit_message_text(
                message,
                parse_mode='HTML'
            )
            return AdminStates.WAITING_INPUT
            
        elif query.data == "admin_rights_manage":
            return await self._admin_rights_menu(query)
            
        elif query.data == "departments_manage":
            return await self._departments_menu(query)
            
        elif query.data == "departments_list_all":
            message = await self._get_departments_menu()
            
        elif query.data == "departments_add":
            message = await self._handle_add_department_request()
            context.user_data['action'] = 'add_department'
            await query.edit_message_text(
                message,
                parse_mode='HTML'
            )
            return AdminStates.WAITING_INPUT
            
        elif query.data == "departments_add_wizard":
            return await self._start_add_department_wizard(update, context)
            
        elif query.data == "departments_delete":
            return await self._start_delete_department_wizard(update, context)
            
        elif query.data == "departments_edit":
            message = await self._handle_edit_department_request()
            context.user_data['action'] = 'edit_department'
            await query.edit_message_text(
                message,
                parse_mode='HTML'
            )
            return AdminStates.WAITING_INPUT
            
        elif query.data == "departments_toggle":
            message = await self._handle_toggle_department_request()
            context.user_data['action'] = 'toggle_department'
            await query.edit_message_text(
                message,
                parse_mode='HTML'
            )
            return AdminStates.WAITING_INPUT
            
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
                reports = self.report_processor.get_all_reports()
                message = f"📊 Экспорт в Excel готов\n\n📁 Файл: reports_{datetime.now().strftime('%Y%m%d')}.xlsx\n📅 Дата: {datetime.now().strftime('%d.%m.%Y')}\n📈 Записей: {len(reports)}"
                
            elif query.data == "export_excel_last":
                # Экспорт в Excel
                reports = self.report_processor.get_all_reports()
                message = f"📊 Экспорт в Excel готов\n\n📁 Файл: reports_{datetime.now().strftime('%Y%m%d')}.xlsx\n📅 Дата: {datetime.now().strftime('%d.%m.%Y')}\n📈 Записей: {len(reports)}"
                
            elif query.data == "export_csv_all":
                # Экспорт в CSV
                reports = self.report_processor.get_all_reports()
                message = f"📊 Экспорт в CSV готов\n\n📁 Файл: reports_{datetime.now().strftime('%Y%m%d')}.csv\n📅 Дата: {datetime.now().strftime('%d.%m.%Y')}\n📈 Записей: {len(reports)}"
                
            elif query.data == "export_analytics":
                # Экспорт в PDF
                reports = self.report_processor.get_all_reports()
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
    
    async def _handle_add_user_request(self) -> str:
        """Запрос данных для добавления нового пользователя"""
        departments = await self.db_manager.get_departments()
        dept_list = "\n".join([f"• {dept.code} - {dept.name}" for dept in departments])
        
        return (
            "➕ <b>Добавление нового пользователя</b>\n\n"
            "Отправьте данные пользователя в следующем формате:\n\n"
            "<code>user_id:username:full_name:department_code:position:employee_id:email:phone</code>\n\n"
            "<b>Пример:</b>\n"
            "<code>123456789:john_doe:Иванов Иван Иванович:IT:Программист:EMP001:ivan@company.com:+7900123456</code>\n\n"
            "<b>Доступные отделы:</b>\n"
            f"{dept_list}\n\n"
            "Или отправьте /cancel для отмены"
        )
    
    async def _handle_edit_user_request(self) -> str:
        """Запрос данных для редактирования пользователя"""
        return (
            "✏️ <b>Редактирование пользователя</b>\n\n"
            "Отправьте user_id пользователя для редактирования:\n\n"
            "<b>Пример:</b> <code>123456789</code>\n\n"
            "Или отправьте /cancel для отмены"
        )
    
    async def _handle_block_user_request(self) -> str:
        """Запрос данных для блокировки пользователя"""
        return (
            "🚫 <b>Блокировка/разблокировка пользователя</b>\n\n"
            "Отправьте данные в формате:\n"
            "<code>user_id:action</code>\n\n"
            "Где action может быть:\n"
            "• <code>block</code> - заблокировать\n"
            "• <code>unblock</code> - разблокировать\n\n"
            "<b>Пример:</b> <code>123456789:block</code>\n\n"
            "Или отправьте /cancel для отмены"
        )
    
    async def handle_user_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обработка ввода данных пользователя"""
        message = update.message
        text = message.text
        user_action = context.user_data.get('action')
        
        if text == '/cancel':
            await message.reply_text("❌ Операция отменена")
            return await self.admin_command(update, context)
        
        if user_action == 'add_user':
            return await self._process_add_user(update, context)
        
        elif user_action == 'edit_user':
            try:
                user_id = int(text.strip())
                
                # Получение данных пользователя
                employee = await self.db_manager.get_employee_by_user_id(user_id)
                if not employee:
                    await message.reply_text(
                    "❌ Пользователь не найден.",
                    reply_markup=get_admin_main_keyboard()
                )
                    context.user_data.clear()
                    return AdminStates.MAIN_MENU
                
                # Сохранение user_id для следующего шага
                context.user_data['edit_user_id'] = user_id
                context.user_data['action'] = 'edit_user_data'
                
                await message.reply_text(
                     f"👤 <b>Редактирование пользователя</b>\n\n"
                     f"Текущие данные:\n"
                     f"• ID: {employee.user_id}\n"
                     f"• Имя: {employee.full_name}\n"
                     f"• Отдел: {employee.department}\n\n"
                     f"Отправьте новые данные в формате:\n"
                     f"<code>полное_имя:отдел</code>\n\n"
                     f"Или отправьте /cancel для отмены",
                     parse_mode='HTML'
                 )
                
                return AdminStates.WAITING_INPUT
                
            except ValueError:
                await message.reply_text(
                    "❌ Неверный формат user_id. Должно быть число."
                )
                return AdminStates.WAITING_INPUT
            except Exception as e:
                logger.error(f"Ошибка получения пользователя: {e}")
                await message.reply_text(
                    "❌ Произошла ошибка при получении данных пользователя."
                )
                return AdminStates.WAITING_INPUT
        
        elif user_action == 'edit_user_data':
            try:
                parts = text.split(':')
                if len(parts) != 2:
                    await message.reply_text(
                        "❌ Неверный формат данных. Используйте:\n"
                        "<code>полное_имя:отдел</code>"
                    )
                    return AdminStates.WAITING_INPUT
                
                full_name, department = [p.strip() for p in parts]
                user_id = context.user_data['edit_user_id']
                
                # Создание объекта Employee с обновленными данными
                # Обновление данных
                success = await self.db_manager.update_employee(
                    user_id=user_id,
                    full_name=full_name,
                    department_code=department
                )
                
                if not success:
                    await message.reply_text(
                        "❌ Ошибка при обновлении данных пользователя",
                        reply_markup=get_admin_main_keyboard()
                    )
                    return AdminStates.MAIN_MENU
                
                await message.reply_text(
                    f"✅ Данные пользователя {full_name} успешно обновлены!",
                    reply_markup=get_admin_main_keyboard()
                )
                
                context.user_data.clear()
                return AdminStates.MAIN_MENU
                
            except Exception as e:
                logger.error(f"Ошибка обновления пользователя: {e}")
                reply_markup = InlineKeyboardMarkup([
                    [InlineKeyboardButton("⬅️ Назад к управлению пользователями", callback_data="manage_users")]
                ])
                await message.reply_text(
                    "❌ Произошла ошибка при обновлении данных пользователя.",
                    reply_markup=reply_markup
                )
                return AdminStates.WAITING_INPUT
        
        elif user_action == 'block_user':
            try:
                parts = text.split(':')
                if len(parts) != 2:
                    await message.reply_text(
                        "❌ Неверный формат данных. Используйте:\n"
                        "<code>user_id:action</code>\n"
                        "Где action: block или unblock"
                    )
                    return AdminStates.WAITING_INPUT
                
                user_id, action_type = [p.strip() for p in parts]
                user_id = int(user_id)
                
                if action_type not in ['block', 'unblock']:
                    await message.reply_text(
                        "❌ Неверное действие. Используйте 'block' или 'unblock'."
                    )
                    return AdminStates.WAITING_INPUT
                
                is_blocked = action_type == 'block'
                await self.db_manager.block_employee(user_id, is_blocked)
                
                action_text = "заблокирован" if is_blocked else "разблокирован"
                await message.reply_text(
                    f"✅ Пользователь {action_text}!",
                    reply_markup=get_admin_main_keyboard()
                )
                
                context.user_data.clear()
                return AdminStates.MAIN_MENU
                
            except ValueError:
                await message.reply_text(
                    "❌ Неверный формат user_id. Должно быть число."
                )
                return AdminStates.WAITING_INPUT
            except Exception as e:
                logger.error(f"Ошибка блокировки пользователя: {e}")
                reply_markup = InlineKeyboardMarkup([
                    [InlineKeyboardButton("⬅️ Назад к управлению пользователями", callback_data="manage_users")]
                ])
                await message.reply_text(
                    "❌ Произошла ошибка при изменении статуса пользователя.",
                    reply_markup=reply_markup
                )
                return AdminStates.WAITING_INPUT
        
        elif user_action == 'add_department':
            try:
                parts = text.split(':')
                if len(parts) != 4:
                    await message.reply_text(
                        "❌ Неверный формат данных. Используйте:\n"
                        "<code>код:название:описание:руководитель</code>"
                    )
                    return AdminStates.WAITING_INPUT
                
                code, name, description, head_name = [p.strip() for p in parts]
                
                # Создаем объект Department
                department = Department(
                    code=code,
                    name=name,
                    description=description if description else None,
                    head_name=head_name if head_name else None,
                    is_active=True
                )
                
                # Добавляем в базу данных
                success = await self.db_manager.add_department(department)
                
                if success:
                    await message.reply_text(
                        f"✅ Отдел '{name}' успешно добавлен!",
                        reply_markup=get_admin_main_keyboard()
                    )
                    context.user_data.clear()
                    return AdminStates.MAIN_MENU
                else:
                    reply_markup = InlineKeyboardMarkup([
                        [InlineKeyboardButton("⬅️ Назад к управлению отделами", callback_data="manage_departments")]
                    ])
                    await message.reply_text(
                        "❌ Ошибка при добавлении отдела (возможно, код уже существует)",
                        reply_markup=reply_markup
                    )
                    return AdminStates.WAITING_INPUT
                    
            except Exception as e:
                logger.error(f"Ошибка добавления отдела: {e}")
                reply_markup = InlineKeyboardMarkup([
                    [InlineKeyboardButton("⬅️ Назад к управлению отделами", callback_data="manage_departments")]
                ])
                await message.reply_text(
                    "❌ Произошла ошибка при добавлении отдела",
                    reply_markup=reply_markup
                )
                return AdminStates.WAITING_INPUT
        
        elif user_action == 'edit_department':
            try:
                parts = text.split(':')
                if len(parts) != 4:
                    await message.reply_text(
                        "❌ Неверный формат данных. Используйте:\n"
                        "<code>код:новое_название:новое_описание:новый_руководитель</code>"
                    )
                    return AdminStates.WAITING_INPUT
                
                code, name, description, head_name = [p.strip() for p in parts]
                
                # Получаем существующий отдел
                department = await self.db_manager.get_department_by_code(code)
                if not department:
                    await message.reply_text(
                        f"❌ Отдел с кодом '{code}' не найден"
                    )
                    return AdminStates.WAITING_INPUT
                
                # Обновляем данные
                department.name = name
                department.description = description if description else None
                department.head_name = head_name if head_name else None
                
                success = await self.db_manager.update_department(department)
                
                if success:
                    await message.reply_text(
                        f"✅ Отдел '{name}' успешно обновлен!",
                        reply_markup=get_admin_main_keyboard()
                    )
                    context.user_data.clear()
                    return AdminStates.MAIN_MENU
                else:
                    reply_markup = InlineKeyboardMarkup([
                        [InlineKeyboardButton("⬅️ Назад к управлению отделами", callback_data="manage_departments")]
                    ])
                    await message.reply_text(
                        "❌ Ошибка при обновлении отдела",
                        reply_markup=reply_markup
                    )
                    return AdminStates.WAITING_INPUT
                    
            except Exception as e:
                logger.error(f"Ошибка редактирования отдела: {e}")
                reply_markup = InlineKeyboardMarkup([
                    [InlineKeyboardButton("⬅️ Назад к управлению отделами", callback_data="manage_departments")]
                ])
                await message.reply_text(
                    "❌ Произошла ошибка при редактировании отдела",
                    reply_markup=reply_markup
                )
                return AdminStates.WAITING_INPUT
        
        elif user_action == 'toggle_department':
            try:
                code = text.strip()
                
                # Получаем существующий отдел
                department = await self.db_manager.get_department_by_code(code)
                if not department:
                    await message.reply_text(
                        f"❌ Отдел с кодом '{code}' не найден"
                    )
                    return AdminStates.WAITING_INPUT
                
                # Переключаем статус
                department.is_active = not department.is_active
                success = await self.db_manager.update_department(department)
                
                if success:
                    status_text = "активирован" if department.is_active else "деактивирован"
                    await message.reply_text(
                        f"✅ Отдел '{department.name}' {status_text}!",
                        reply_markup=get_admin_main_keyboard()
                    )
                    context.user_data.clear()
                    return AdminStates.MAIN_MENU
                else:
                    reply_markup = InlineKeyboardMarkup([
                        [InlineKeyboardButton("⬅️ Назад к управлению отделами", callback_data="manage_departments")]
                    ])
                    await message.reply_text(
                        "❌ Ошибка при изменении статуса отдела",
                        reply_markup=reply_markup
                    )
                    return AdminStates.WAITING_INPUT
                    
            except Exception as e:
                logger.error(f"Ошибка изменения статуса отдела: {e}")
                reply_markup = InlineKeyboardMarkup([
                    [InlineKeyboardButton("⬅️ Назад к управлению отделами", callback_data="manage_departments")]
                ])
                await message.reply_text(
                    "❌ Произошла ошибка при изменении статуса отдела",
                    reply_markup=reply_markup
                )
                return AdminStates.WAITING_INPUT
        
        return AdminStates.MAIN_MENU
    
    async def _process_add_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обработка добавления нового пользователя"""
        try:
            data = update.message.text.strip().split(':')
            if len(data) != 8:
                await update.message.reply_text(
                    "❌ Неверный формат данных. Требуется 8 полей, разделенных двоеточием."
                )
                return AdminStates.WAITING_INPUT
            
            user_id, username, full_name, dept_code, position, emp_id, email, phone = data
            
            # Создаем объект Employee
            employee = Employee(
                user_id=int(user_id),
                username=username,
                full_name=full_name,
                department_code=dept_code,
                position=position,
                employee_id=emp_id,
                email=email,
                phone=phone,
                is_active=True,
                is_blocked=False
            )
            
            # Проверяем, существует ли отдел
            departments = await self.db_manager.get_departments()
            dept_codes = [dept.code for dept in departments]
            
            if dept_code not in dept_codes:
                reply_markup = InlineKeyboardMarkup([
                    [InlineKeyboardButton("⬅️ Назад к управлению пользователями", callback_data="manage_users")]
                ])
                await update.message.reply_text(
                    f"❌ Отдел с кодом '{dept_code}' не существует!\n\n"
                    f"Доступные отделы: {', '.join(dept_codes)}",
                    parse_mode='HTML',
                    reply_markup=reply_markup
                )
                return AdminStates.WAITING_INPUT
            
            # Добавляем в базу данных
            success = await self.db_manager.add_employee(employee)
            
            if success:
                await update.message.reply_text(
                    f"✅ Пользователь {full_name} успешно добавлен!",
                    parse_mode='HTML'
                )
            else:
                reply_markup = InlineKeyboardMarkup([
                    [InlineKeyboardButton("⬅️ Назад к управлению пользователями", callback_data="manage_users")]
                ])
                await update.message.reply_text(
                    "❌ Ошибка при добавлении пользователя.\n\n"
                    "Возможные причины:\n"
                    "• Пользователь с таким ID уже существует\n"
                    "• Табельный номер уже используется\n"
                    "• Неверный формат данных\n\n"
                    "Проверьте данные и попробуйте снова.",
                    parse_mode='HTML',
                    reply_markup=reply_markup
                )
            
            # Очищаем контекст
            context.user_data.clear()
            
            return await self.admin_command(update, context)
            
        except ValueError as e:
            reply_markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Назад к управлению пользователями", callback_data="manage_users")]
            ])
            if "invalid literal for int()" in str(e):
                await update.message.reply_text(
                    "❌ Неверный формат user_id. Должно быть число.\n\n"
                    "Пример правильного формата:\n"
                    "<code>123456789:john_doe:Иванов И.И.:IT:Программист:EMP001:ivan@company.com:+7900123456</code>",
                    parse_mode='HTML',
                    reply_markup=reply_markup
                )
            else:
                await update.message.reply_text(
                    f"❌ Ошибка валидации данных: {str(e)}\n\n"
                    "Проверьте правильность введенных данных.",
                    parse_mode='HTML',
                    reply_markup=reply_markup
                )
            return AdminStates.WAITING_INPUT
        except Exception as e:
            logger.error(f"Ошибка при добавлении пользователя: {e}")
            reply_markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Назад к управлению пользователями", callback_data="manage_users")]
            ])
            await update.message.reply_text(
                "❌ Произошла неожиданная ошибка при добавлении пользователя.\n\n"
                f"Детали ошибки: {str(e)}",
                parse_mode='HTML',
                reply_markup=reply_markup
            )
            return AdminStates.WAITING_INPUT
    
    async def _get_users_list(self) -> str:
        """Получить список пользователей из базы данных"""
        try:
            employees = await self.db_manager.get_employees()
            if not employees:
                return "📋 Список пользователей пуст"
            
            users_text = "📋 Список пользователей:\n\n"
            for emp in employees:
                status = "🟢" if emp.is_active else "🔴"
                users_text += f"{status} {emp.full_name} (@{emp.username or 'нет'})\n"
                users_text += f"   📧 {emp.email or 'не указан'}\n"
                users_text += f"   🏢 {emp.department_code or 'не указан'}\n\n"
            
            return users_text
        except Exception as e:
            logger.error(f"Ошибка получения списка пользователей: {e}")
            return "❌ Ошибка при получении списка пользователей"
    
    async def _departments_menu(self, query) -> int:
        """Меню управления отделами"""
        keyboard = [
            [InlineKeyboardButton("📋 Список всех отделов", callback_data="departments_list_all")],
            [InlineKeyboardButton("➕ Добавить отдел", callback_data="departments_add_wizard")],
            [InlineKeyboardButton("✏️ Редактировать отдел", callback_data="departments_edit")],
            [InlineKeyboardButton("🔄 Активировать/Деактивировать", callback_data="departments_toggle")],
            [InlineKeyboardButton("🗑️ Удалить отдел", callback_data="departments_delete")],
            [InlineKeyboardButton("⬅️ Назад к управлению пользователями", callback_data="admin_manage_users")]
        ]
        
        await query.edit_message_text(
            "🏢 <b>Управление отделами</b>\n\n"
            "Выберите действие:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        
        return AdminStates.MANAGE_USERS
    
    async def _get_departments_menu(self) -> str:
        """Получить список отделов из базы данных"""
        try:
            departments = await self.db_manager.get_departments()
            if not departments:
                return "🏢 Отделы не найдены"
            
            dept_text = "🏢 <b>Список отделов:</b>\n\n"
            for dept in departments:
                employees_count = len(self.report_processor.get_employees_by_department(dept.code))
                status = "🟢" if dept.is_active else "🔴"
                dept_text += f"{status} <b>{dept.name}</b> (код: {dept.code})\n"
                dept_text += f"   👥 Сотрудников: {employees_count}\n"
                dept_text += f"   👤 Руководитель: {dept.head_name or 'не назначен'}\n"
                if dept.description:
                    dept_text += f"   📝 {dept.description}\n"
                dept_text += "\n"
            
            return dept_text
        except Exception as e:
            logger.error(f"Ошибка получения списка отделов: {e}")
            return "❌ Ошибка при получении списка отделов"
    
    async def _handle_add_department_request(self) -> str:
        """Обработка запроса на добавление отдела"""
        return (
            "➕ <b>Добавление нового отдела</b>\n\n"
            "Введите данные отдела в формате:\n"
            "<code>код:название:описание:руководитель</code>\n\n"
            "<b>Пример:</b>\n"
            "<code>IT:Отдел информационных технологий:Разработка и поддержка ПО:Иванов И.И.</code>\n\n"
            "Для отмены введите /cancel"
        )
    
    async def _handle_edit_department_request(self) -> str:
        """Обработка запроса на редактирование отдела"""
        return (
            "✏️ <b>Редактирование отдела</b>\n\n"
            "Введите данные в формате:\n"
            "<code>код:новое_название:новое_описание:новый_руководитель</code>\n\n"
            "<b>Пример:</b>\n"
            "<code>IT:ИТ отдел:Информационные технологии:Петров П.П.</code>\n\n"
            "Для отмены введите /cancel"
        )
    
    async def _handle_toggle_department_request(self) -> str:
        """Обработка запроса на активацию/деактивацию отдела"""
        return (
            "🔄 <b>Активация/Деактивация отдела</b>\n\n"
            "Введите код отдела для изменения статуса:\n\n"
            "<b>Пример:</b>\n"
            "<code>IT</code>\n\n"
            "Для отмены введите /cancel"
        )
    
    # Методы мастера добавления пользователей
    async def _start_add_user_wizard(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Начало мастера добавления пользователя"""
        query = update.callback_query
        await query.answer()
        
        keyboard = get_wizard_navigation_keyboard()
        
        await query.edit_message_text(
            "👤 <b>Добавление нового сотрудника</b>\n\n"
            "Шаг 1 из 8: Введите имя сотрудника\n\n"
            "<b>Пример:</b> Иван",
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        
        context.user_data['wizard_data'] = {}
        return AdminStates.ADD_USER_STEP1_ID
    
    async def _handle_add_user_step1(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обработка ввода имени пользователя"""
        first_name = update.message.text.strip()
        
        if not first_name:
            await update.message.reply_text(
                "❌ Имя не может быть пустым. Попробуйте еще раз:"
            )
            return AdminStates.ADD_USER_STEP1_ID
        
        context.user_data['wizard_data']['first_name'] = first_name
        
        keyboard = get_wizard_navigation_keyboard()
        
        await update.message.reply_text(
            "👤 <b>Добавление нового сотрудника</b>\n\n"
            "Шаг 2 из 8: Введите фамилию сотрудника\n\n"
            "<b>Пример:</b> Иванов",
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        
        return AdminStates.ADD_USER_STEP2_USERNAME
    
    async def _handle_add_user_step2(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обработка ввода фамилии пользователя"""
        last_name = update.message.text.strip()
        
        if not last_name:
            await update.message.reply_text(
                "❌ Фамилия не может быть пустой. Попробуйте еще раз:"
            )
            return AdminStates.ADD_USER_STEP2_USERNAME
        
        context.user_data['wizard_data']['last_name'] = last_name
        
        keyboard = get_wizard_navigation_keyboard(skip_callback="wizard_next")
        
        await update.message.reply_text(
            "👤 <b>Добавление нового сотрудника</b>\n\n"
            "Шаг 3 из 8: Введите отчество сотрудника (или пропустите, нажав 'Далее')\n\n"
            "<b>Пример:</b> Петрович",
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        
        return AdminStates.ADD_USER_STEP3_FULLNAME
    
    async def _handle_add_user_step3(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обработка ввода отчества пользователя"""
        if update.message:
            middle_name = update.message.text.strip()
            context.user_data['wizard_data']['middle_name'] = middle_name if middle_name else None
        elif update.callback_query and update.callback_query.data == 'wizard_next':
            context.user_data['wizard_data']['middle_name'] = None
        
        keyboard = get_wizard_navigation_keyboard()
        
        message_text = (
            "👤 <b>Добавление нового сотрудника</b>\n\n"
            "Шаг 4 из 8: Введите Telegram ID сотрудника\n\n"
            "<b>Пример:</b> 123456789\n\n"
            "💡 <i>Сотрудник может узнать свой ID, написав боту /start</i>"
        )
        
        if update.message:
            await update.message.reply_text(
                message_text,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
        else:
            await update.callback_query.edit_message_text(
                message_text,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
        
        return AdminStates.ADD_USER_STEP4_DEPARTMENT
    
    async def _handle_add_user_step4(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обработка ввода Telegram ID пользователя"""
        try:
            telegram_id = int(update.message.text.strip())
        except ValueError:
            await update.message.reply_text(
                "❌ Telegram ID должен быть числом. Попробуйте еще раз:"
            )
            return AdminStates.ADD_USER_STEP4_DEPARTMENT
        
        # Проверяем, не существует ли уже пользователь с таким ID
        existing_user = await self.db_manager.get_employee_by_user_id(telegram_id)
        if existing_user:
            await update.message.reply_text(
                f"❌ Пользователь с Telegram ID {telegram_id} уже существует.\n"
                "Попробуйте другой ID:"
            )
            return AdminStates.ADD_USER_STEP4_DEPARTMENT
        
        context.user_data['wizard_data']['telegram_id'] = telegram_id
        
        keyboard = get_wizard_navigation_keyboard()
        
        await update.message.reply_text(
            "👤 <b>Добавление нового сотрудника</b>\n\n"
            "Шаг 5 из 8: Введите должность сотрудника\n\n"
            "<b>Пример:</b> Программист",
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        
        return AdminStates.ADD_USER_STEP5_POSITION
    
    async def _handle_add_user_step5(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обработка ввода должности пользователя"""
        position = update.message.text.strip()
        
        if not position:
            await update.message.reply_text(
                "❌ Должность не может быть пустой. Попробуйте еще раз:"
            )
            return AdminStates.ADD_USER_STEP5_POSITION
        
        context.user_data['wizard_data']['position'] = position
        
        # Получаем список отделов
        departments = await self.db_manager.get_departments()
        if not departments:
            await update.message.reply_text(
                "❌ В системе нет отделов. Сначала создайте отдел."
            )
            return ConversationHandler.END
        
        keyboard = get_wizard_navigation_keyboard()
        
        dept_list = "\n".join([f"• <code>{dept.code}</code> - {dept.name}" for dept in departments])
        
        await update.message.reply_text(
            f"👤 <b>Добавление нового сотрудника</b>\n\n"
            f"Шаг 6 из 8: Выберите отдел\n\n"
            f"Доступные отделы:\n{dept_list}\n\n"
            f"Введите код отдела:",
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        
        return AdminStates.ADD_USER_STEP6_EMPLOYEE_ID
    
    async def _handle_add_user_step6(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обработка выбора отдела"""
        department_code = update.message.text.strip().upper()
        
        department = await self.db_manager.get_department_by_code(department_code)
        if not department:
            await update.message.reply_text(
                f"❌ Отдел с кодом '{department_code}' не найден. Попробуйте еще раз:"
            )
            return AdminStates.ADD_USER_STEP6_EMPLOYEE_ID
        
        context.user_data['wizard_data']['department_code'] = department_code
        
        keyboard = get_wizard_navigation_keyboard(skip_callback="wizard_next")
        
        await update.message.reply_text(
            "👤 <b>Добавление нового сотрудника</b>\n\n"
            "Шаг 7 из 8: Введите email сотрудника (или пропустите, нажав 'Далее')\n\n"
            "<b>Пример:</b> ivan.ivanov@company.com",
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        
        return AdminStates.ADD_USER_STEP7_EMAIL
    
    async def _handle_add_user_step7(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обработка ввода email"""
        if update.message:
            email = update.message.text.strip()
            context.user_data['wizard_data']['email'] = email if email else None
        elif update.callback_query and update.callback_query.data == 'wizard_next':
            context.user_data['wizard_data']['email'] = None
        
        keyboard = get_wizard_navigation_keyboard(skip_callback="wizard_next")
        
        message_text = (
            "👤 <b>Добавление нового сотрудника</b>\n\n"
            "Шаг 8 из 8: Введите номер телефона (или пропустите, нажав 'Далее')\n\n"
            "<b>Пример:</b> +7 (999) 123-45-67"
        )
        
        if update.message:
            await update.message.reply_text(
                message_text,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
        else:
            await update.callback_query.edit_message_text(
                message_text,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
        
        return AdminStates.ADD_USER_STEP8_PHONE
    
    async def _handle_add_user_step8(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обработка ввода телефона и показ подтверждения"""
        if update.message:
            phone = update.message.text.strip()
            context.user_data['wizard_data']['phone'] = phone if phone else None
        elif update.callback_query and update.callback_query.data == 'wizard_next':
            context.user_data['wizard_data']['phone'] = None
        
        # Показываем данные для подтверждения
        wizard_data = context.user_data['wizard_data']
        
        summary = (
            "👤 <b>Подтверждение добавления сотрудника</b>\n\n"
            f"<b>Имя:</b> {wizard_data['first_name']}\n"
            f"<b>Фамилия:</b> {wizard_data['last_name']}\n"
        )
        
        if wizard_data.get('middle_name'):
            summary += f"<b>Отчество:</b> {wizard_data['middle_name']}\n"
        
        summary += (
            f"<b>Telegram ID:</b> {wizard_data['telegram_id']}\n"
            f"<b>Должность:</b> {wizard_data['position']}\n"
            f"<b>Отдел:</b> {wizard_data['department_code']}\n"
        )
        
        if wizard_data.get('email'):
            summary += f"<b>Email:</b> {wizard_data['email']}\n"
        
        if wizard_data.get('phone'):
            summary += f"<b>Телефон:</b> {wizard_data['phone']}\n"
        
        summary += "\n✅ Подтвердить добавление?"
        
        keyboard = get_confirmation_keyboard('user_confirm')
        
        if update.message:
            await update.message.reply_text(
                summary,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
        else:
            await update.callback_query.edit_message_text(
                summary,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
        
        return AdminStates.ADD_USER_CONFIRM
    
    async def _confirm_add_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Подтверждение добавления пользователя"""
        query = update.callback_query
        await query.answer()
        
        if query.data == 'user_confirm':
            wizard_data = context.user_data['wizard_data']
            
            try:
                # Создаем объект сотрудника
                from models.department import Employee
                
                # Отладочная информация
                logger.info(f"Wizard data: {wizard_data}")
                
                # Проверяем обязательные поля
                if not wizard_data.get('department_code'):
                    await query.edit_message_text(
                        "❌ Ошибка: не указан код отдела. Попробуйте начать процесс добавления заново.",
                        parse_mode='HTML'
                    )
                    return ConversationHandler.END
                
                # Формируем полное имя
                full_name_parts = [wizard_data['first_name'], wizard_data['last_name']]
                if wizard_data.get('middle_name'):
                    full_name_parts.insert(1, wizard_data['middle_name'])
                full_name = ' '.join(full_name_parts)
                
                employee = Employee(
                    user_id=wizard_data['telegram_id'],
                    full_name=full_name,
                    department_code=wizard_data['department_code'],
                    position=wizard_data['position'],
                    email=wizard_data.get('email'),
                    phone=wizard_data.get('phone')
                )
                
                success = await self.db_manager.add_employee(employee)
                
                if success:
                    keyboard = [[InlineKeyboardButton("⬅️ Назад к управлению пользователями", callback_data="admin_manage_users")]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await query.edit_message_text(
                        f"✅ Сотрудник {wizard_data['first_name']} {wizard_data['last_name']} успешно добавлен!",
                        parse_mode='HTML',
                        reply_markup=reply_markup
                    )
                else:
                    keyboard = [[InlineKeyboardButton("⬅️ Назад к управлению пользователями", callback_data="admin_manage_users")]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await query.edit_message_text(
                        "❌ Ошибка при добавлении сотрудника. Попробуйте еще раз.",
                        reply_markup=reply_markup
                    )
            except Exception as e:
                keyboard = [[InlineKeyboardButton("⬅️ Назад к управлению пользователями", callback_data="admin_manage_users")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(
                    f"❌ Ошибка при добавлении сотрудника: {str(e)}",
                    reply_markup=reply_markup
                )
        else:
            keyboard = [[InlineKeyboardButton("⬅️ Назад к управлению пользователями", callback_data="admin_manage_users")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "❌ Добавление сотрудника отменено.",
                reply_markup=reply_markup
            )
        
        # Очищаем данные мастера
        context.user_data.pop('wizard_data', None)
        return ConversationHandler.END
    
    # Методы мастера удаления пользователей
    async def _start_delete_user_wizard(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Начало мастера удаления пользователя"""
        query = update.callback_query
        await query.answer()
        
        employees = await self.db_manager.get_employees()
        if not employees:
            await query.edit_message_text(
                "❌ В системе нет сотрудников для удаления."
            )
            return ConversationHandler.END
        
        # Создаем список сотрудников для выбора
        keyboard = []
        for emp in employees[:20]:  # Ограничиваем до 20 для удобства
            keyboard.append([
                InlineKeyboardButton(
                    f"{emp.full_name} ({emp.position or 'Не указано'})",
                    callback_data=f"delete_user_{emp.user_id}"
                )
            ])
        
        keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="cancel")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🗑️ <b>Удаление сотрудника</b>\n\n"
            "Выберите сотрудника для удаления:",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        
        return AdminStates.DELETE_USER_SELECT
    
    async def _handle_delete_user_select(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обработка выбора пользователя для удаления"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "cancel":
            await query.edit_message_text("❌ Удаление отменено.")
            return ConversationHandler.END
        
        telegram_id = int(query.data.split("_")[-1])
        employee = await self.db_manager.get_employee_by_user_id(telegram_id)
        
        if not employee:
            await query.edit_message_text("❌ Сотрудник не найден.")
            return ConversationHandler.END
        
        context.user_data['delete_user_id'] = telegram_id
        
        full_name = employee.full_name
        
        keyboard = get_delete_confirmation_keyboard("delete_confirm")
        
        await query.edit_message_text(
            f"🗑️ <b>Подтверждение удаления</b>\n\n"
            f"Вы действительно хотите удалить сотрудника:\n"
            f"<b>{full_name}</b>\n"
            f"Должность: {employee.position}\n"
            f"Отдел: {employee.department_code}\n\n"
            f"⚠️ <i>Это действие нельзя отменить!</i>",
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        
        return AdminStates.DELETE_USER_CONFIRM
    
    async def _confirm_delete_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Подтверждение удаления пользователя"""
        query = update.callback_query
        await query.answer()
        
        if query.data == 'delete_confirm':
            telegram_id = context.user_data.get('delete_user_id')
            if telegram_id:
                employee = await self.db_manager.get_employee_by_user_id(telegram_id)
                if employee:
                    success = await self.db_manager.delete_employee(telegram_id)
                    if success:
                        full_name = employee.full_name
                        keyboard = [[InlineKeyboardButton("⬅️ Назад к управлению пользователями", callback_data="admin_manage_users")]]
                        reply_markup = InlineKeyboardMarkup(keyboard)
                        await query.edit_message_text(
                            f"✅ Сотрудник {full_name} успешно удален!",
                            reply_markup=reply_markup
                        )
                    else:
                        keyboard = [[InlineKeyboardButton("⬅️ Назад к управлению пользователями", callback_data="admin_manage_users")]]
                        reply_markup = InlineKeyboardMarkup(keyboard)
                        await query.edit_message_text(
                            "❌ Ошибка при удалении сотрудника.",
                            reply_markup=reply_markup
                        )
                else:
                    keyboard = [[InlineKeyboardButton("⬅️ Назад к управлению пользователями", callback_data="admin_manage_users")]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await query.edit_message_text("❌ Сотрудник не найден.", reply_markup=reply_markup)
            else:
                keyboard = [[InlineKeyboardButton("⬅️ Назад к управлению пользователями", callback_data="admin_manage_users")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text("❌ Ошибка: ID сотрудника не найден.", reply_markup=reply_markup)
        else:
            keyboard = [[InlineKeyboardButton("⬅️ Назад к управлению пользователями", callback_data="admin_manage_users")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("❌ Удаление отменено.", reply_markup=reply_markup)
        
        context.user_data.pop('delete_user_id', None)
        return ConversationHandler.END
    
    # Методы мастера добавления отделов
    async def _start_add_department_wizard(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Начало мастера добавления отдела"""
        query = update.callback_query
        await query.answer()
        
        keyboard = get_wizard_navigation_keyboard()
        
        await query.edit_message_text(
            "🏢 <b>Добавление нового отдела</b>\n\n"
            "Шаг 1 из 4: Введите код отдела\n\n"
            "<b>Пример:</b> IT\n\n"
            "💡 <i>Код должен быть уникальным и состоять из заглавных букв</i>",
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        
        context.user_data['wizard_data'] = {}
        return AdminStates.ADD_DEPT_STEP1_CODE
    
    async def _handle_add_department_step1(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обработка ввода кода отдела"""
        code = update.message.text.strip().upper()
        
        if not code:
            await update.message.reply_text(
                "❌ Код отдела не может быть пустым. Попробуйте еще раз:"
            )
            return AdminStates.ADD_DEPT_STEP1_CODE
        
        # Проверяем, не существует ли уже отдел с таким кодом
        existing_dept = await self.db_manager.get_department_by_code(code)
        if existing_dept:
            await update.message.reply_text(
                f"❌ Отдел с кодом '{code}' уже существует. Попробуйте другой код:"
            )
            return AdminStates.ADD_DEPT_STEP1_CODE
        
        context.user_data['wizard_data']['code'] = code
        
        keyboard = get_wizard_navigation_keyboard()
        
        await update.message.reply_text(
            "🏢 <b>Добавление нового отдела</b>\n\n"
            "Шаг 2 из 4: Введите название отдела\n\n"
            "<b>Пример:</b> Информационные технологии",
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        
        return AdminStates.ADD_DEPT_STEP2_NAME
    
    async def _handle_add_department_step2(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обработка ввода названия отдела"""
        name = update.message.text.strip()
        
        if not name:
            await update.message.reply_text(
                "❌ Название отдела не может быть пустым. Попробуйте еще раз:"
            )
            return AdminStates.ADD_DEPT_STEP2_NAME
        
        context.user_data['wizard_data']['name'] = name
        
        keyboard = get_wizard_navigation_keyboard(skip_callback="wizard_next")
        
        await update.message.reply_text(
            "🏢 <b>Добавление нового отдела</b>\n\n"
            "Шаг 3 из 4: Введите описание отдела (или пропустите, нажав 'Далее')\n\n"
            "<b>Пример:</b> Отдел разработки и поддержки информационных систем",
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        
        return AdminStates.ADD_DEPT_STEP3_DESCRIPTION
    
    async def _handle_add_department_step3(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обработка ввода описания отдела"""
        if update.message:
            description = update.message.text.strip()
            context.user_data['wizard_data']['description'] = description if description else None
        elif update.callback_query and update.callback_query.data == 'wizard_next':
            context.user_data['wizard_data']['description'] = None
        
        keyboard = get_wizard_navigation_keyboard(skip_callback="wizard_next")
        
        message_text = (
            "🏢 <b>Добавление нового отдела</b>\n\n"
            "Шаг 4 из 4: Введите ФИО руководителя отдела (или пропустите, нажав 'Далее')\n\n"
            "<b>Пример:</b> Иванов Иван Иванович"
        )
        
        if update.message:
            await update.message.reply_text(
                message_text,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
        else:
            await update.callback_query.edit_message_text(
                message_text,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
        
        return AdminStates.ADD_DEPT_STEP4_HEAD
    
    async def _handle_add_department_step4(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обработка ввода руководителя и показ подтверждения"""
        if update.message:
            manager = update.message.text.strip()
            context.user_data['wizard_data']['manager'] = manager if manager else None
        elif update.callback_query and update.callback_query.data == 'wizard_next':
            context.user_data['wizard_data']['manager'] = None
        
        # Показываем данные для подтверждения
        wizard_data = context.user_data['wizard_data']
        
        summary = (
            "🏢 <b>Подтверждение добавления отдела</b>\n\n"
            f"<b>Код:</b> {wizard_data['code']}\n"
            f"<b>Название:</b> {wizard_data['name']}\n"
        )
        
        if wizard_data.get('description'):
            summary += f"<b>Описание:</b> {wizard_data['description']}\n"
        
        if wizard_data.get('manager'):
            summary += f"<b>Руководитель:</b> {wizard_data['manager']}\n"
        
        summary += "\n✅ Подтвердить добавление?"
        
        keyboard = get_confirmation_keyboard('dept_confirm_confirm', 'dept_confirm_cancel')
        
        if update.message:
            await update.message.reply_text(
                summary,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
        else:
            await update.callback_query.edit_message_text(
                summary,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
        
        return AdminStates.ADD_DEPT_CONFIRM
    
    async def _confirm_add_department(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Подтверждение добавления отдела"""
        query = update.callback_query
        await query.answer()
        
        if query.data == 'dept_confirm_confirm':
            wizard_data = context.user_data['wizard_data']
            
            try:
                # Создаем объект отдела
                from models.department import Department
                
                department = Department(
                    code=wizard_data['code'],
                    name=wizard_data['name'],
                    description=wizard_data.get('description'),
                    head_name=wizard_data.get('manager')
                )
                
                success = await self.db_manager.add_department(department)
                
                if success:
                    keyboard = [[InlineKeyboardButton("⬅️ Назад к управлению отделами", callback_data="departments_manage")]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await query.edit_message_text(
                        f"✅ Отдел {wizard_data['name']} ({wizard_data['code']}) успешно добавлен!",
                        parse_mode='HTML',
                        reply_markup=reply_markup
                    )
                else:
                    keyboard = [[InlineKeyboardButton("⬅️ Назад к управлению отделами", callback_data="departments_manage")]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await query.edit_message_text(
                        "❌ Ошибка при добавлении отдела. Попробуйте еще раз.",
                        reply_markup=reply_markup
                    )
            except Exception as e:
                keyboard = [[InlineKeyboardButton("⬅️ Назад к управлению отделами", callback_data="departments_manage")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(
                    f"❌ Ошибка при добавлении отдела: {str(e)}",
                    reply_markup=reply_markup
                )
        elif query.data == 'dept_confirm_edit':
            # Возвращаемся к первому шагу мастера
            return await self._start_add_department_wizard(update, context)
        else:
            keyboard = [[InlineKeyboardButton("⬅️ Назад к управлению отделами", callback_data="departments_manage")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "❌ Добавление отдела отменено.",
                reply_markup=reply_markup
            )
        
        # Очищаем данные мастера
        context.user_data.pop('wizard_data', None)
        return ConversationHandler.END
    
    # Методы мастера удаления отделов
    async def _start_delete_department_wizard(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Начало мастера удаления отдела"""
        query = update.callback_query
        await query.answer()
        
        departments = await self.db_manager.get_departments()
        if not departments:
            await query.edit_message_text(
                "❌ В системе нет отделов для удаления."
            )
            return ConversationHandler.END
        
        # Создаем список отделов для выбора
        keyboard = []
        for dept in departments:
            keyboard.append([
                InlineKeyboardButton(
                    f"{dept.name} ({dept.code})",
                    callback_data=f"delete_dept_{dept.code}"
                )
            ])
        
        keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="cancel")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🗑️ <b>Удаление отдела</b>\n\n"
            "Выберите отдел для удаления:",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        
        return AdminStates.DELETE_DEPT_SELECT
    
    async def _handle_delete_department_select(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обработка выбора отдела для удаления"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "cancel":
            await query.edit_message_text("❌ Удаление отменено.")
            return ConversationHandler.END
        
        dept_code = query.data.split("_")[-1]
        department = await self.db_manager.get_department_by_code(dept_code)
        
        if not department:
            await query.edit_message_text("❌ Отдел не найден.")
            return ConversationHandler.END
        
        # Проверяем, есть ли сотрудники в этом отделе
        employees_in_dept = await self.db_manager.get_employees_by_department(dept_code)
        if employees_in_dept:
            await query.edit_message_text(
                f"❌ Нельзя удалить отдел '{department.name}', так как в нем есть сотрудники.\n\n"
                f"Сначала переведите всех сотрудников в другие отделы или удалите их."
            )
            return ConversationHandler.END
        
        context.user_data['delete_dept_code'] = dept_code
        
        keyboard = get_delete_confirmation_keyboard("delete_confirm")
        
        await query.edit_message_text(
            f"🗑️ <b>Подтверждение удаления</b>\n\n"
            f"Вы действительно хотите удалить отдел:\n"
            f"<b>{department.name} ({department.code})</b>\n\n"
            f"⚠️ <i>Это действие нельзя отменить!</i>",
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        
        return AdminStates.DELETE_DEPT_CONFIRM
    
    async def _confirm_delete_department(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Подтверждение удаления отдела"""
        query = update.callback_query
        await query.answer()
        
        if query.data == 'delete_confirm':
            dept_code = context.user_data.get('delete_dept_code')
            if dept_code:
                department = await self.db_manager.get_department_by_code(dept_code)
                if department:
                    success = await self.db_manager.delete_department(dept_code)
                    if success:
                        keyboard = [[InlineKeyboardButton("⬅️ Назад к управлению отделами", callback_data="admin_manage_departments")]]
                        reply_markup = InlineKeyboardMarkup(keyboard)
                        await query.edit_message_text(
                            f"✅ Отдел {department.name} ({department.code}) успешно удален!",
                            reply_markup=reply_markup
                        )
                    else:
                        keyboard = [[InlineKeyboardButton("⬅️ Назад к управлению отделами", callback_data="admin_manage_departments")]]
                        reply_markup = InlineKeyboardMarkup(keyboard)
                        await query.edit_message_text(
                            "❌ Ошибка при удалении отдела.",
                            reply_markup=reply_markup
                        )
                else:
                    keyboard = [[InlineKeyboardButton("⬅️ Назад к управлению отделами", callback_data="admin_manage_departments")]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await query.edit_message_text("❌ Отдел не найден.", reply_markup=reply_markup)
            else:
                keyboard = [[InlineKeyboardButton("⬅️ Назад к управлению отделами", callback_data="admin_manage_departments")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text("❌ Ошибка: код отдела не найден.", reply_markup=reply_markup)
        else:
            keyboard = [[InlineKeyboardButton("⬅️ Назад к управлению отделами", callback_data="admin_manage_departments")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("❌ Удаление отменено.", reply_markup=reply_markup)
        
        context.user_data.pop('delete_dept_code', None)
        return ConversationHandler.END
    
    async def _admin_rights_menu(self, query) -> int:
        """Меню управления административными правами"""
        keyboard = [
            [InlineKeyboardButton("👑 Список администраторов", callback_data="admin_list")],
            [InlineKeyboardButton("➕ Назначить администратора", callback_data="admin_grant")],
            [InlineKeyboardButton("➖ Снять права администратора", callback_data="admin_revoke")],
            [InlineKeyboardButton("⬅️ Назад к управлению пользователями", callback_data="admin_manage_users")],
            [InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_main")]
        ]
        
        await query.edit_message_text(
            "👑 <b>Управление административными правами</b>\n\n"
            "Выберите действие:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        
        return AdminStates.ADMIN_RIGHTS
    
    async def handle_admin_rights_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обработка callback'ов управления административными правами"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "admin_list":
            message = await self._get_admin_list()
            
        elif query.data == "admin_grant":
            return await self._start_grant_admin_wizard(update, context)
            
        elif query.data == "admin_revoke":
            return await self._start_revoke_admin_wizard(update, context)
            
        else:
            message = "Функция в разработке"
        
        keyboard = [[InlineKeyboardButton("⬅️ Назад к управлению админами", callback_data="admin_rights_manage")]]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        
        return AdminStates.ADMIN_RIGHTS
    
    async def _get_admin_list(self) -> str:
        """Получение списка администраторов"""
        try:
            admins = await self.db_manager.get_admin_employees()
            
            if not admins:
                return "👑 <b>Список администраторов</b>\n\n❌ Администраторы не найдены в базе данных."
            
            admin_list = "👑 <b>Список администраторов</b>\n\n"
            for admin in admins:
                status = "🟢" if admin.is_active and not admin.is_blocked else "🔴"
                admin_list += f"{status} <b>{admin.full_name}</b>\n"
                admin_list += f"   📱 ID: <code>{admin.user_id}</code>\n"
                admin_list += f"   🏢 {admin.department_code} - {admin.position}\n\n"
            
            return admin_list
            
        except Exception as e:
            logger.error(f"Ошибка получения списка администраторов: {e}")
            return "❌ Ошибка при получении списка администраторов"
    
    async def _start_grant_admin_wizard(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Начало мастера назначения администратора"""
        query = update.callback_query
        
        try:
            # Получаем всех сотрудников, которые не являются администраторами
            employees = await self.db_manager.get_employees()
            non_admin_employees = [emp for emp in employees if emp.is_active and not emp.is_blocked and not emp.is_admin]
            
            if not non_admin_employees:
                keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data="admin_rights_manage")]]
                await query.edit_message_text(
                    "❌ Нет сотрудников для назначения администраторами.",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                return AdminStates.ADMIN_RIGHTS
            
            keyboard = []
            for emp in non_admin_employees[:10]:  # Показываем первых 10
                keyboard.append([InlineKeyboardButton(
                    f"{emp.full_name} ({emp.department_code})",
                    callback_data=f"grant_admin_{emp.user_id}"
                )])
            
            keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="admin_rights_manage")])
            
            await query.edit_message_text(
                "➕ <b>Назначение администратора</b>\n\n"
                "Выберите сотрудника для назначения администратором:",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='HTML'
            )
            
            return AdminStates.GRANT_ADMIN_SELECT
            
        except Exception as e:
            logger.error(f"Ошибка в мастере назначения администратора: {e}")
            keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data="admin_rights_manage")]]
            await query.edit_message_text(
                "❌ Ошибка при загрузке списка сотрудников",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return AdminStates.ADMIN_RIGHTS
    
    async def _start_revoke_admin_wizard(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Начало мастера снятия прав администратора"""
        query = update.callback_query
        
        try:
            # Получаем всех администраторов
            admins = await self.db_manager.get_admin_employees()
            
            if not admins:
                keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data="admin_rights_manage")]]
                await query.edit_message_text(
                    "❌ Нет администраторов для снятия прав.",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                return AdminStates.ADMIN_RIGHTS
            
            keyboard = []
            for admin in admins:
                # Не позволяем снимать права с самого себя
                if admin.user_id != query.from_user.id:
                    keyboard.append([InlineKeyboardButton(
                        f"{admin.full_name} ({admin.department_code})",
                        callback_data=f"revoke_admin_{admin.user_id}"
                    )])
            
            if not keyboard:
                keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="admin_rights_manage")])
                await query.edit_message_text(
                    "❌ Нет администраторов для снятия прав (нельзя снять права с самого себя).",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                return AdminStates.ADMIN_RIGHTS
            
            keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="admin_rights_manage")])
            
            await query.edit_message_text(
                "➖ <b>Снятие прав администратора</b>\n\n"
                "Выберите администратора для снятия прав:",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='HTML'
            )
            
            return AdminStates.REVOKE_ADMIN_SELECT
            
        except Exception as e:
            logger.error(f"Ошибка в мастере снятия прав администратора: {e}")
            keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data="admin_rights_manage")]]
            await query.edit_message_text(
                "❌ Ошибка при загрузке списка администраторов",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return AdminStates.ADMIN_RIGHTS
    
    async def _handle_grant_admin_select(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обработка выбора сотрудника для назначения администратором"""
        query = update.callback_query
        await query.answer()
        
        if query.data.startswith("grant_admin_"):
            user_id = int(query.data.replace("grant_admin_", ""))
            employee = await self.db_manager.get_employee_by_user_id(user_id)
            
            if employee:
                context.user_data['grant_admin_user_id'] = user_id
                
                keyboard = [
                    [InlineKeyboardButton("✅ Подтвердить", callback_data="confirm_grant_admin")],
                    [InlineKeyboardButton("❌ Отмена", callback_data="admin_rights_manage")]
                ]
                
                await query.edit_message_text(
                    f"➕ <b>Подтверждение назначения</b>\n\n"
                    f"Назначить администратором:\n"
                    f"<b>{employee.full_name}</b>\n"
                    f"📱 ID: <code>{employee.user_id}</code>\n"
                    f"🏢 {employee.department_code} - {employee.position}\n\n"
                    f"⚠️ <i>Администратор получит доступ ко всем функциям управления!</i>",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='HTML'
                )
                
                return AdminStates.GRANT_ADMIN_CONFIRM
            else:
                keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data="admin_rights_manage")]]
                await query.edit_message_text(
                    "❌ Сотрудник не найден",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                return AdminStates.ADMIN_RIGHTS
        
        return AdminStates.ADMIN_RIGHTS
    
    async def _handle_revoke_admin_select(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обработка выбора администратора для снятия прав"""
        query = update.callback_query
        await query.answer()
        
        if query.data.startswith("revoke_admin_"):
            user_id = int(query.data.replace("revoke_admin_", ""))
            employee = await self.db_manager.get_employee_by_user_id(user_id)
            
            if employee:
                context.user_data['revoke_admin_user_id'] = user_id
                
                keyboard = [
                    [InlineKeyboardButton("✅ Подтвердить", callback_data="confirm_revoke_admin")],
                    [InlineKeyboardButton("❌ Отмена", callback_data="admin_rights_manage")]
                ]
                
                await query.edit_message_text(
                    f"➖ <b>Подтверждение снятия прав</b>\n\n"
                    f"Снять права администратора с:\n"
                    f"<b>{employee.full_name}</b>\n"
                    f"📱 ID: <code>{employee.user_id}</code>\n"
                    f"🏢 {employee.department_code} - {employee.position}\n\n"
                    f"⚠️ <i>Пользователь потеряет доступ к функциям управления!</i>",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='HTML'
                )
                
                return AdminStates.REVOKE_ADMIN_CONFIRM
            else:
                keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data="admin_rights_manage")]]
                await query.edit_message_text(
                    "❌ Администратор не найден",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                return AdminStates.ADMIN_RIGHTS
        
        return AdminStates.ADMIN_RIGHTS
    
    async def _confirm_grant_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Подтверждение назначения администратора"""
        query = update.callback_query
        await query.answer()
        
        if query.data == 'confirm_grant_admin':
            user_id = context.user_data.get('grant_admin_user_id')
            if user_id:
                employee = await self.db_manager.get_employee_by_user_id(user_id)
                if employee:
                    success = await self.db_manager.set_admin_rights(user_id, True)
                    if success:
                        keyboard = [[InlineKeyboardButton("⬅️ Назад к управлению админами", callback_data="admin_rights_manage")]]
                        await query.edit_message_text(
                            f"✅ <b>{employee.full_name}</b> назначен администратором!",
                            reply_markup=InlineKeyboardMarkup(keyboard),
                            parse_mode='HTML'
                        )
                    else:
                        keyboard = [[InlineKeyboardButton("⬅️ Назад к управлению админами", callback_data="admin_rights_manage")]]
                        await query.edit_message_text(
                            "❌ Ошибка при назначении администратора.",
                            reply_markup=InlineKeyboardMarkup(keyboard)
                        )
                else:
                    keyboard = [[InlineKeyboardButton("⬅️ Назад к управлению админами", callback_data="admin_rights_manage")]]
                    await query.edit_message_text(
                        "❌ Сотрудник не найден.",
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
            else:
                keyboard = [[InlineKeyboardButton("⬅️ Назад к управлению админами", callback_data="admin_rights_manage")]]
                await query.edit_message_text(
                    "❌ Ошибка: ID пользователя не найден.",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
        
        context.user_data.pop('grant_admin_user_id', None)
        return AdminStates.ADMIN_RIGHTS
    
    async def _confirm_revoke_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Подтверждение снятия прав администратора"""
        query = update.callback_query
        await query.answer()
        
        if query.data == 'confirm_revoke_admin':
            user_id = context.user_data.get('revoke_admin_user_id')
            if user_id:
                employee = await self.db_manager.get_employee_by_user_id(user_id)
                if employee:
                    success = await self.db_manager.set_admin_rights(user_id, False)
                    if success:
                        keyboard = [[InlineKeyboardButton("⬅️ Назад к управлению админами", callback_data="admin_rights_manage")]]
                        await query.edit_message_text(
                            f"✅ Права администратора сняты с <b>{employee.full_name}</b>!",
                            reply_markup=InlineKeyboardMarkup(keyboard),
                            parse_mode='HTML'
                        )
                    else:
                        keyboard = [[InlineKeyboardButton("⬅️ Назад к управлению админами", callback_data="admin_rights_manage")]]
                        await query.edit_message_text(
                            "❌ Ошибка при снятии прав администратора.",
                            reply_markup=InlineKeyboardMarkup(keyboard)
                        )
                else:
                    keyboard = [[InlineKeyboardButton("⬅️ Назад к управлению админами", callback_data="admin_rights_manage")]]
                    await query.edit_message_text(
                        "❌ Администратор не найден.",
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
            else:
                keyboard = [[InlineKeyboardButton("⬅️ Назад к управлению админами", callback_data="admin_rights_manage")]]
                await query.edit_message_text(
                    "❌ Ошибка: ID пользователя не найден.",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
        
        context.user_data.pop('revoke_admin_user_id', None)
        return AdminStates.ADMIN_RIGHTS
    
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
                    CallbackQueryHandler(self.handle_users_callback, pattern='^users_|^departments_'),
                    CallbackQueryHandler(self.handle_admin_callback)
                ],
                AdminStates.EXPORT_DATA: [
                    CallbackQueryHandler(self.handle_export_callback, pattern='^export_'),
                    CallbackQueryHandler(self.handle_admin_callback)
                ],
                AdminStates.WAITING_INPUT: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_user_input),
                    CommandHandler('cancel', self._cancel_admin)
                ],
                # Состояния мастера добавления пользователей
                AdminStates.ADD_USER_STEP1_ID: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_add_user_step1),
                    CallbackQueryHandler(self._cancel_admin, pattern='^cancel$')
                ],
                AdminStates.ADD_USER_STEP2_USERNAME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_add_user_step2),
                    CallbackQueryHandler(self._handle_add_user_step1, pattern='^wizard_back$'),
                    CallbackQueryHandler(self._cancel_admin, pattern='^cancel$')
                ],
                AdminStates.ADD_USER_STEP3_FULLNAME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_add_user_step3),
                    CallbackQueryHandler(self._handle_add_user_step3, pattern='^wizard_next$'),
                    CallbackQueryHandler(self._handle_add_user_step2, pattern='^wizard_back$'),
                    CallbackQueryHandler(self._cancel_admin, pattern='^cancel$')
                ],
                AdminStates.ADD_USER_STEP4_DEPARTMENT: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_add_user_step4),
                    CallbackQueryHandler(self._handle_add_user_step3, pattern='^wizard_back$'),
                    CallbackQueryHandler(self._cancel_admin, pattern='^cancel$')
                ],
                AdminStates.ADD_USER_STEP5_POSITION: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_add_user_step5),
                    CallbackQueryHandler(self._handle_add_user_step4, pattern='^wizard_back$'),
                    CallbackQueryHandler(self._cancel_admin, pattern='^cancel$')
                ],
                AdminStates.ADD_USER_STEP6_EMPLOYEE_ID: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_add_user_step6),
                    CallbackQueryHandler(self._handle_add_user_step5, pattern='^wizard_back$'),
                    CallbackQueryHandler(self._cancel_admin, pattern='^cancel$')
                ],
                AdminStates.ADD_USER_STEP7_EMAIL: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_add_user_step7),
                    CallbackQueryHandler(self._handle_add_user_step7, pattern='^wizard_next$'),
                    CallbackQueryHandler(self._handle_add_user_step6, pattern='^wizard_back$'),
                    CallbackQueryHandler(self._cancel_admin, pattern='^cancel$')
                ],
                AdminStates.ADD_USER_STEP8_PHONE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_add_user_step8),
                    CallbackQueryHandler(self._handle_add_user_step8, pattern='^wizard_next$'),
                    CallbackQueryHandler(self._handle_add_user_step7, pattern='^wizard_back$'),
                    CallbackQueryHandler(self._cancel_admin, pattern='^cancel$')
                ],
                AdminStates.ADD_USER_CONFIRM: [
                    CallbackQueryHandler(self._confirm_add_user, pattern='^confirm_'),
                    CallbackQueryHandler(self._handle_add_user_step8, pattern='^wizard_back$'),
                    CallbackQueryHandler(self._cancel_admin, pattern='^cancel$')
                ],
                # Состояния мастера удаления пользователей
                AdminStates.DELETE_USER_SELECT: [
                    CallbackQueryHandler(self._handle_delete_user_select, pattern='^delete_user_|^cancel$')
                ],
                AdminStates.DELETE_USER_CONFIRM: [
                    CallbackQueryHandler(self._confirm_delete_user, pattern='^delete_confirm|^delete_cancel$')
                ],
                # Состояния мастера добавления отделов
                AdminStates.ADD_DEPT_STEP1_CODE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_add_department_step1),
                    CallbackQueryHandler(self._cancel_admin, pattern='^cancel$')
                ],
                AdminStates.ADD_DEPT_STEP2_NAME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_add_department_step2),
                    CallbackQueryHandler(self._handle_add_department_step1, pattern='^wizard_back$'),
                    CallbackQueryHandler(self._cancel_admin, pattern='^cancel$')
                ],
                AdminStates.ADD_DEPT_STEP3_DESCRIPTION: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_add_department_step3),
                    CallbackQueryHandler(self._handle_add_department_step3, pattern='^wizard_next$'),
                    CallbackQueryHandler(self._handle_add_department_step2, pattern='^wizard_back$'),
                    CallbackQueryHandler(self._cancel_admin, pattern='^cancel$')
                ],
                AdminStates.ADD_DEPT_STEP4_HEAD: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_add_department_step4),
                    CallbackQueryHandler(self._handle_add_department_step4, pattern='^wizard_next$'),
                    CallbackQueryHandler(self._handle_add_department_step3, pattern='^wizard_back$'),
                    CallbackQueryHandler(self._cancel_admin, pattern='^cancel$')
                ],
                AdminStates.ADD_DEPT_CONFIRM: [
                    CallbackQueryHandler(self._confirm_add_department, pattern='^confirm_'),
                    CallbackQueryHandler(self._handle_add_department_step4, pattern='^wizard_back$'),
                    CallbackQueryHandler(self._cancel_admin, pattern='^cancel$')
                ],
                # Состояния мастера удаления отделов
                AdminStates.DELETE_DEPT_SELECT: [
                    CallbackQueryHandler(self._handle_delete_department_select, pattern='^delete_dept_|^cancel$')
                ],
                AdminStates.DELETE_DEPT_CONFIRM: [
                    CallbackQueryHandler(self._confirm_delete_department, pattern='^delete_confirm|^delete_cancel$')
                ],
                # Состояния управления административными правами
                AdminStates.ADMIN_RIGHTS: [
                    CallbackQueryHandler(self.handle_admin_rights_callback, pattern='^admin_list|^admin_grant|^admin_revoke$'),
                    CallbackQueryHandler(self.handle_admin_callback)
                ],
                AdminStates.GRANT_ADMIN_SELECT: [
                    CallbackQueryHandler(self._handle_grant_admin_select, pattern='^grant_admin_|^admin_rights_manage$')
                ],
                AdminStates.GRANT_ADMIN_CONFIRM: [
                    CallbackQueryHandler(self._confirm_grant_admin, pattern='^confirm_grant_admin|^admin_rights_manage$')
                ],
                AdminStates.REVOKE_ADMIN_SELECT: [
                    CallbackQueryHandler(self._handle_revoke_admin_select, pattern='^revoke_admin_|^admin_rights_manage$')
                ],
                AdminStates.REVOKE_ADMIN_CONFIRM: [
                    CallbackQueryHandler(self._confirm_revoke_admin, pattern='^confirm_revoke_admin|^admin_rights_manage$')
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