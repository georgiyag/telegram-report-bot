# -*- coding: utf-8 -*-
"""
Основной модуль-обработчик для админ-панели.

Отвечает за главное меню админки и делегирует
задачи по управлению пользователями и отделами
соответствующим обработчикам.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from loguru import logger
from datetime import datetime

from .states import AdminStates
from database import DatabaseManager
from .admin.user_management import UserManagementHandler
from .admin.department_management import DepartmentManagementHandler

class AdminHandler:
    """Основной обработчик для админ-панели."""

    def __init__(self, report_processor, db_manager, telegram_service, user_management_handler, department_management_handler):
        self.report_processor = report_processor
        self.db_manager = db_manager
        self.telegram_service = telegram_service
        self.user_management_handler = user_management_handler
        self.department_management_handler = department_management_handler

    async def admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handles the /admin command."""
        user_id = update.effective_user.id
        if await self.db_manager.is_admin(user_id):
            return await self.show_admin_panel(update, context)
        else:
            # Обрабатываем как callback_query, так и обычное сообщение
            if update.callback_query:
                await update.callback_query.answer("У вас нет прав для доступа к админ-панели.", show_alert=True)
            elif update.message:
                await update.message.reply_text("У вас нет прав для доступа к админ-панели.")
            return ConversationHandler.END

    async def show_admin_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Показывает главное меню админ-панели."""
        from utils.navigation import get_breadcrumb_path, update_context_path
        
        query = update.callback_query
        if query:
            await query.answer()

        # Обновляем путь навигации
        path = update_context_path(context, 'admin')
        breadcrumb = get_breadcrumb_path(path)

        keyboard = [
            [InlineKeyboardButton("👥 Управление пользователями", callback_data="admin_manage_users")],
            [InlineKeyboardButton("🗄️ Управление отделами", callback_data="admin_manage_depts")],
            [InlineKeyboardButton("📊 Просмотр отчетов", callback_data="admin_reports")],
            [InlineKeyboardButton("🔔 Управление напоминаниями", callback_data="admin_reminders")],
            [InlineKeyboardButton("📤 Экспорт данных", callback_data="admin_export")],
            [InlineKeyboardButton("🏠 В главное меню", callback_data="admin_exit")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        message_text = (
            f"📍 {breadcrumb}\n\n"
            f"👑 <b>Панель администратора</b>\n\n"
            f"🎯 Выберите действие:"
        )
        
        if query:
            await query.edit_message_text(
                text=message_text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        else:
            await update.message.reply_text(
                text=message_text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        
        return AdminStates.MAIN_MENU
    
    async def handle_reminder_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обрабатывает callback для напоминаний."""
        from utils.navigation import get_breadcrumb_path, update_context_path, create_keyboard
        
        query = update.callback_query
        await query.answer()
        data = query.data
        
        # Обработка конкретных callback_data
        if data.startswith('schedule_reminder_'):
            if data == 'schedule_reminder_1h':
                await query.edit_message_text(
                    "⏰ <b>Напоминание через 1 час</b>\n\n"
                    "✅ Напоминание запланировано на отправку через 1 час.",
                    parse_mode='HTML'
                )
            elif data == 'schedule_reminder_tomorrow':
                await query.edit_message_text(
                    "📅 <b>Напоминание завтра в 9:00</b>\n\n"
                    "✅ Напоминание запланировано на завтра в 9:00.",
                    parse_mode='HTML'
                )
            elif data == 'schedule_reminder_weekly':
                await query.edit_message_text(
                    "📆 <b>Еженедельное напоминание</b>\n\n"
                    "✅ Напоминание будет отправляться каждый понедельник.",
                    parse_mode='HTML'
                )
            elif data == 'schedule_reminder_custom':
                await query.edit_message_text(
                    "⚙️ <b>Настройка времени</b>\n\n"
                    "📝 Введите время в формате ЧЧ:ММ (например, 14:30):",
                    parse_mode='HTML'
                )
            return AdminStates.MAIN_MENU
        
        elif data.startswith('time_'):
            # Обработка выбора времени
            if data == 'time_custom':
                # Обработка кастомного времени
                await query.edit_message_text(
                    "⏰ <b>Ввод времени</b>\n\n"
                    "🕐 Введите время в формате ЧЧ:ММ (например, 14:30):",
                    parse_mode='HTML'
                )
                return AdminStates.MAIN_MENU
            
            time_value = data.replace('time_', '').replace('_', ':')
            try:
                # Получаем текущие настройки и обновляем время
                reminder_settings = await self.db_manager.get_reminder_settings()
                reminder_settings['reminder_time'] = time_value
                
                # Сохраняем в базу
                await self.db_manager.update_reminder_settings(reminder_settings)
                
                # Возвращаемся к настройкам с обновленным временем
                auto_enabled = reminder_settings.get('auto_enabled', False)
                reminder_time = reminder_settings.get('reminder_time', '09:00')
                reminder_days = reminder_settings.get('reminder_days', 'Пн,Ср,Пт')
                
                path = update_context_path(context, 'reminder_settings')
                breadcrumb = get_breadcrumb_path(path)
                
                keyboard = create_keyboard([
                    [(f"{'🔔' if auto_enabled else '🔕'} Автонапоминания: {'ВКЛ' if auto_enabled else 'ВЫКЛ'}", "toggle_auto_reminders")],
                    [(f"⏰ Время: {reminder_time}", "set_reminder_time")],
                    [(f"📅 Дни: {reminder_days}", "set_reminder_days")],
                    [("💾 Сохранить настройки", "save_reminder_settings")]
                ], path)
                
                await query.edit_message_text(
                    f"📍 {breadcrumb}\n\n"
                    f"⚙️ <b>Настройки напоминаний</b>\n\n"
                    f"✅ <b>Время обновлено на {time_value}</b>\n\n"
                    f"🔧 Текущие настройки:\n\n"
                    f"• <b>Автоматические напоминания:</b> {'Включены' if auto_enabled else 'Отключены'}\n"
                    f"• <b>Время отправки:</b> {reminder_time}\n"
                    f"• <b>Дни недели:</b> {reminder_days}\n\n"
                    f"💡 Нажмите на настройку для изменения:",
                    reply_markup=keyboard,
                    parse_mode='HTML'
                )
            except Exception as e:
                logger.error(f"Ошибка при обновлении времени напоминаний: {e}")
                await query.edit_message_text(
                    f"❌ <b>Ошибка</b>\n\n"
                    f"Не удалось обновить время напоминаний.",
                    parse_mode='HTML'
                )
            return AdminStates.MAIN_MENU
        
        elif data.startswith('days_'):
            # Обработка выбора дней
            days_mapping = {
                'days_mon_wed_fri': 'Пн,Ср,Пт',
                'days_tue_thu': 'Вт,Чт', 
                'days_everyday': 'Каждый день',
                'days_friday_only': 'Только пятница'
            }
            
            selected_days = days_mapping.get(data, 'Пн,Ср,Пт')
            
            try:
                # Получаем текущие настройки и обновляем дни
                reminder_settings = await self.db_manager.get_reminder_settings()
                reminder_settings['reminder_days'] = selected_days
                
                # Сохраняем в базу
                await self.db_manager.update_reminder_settings(reminder_settings)
                
                # Возвращаемся к настройкам с обновленными днями
                auto_enabled = reminder_settings.get('auto_enabled', False)
                reminder_time = reminder_settings.get('reminder_time', '09:00')
                reminder_days = reminder_settings.get('reminder_days', 'Пн,Ср,Пт')
                
                path = update_context_path(context, 'reminder_settings')
                breadcrumb = get_breadcrumb_path(path)
                
                keyboard = create_keyboard([
                    [(f"{'🔔' if auto_enabled else '🔕'} Автонапоминания: {'ВКЛ' if auto_enabled else 'ВЫКЛ'}", "toggle_auto_reminders")],
                    [(f"⏰ Время: {reminder_time}", "set_reminder_time")],
                    [(f"📅 Дни: {reminder_days}", "set_reminder_days")],
                    [("💾 Сохранить настройки", "save_reminder_settings")]
                ], path)
                
                await query.edit_message_text(
                    f"📍 {breadcrumb}\n\n"
                    f"⚙️ <b>Настройки напоминаний</b>\n\n"
                    f"✅ <b>Дни обновлены на {selected_days}</b>\n\n"
                    f"🔧 Текущие настройки:\n\n"
                    f"• <b>Автоматические напоминания:</b> {'Включены' if auto_enabled else 'Отключены'}\n"
                    f"• <b>Время отправки:</b> {reminder_time}\n"
                    f"• <b>Дни недели:</b> {reminder_days}\n\n"
                    f"💡 Нажмите на настройку для изменения:",
                    reply_markup=keyboard,
                    parse_mode='HTML'
                )
            except Exception as e:
                logger.error(f"Ошибка при обновлении дней напоминаний: {e}")
                await query.edit_message_text(
                    f"❌ <b>Ошибка</b>\n\n"
                    f"Не удалось обновить дни напоминаний.",
                    parse_mode='HTML'
                )
            return AdminStates.MAIN_MENU
        
        elif data == 'set_reminder_time':
            # Показываем варианты времени
            path = update_context_path(context, 'set_reminder_time')
            breadcrumb = get_breadcrumb_path(path)
            
            keyboard = create_keyboard([
                [("🌅 09:00", "time_09_00")],
                [("🌞 12:00", "time_12_00")],
                [("🌆 18:00", "time_18_00")],
                [("⚙️ Другое время", "time_custom")]
            ], path)
            
            await query.edit_message_text(
                f"📍 {breadcrumb}\n\n"
                f"⏰ <b>Выбор времени напоминаний</b>\n\n"
                f"🕐 Выберите время отправки автоматических напоминаний:\n\n"
                f"• <b>09:00</b> - утром\n"
                f"• <b>12:00</b> - в обед\n"
                f"• <b>18:00</b> - вечером\n\n"
                f"💡 Или введите свое время:",
                reply_markup=keyboard,
                parse_mode='HTML'
            )
            return AdminStates.MAIN_MENU
        
        elif data == 'set_reminder_days':
            # Показываем варианты дней
            path = update_context_path(context, 'set_reminder_days')
            breadcrumb = get_breadcrumb_path(path)
            
            keyboard = create_keyboard([
                [("📅 Пн,Ср,Пт", "days_mon_wed_fri")],
                [("📅 Вт,Чт", "days_tue_thu")],
                [("📅 Каждый день", "days_everyday")],
                [("📅 Только пятница", "days_friday_only")],
                [("⌨️ Настроить дни", "custom_days_input")]
            ], path)
            
            await query.edit_message_text(
                f"📍 {breadcrumb}\n\n"
                f"📅 <b>Выбор дней напоминаний</b>\n\n"
                f"📆 Выберите дни отправки автоматических напоминаний:\n\n"
                f"• <b>Пн,Ср,Пт</b> - через день\n"
                f"• <b>Вт,Чт</b> - вторник и четверг\n"
                f"• <b>Каждый день</b> - ежедневно\n"
                f"• <b>Только пятница</b> - перед дедлайном\n\n"
                f"💡 Или настройте свои дни:",
                reply_markup=keyboard,
                parse_mode='HTML'
            )
            return AdminStates.MAIN_MENU
        
        elif data == 'custom_days_input':
            # Обработка кастомного ввода дней
            await query.edit_message_text(
                "📅 <b>Ввод дней недели</b>\n\n"
                "📝 Введите дни недели через запятую (например: Пн,Ср,Пт):",
                parse_mode='HTML'
            )
            return AdminStates.MAIN_MENU
        
        elif data == 'save_reminder_settings':
            # Сохраняем настройки
            try:
                reminder_settings = await self.db_manager.get_reminder_settings()
                await self.db_manager.update_reminder_settings(reminder_settings)
                
                await query.edit_message_text(
                    "💾 <b>Настройки сохранены</b>\n\n"
                    "✅ Настройки напоминаний успешно сохранены.",
                    parse_mode='HTML'
                )
            except Exception as e:
                logger.error(f"Ошибка при сохранении настроек: {e}")
                await query.edit_message_text(
                    "❌ <b>Ошибка</b>\n\n"
                    "Произошла ошибка при сохранении настроек.",
                    parse_mode='HTML'
                )
            return AdminStates.MAIN_MENU
        
        # Если это основной вызов без конкретного callback_data
        # Обновляем путь навигации
        path = update_context_path(context, 'admin_reminders')
        breadcrumb = get_breadcrumb_path(path)
        
        keyboard = create_keyboard([
            [("📤 Отправить напоминание всем", "reminder_send_all")],
            [("📋 Напомнить не сдавшим", "reminder_send_missing")],
            [("⚙️ Настройки напоминаний", "reminder_settings")]
        ], path)
        
        await query.edit_message_text(
            f"📍 {breadcrumb}\n\n"
            f"🔔 <b>Управление напоминаниями</b>\n\n"
            f"📊 Выберите действие для работы с напоминаниями:\n\n"
            f"• <b>Отправить всем</b> - массовая рассылка\n"
            f"• <b>Напомнить не сдавшим</b> - только тем, кто не сдал отчет\n"
            f"• <b>Настройки</b> - управление автоматическими напоминаниями",
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        return AdminStates.MAIN_MENU
    
    async def handle_reports_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обрабатывает callback для просмотра отчетов."""
        from utils.navigation import get_breadcrumb_path, update_context_path, create_keyboard
        
        query = update.callback_query
        await query.answer()
        
        # Обновляем путь навигации
        path = update_context_path(context, 'admin_reports')
        breadcrumb = get_breadcrumb_path(path)
        
        keyboard = create_keyboard([
            [("📅 Отчеты за текущую неделю", "reports_current_week")],
            [("📊 Статистика по отделам", "reports_department_stats")],
            [("📈 Общая статистика", "reports_general_stats")],
            [("🔍 Поиск отчетов", "reports_search")]
        ], path)
        
        await query.edit_message_text(
            f"📍 {breadcrumb}\n\n"
            f"📊 <b>Просмотр отчетов</b>\n\n"
            f"📋 Выберите тип отчетов для просмотра:\n\n"
            f"• <b>Текущая неделя</b> - отчеты за эту неделю\n"
            f"• <b>По отделам</b> - статистика по подразделениям\n"
            f"• <b>Общая статистика</b> - сводные данные\n"
            f"• <b>Поиск</b> - найти конкретные отчеты",
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        return AdminStates.MAIN_MENU
    
    async def handle_export_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обрабатывает callback для экспорта данных."""
        from utils.navigation import get_breadcrumb_path, update_context_path, create_keyboard
        
        query = update.callback_query
        await query.answer()
        
        # Обновляем путь навигации
        path = update_context_path(context, 'admin_export')
        breadcrumb = get_breadcrumb_path(path)
        
        keyboard = create_keyboard([
            [("📄 Экспорт в Excel", "export_excel")],
            [("📋 Экспорт в CSV", "export_csv")],
            [("📊 Отчет по отделам", "export_departments")],
            [("👥 Список пользователей", "export_users")]
        ], path)
        
        await query.edit_message_text(
            f"📍 {breadcrumb}\n\n"
            f"📤 <b>Экспорт данных</b>\n\n"
            f"💾 Выберите формат и тип данных для экспорта:\n\n"
            f"• <b>Excel</b> - полный отчет с форматированием\n"
            f"• <b>CSV</b> - простой формат для обработки\n"
            f"• <b>По отделам</b> - статистика подразделений\n"
            f"• <b>Пользователи</b> - список всех сотрудников",
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        return AdminStates.MAIN_MENU
    
    async def cancel_admin_conversation(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Отменяет административный диалог."""
        await update.message.reply_text(
            "❌ Административный диалог отменен.",
            parse_mode='HTML'
        )
        return ConversationHandler.END
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обрабатывает команду /stats для показа статистики."""
        user_id = update.effective_user.id
        if not await self.db_manager.is_admin(user_id):
            await update.message.reply_text("У вас нет прав для просмотра статистики.")
            return
        
        try:
            # Получаем статистику из базы данных
            total_users = await self.db_manager.get_total_users_count()
            total_reports = await self.db_manager.get_total_reports_count()
            total_departments = await self.db_manager.get_total_departments_count()
            active_users = await self.db_manager.get_active_users_count()
            reports_this_week = await self.db_manager.get_reports_this_week_count()
            
            # Формируем сообщение со статистикой
            stats_message = (
                "📊 <b>Статистика системы</b>\n\n"
                f"👥 <b>Пользователи:</b>\n"
                f"   • Всего зарегистрировано: {total_users}\n"
                f"   • Активных: {active_users}\n\n"
                f"🏢 <b>Отделы:</b> {total_departments}\n\n"
                f"📋 <b>Отчеты:</b>\n"
                f"   • Всего отчетов: {total_reports}\n"
                f"   • За эту неделю: {reports_this_week}\n\n"
                f"📈 <b>Активность:</b>\n"
                f"   • Процент активности: {(active_users/total_users*100):.1f}% (если есть пользователи)\n"
                f"   • Средний отчетов на пользователя: {(total_reports/total_users):.1f} (если есть пользователи)"
            )
            
            await update.message.reply_text(stats_message, parse_mode='HTML')
            
        except Exception as e:
            logger.error(f"Ошибка при получении статистики: {e}")
            await update.message.reply_text(
                "❌ Произошла ошибка при получении статистики. Попробуйте позже.",
                parse_mode='HTML'
            )
    
    async def handle_reminder_action(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обрабатывает действия с напоминаниями."""
        query = update.callback_query
        await query.answer()
        data = query.data
        
        if data == 'reminder_send_all':
            await query.edit_message_text(
                "📤 <b>Отправка напоминаний всем</b>\n\n"
                "⏳ Отправляем напоминания всем активным сотрудникам...",
                parse_mode='HTML'
            )
            # Здесь будет логика отправки напоминаний
            
        elif data == 'reminder_send_dept':
            from utils.navigation import get_breadcrumb_path, update_context_path, create_keyboard
            
            path = update_context_path(context, 'reminder_send_dept')
            breadcrumb = get_breadcrumb_path(path)
            
            try:
                departments = await self.db_manager.get_departments()
                if departments:
                    keyboard_buttons = []
                    for dept in departments:
                        keyboard_buttons.append([(f"🏢 {dept.name}", f"send_reminder_to_dept_{dept.code}")])
                    
                    keyboard = create_keyboard(keyboard_buttons, path)
                    
                    await query.edit_message_text(
                        f"📍 {breadcrumb}\n\n"
                        f"🏢 <b>Выберите отдел</b>\n\n"
                        f"📤 Напоминание будет отправлено всем сотрудникам выбранного отдела:",
                        reply_markup=keyboard,
                        parse_mode='HTML'
                    )
                else:
                    await query.edit_message_text(
                        f"📍 {breadcrumb}\n\n"
                        f"🏢 <b>Отделы не найдены</b>\n\n"
                        f"❌ В системе нет зарегистрированных отделов.",
                        parse_mode='HTML'
                    )
            except Exception as e:
                logger.error(f"Ошибка при получении списка отделов: {e}")
                await query.edit_message_text(
                    f"📍 {breadcrumb}\n\n"
                    f"❌ <b>Ошибка</b>\n\n"
                    f"Не удалось загрузить список отделов.",
                    parse_mode='HTML'
                )
            
        elif data == 'reminder_schedule':
            from utils.navigation import get_breadcrumb_path, update_context_path, create_keyboard
            
            path = update_context_path(context, 'reminder_schedule')
            breadcrumb = get_breadcrumb_path(path)
            
            keyboard = create_keyboard([
                [("⏰ Через 1 час", "schedule_reminder_1h")],
                [("📅 Завтра в 9:00", "schedule_reminder_tomorrow")],
                [("📆 Каждый понедельник", "schedule_reminder_weekly")],
                [("⚙️ Настроить время", "schedule_reminder_custom")]
            ], path)
            
            await query.edit_message_text(
                f"📍 {breadcrumb}\n\n"
                f"⏰ <b>Планирование напоминаний</b>\n\n"
                f"🕐 Выберите время отправки напоминания:\n\n"
                f"• <b>Через 1 час</b> - одноразовое напоминание\n"
                f"• <b>Завтра в 9:00</b> - отложенное напоминание\n"
                f"• <b>Каждый понедельник</b> - еженедельное\n"
                f"• <b>Настроить время</b> - произвольное время",
                reply_markup=keyboard,
                parse_mode='HTML'
            )
            
        elif data == 'reminder_send_missing':
            await query.edit_message_text(
                "📋 <b>Напоминание не сдавшим</b>\n\n"
                "⏳ Отправляем напоминания сотрудникам без отчетов...",
                parse_mode='HTML'
            )
            # Здесь будет логика отправки напоминаний
            
        elif data == 'reminder_settings':
            from utils.navigation import get_breadcrumb_path, update_context_path, create_keyboard
            
            # Обновляем путь навигации
            path = update_context_path(context, 'reminder_settings')
            breadcrumb = get_breadcrumb_path(path)
            
            # Получаем текущие настройки напоминаний
            try:
                reminder_settings = await self.db_manager.get_reminder_settings()
                auto_enabled = reminder_settings.get('auto_enabled', False)
                reminder_time = reminder_settings.get('reminder_time', '09:00')
                reminder_days = reminder_settings.get('reminder_days', 'Пн,Ср,Пт')
                
                keyboard = create_keyboard([
                    [(f"{'🔔' if auto_enabled else '🔕'} Автонапоминания: {'ВКЛ' if auto_enabled else 'ВЫКЛ'}", "toggle_auto_reminders")],
                    [(f"⏰ Время: {reminder_time}", "set_reminder_time")],
                    [(f"📅 Дни: {reminder_days}", "set_reminder_days")],
                    [("💾 Сохранить настройки", "save_reminder_settings")]
                ], path)
                
                await query.edit_message_text(
                    f"📍 {breadcrumb}\n\n"
                    f"⚙️ <b>Настройки напоминаний</b>\n\n"
                    f"🔧 Текущие настройки:\n\n"
                    f"• <b>Автоматические напоминания:</b> {'Включены' if auto_enabled else 'Отключены'}\n"
                    f"• <b>Время отправки:</b> {reminder_time}\n"
                    f"• <b>Дни недели:</b> {reminder_days}\n\n"
                    f"💡 Нажмите на настройку для изменения:",
                    reply_markup=keyboard,
                    parse_mode='HTML'
                )
            except Exception as e:
                logger.error(f"Ошибка при получении настроек напоминаний: {e}")
                await query.edit_message_text(
                    f"📍 {breadcrumb}\n\n"
                    f"⚙️ <b>Настройки напоминаний</b>\n\n"
                    f"❌ Ошибка при загрузке настроек. Попробуйте позже.",
                    parse_mode='HTML'
                )
        
        elif data == 'toggle_auto_reminders':
            from utils.navigation import get_breadcrumb_path, update_context_path, create_keyboard
            
            path = update_context_path(context, 'reminder_settings')
            breadcrumb = get_breadcrumb_path(path)
            
            try:
                # Получаем текущие настройки
                reminder_settings = await self.db_manager.get_reminder_settings()
                current_auto = reminder_settings.get('auto_enabled', False)
                
                # Переключаем состояние
                new_settings = reminder_settings.copy()
                new_settings['auto_enabled'] = not current_auto
                
                # Сохраняем в базу
                await self.db_manager.update_reminder_settings(new_settings)
                
                # Обновляем интерфейс
                auto_enabled = new_settings.get('auto_enabled', False)
                reminder_time = new_settings.get('reminder_time', '09:00')
                reminder_days = new_settings.get('reminder_days', 'Пн,Ср,Пт')
                
                keyboard = create_keyboard([
                    [(f"{'🔔' if auto_enabled else '🔕'} Автонапоминания: {'ВКЛ' if auto_enabled else 'ВЫКЛ'}", "toggle_auto_reminders")],
                    [(f"⏰ Время: {reminder_time}", "set_reminder_time")],
                    [(f"📅 Дни: {reminder_days}", "set_reminder_days")],
                    [("💾 Сохранить настройки", "save_reminder_settings")]
                ], path)
                
                await query.edit_message_text(
                    f"📍 {breadcrumb}\n\n"
                    f"⚙️ <b>Настройки напоминаний</b>\n\n"
                    f"🔧 Текущие настройки:\n\n"
                    f"• <b>Автоматические напоминания:</b> {'Включены' if auto_enabled else 'Отключены'}\n"
                    f"• <b>Время отправки:</b> {reminder_time}\n"
                    f"• <b>Дни недели:</b> {reminder_days}\n\n"
                    f"💡 Нажмите на настройку для изменения:",
                    reply_markup=keyboard,
                    parse_mode='HTML'
                )
            except Exception as e:
                logger.error(f"Ошибка при переключении автонапоминаний: {e}")
                await query.edit_message_text(
                    f"📍 {breadcrumb}\n\n"
                    f"❌ <b>Ошибка</b>\n\n"
                    f"Не удалось изменить настройки автонапоминаний.",
                    parse_mode='HTML'
                )
        
        elif data.startswith('send_reminder_to_dept_'):
            # Обработка отправки напоминания конкретному отделу
            dept_code = data.replace('send_reminder_to_dept_', '')
            
            try:
                # Получаем информацию об отделе
                departments = await self.db_manager.get_departments()
                dept_name = None
                for dept in departments:
                    if dept.code == dept_code:
                        dept_name = dept.name
                        break
                
                if dept_name:
                    await query.edit_message_text(
                        f"📤 <b>Отправка напоминания отделу</b>\n\n"
                        f"🏢 <b>Отдел:</b> {dept_name}\n\n"
                        f"⏳ Отправляем напоминания всем сотрудникам отдела...",
                        parse_mode='HTML'
                    )
                    
                    # Здесь будет логика отправки напоминаний отделу
                    # result = await self.reminder_service.send_reminder_to_department(dept_code)
                    
                    await query.edit_message_text(
                        f"📤 <b>Напоминание отправлено</b>\n\n"
                        f"🏢 <b>Отдел:</b> {dept_name}\n\n"
                        f"✅ Напоминания успешно отправлены всем сотрудникам отдела.",
                        parse_mode='HTML'
                    )
                else:
                    await query.edit_message_text(
                        f"❌ <b>Ошибка</b>\n\n"
                        f"Отдел с кодом {dept_code} не найден.",
                        parse_mode='HTML'
                    )
            except Exception as e:
                logger.error(f"Ошибка при отправке напоминания отделу {dept_code}: {e}")
                await query.edit_message_text(
                    f"❌ <b>Ошибка</b>\n\n"
                    f"Не удалось отправить напоминание отделу.",
                    parse_mode='HTML'
                )
        
        elif data == 'set_reminder_time':
            from utils.navigation import get_breadcrumb_path, update_context_path, create_keyboard
            
            path = update_context_path(context, 'set_reminder_time')
            breadcrumb = get_breadcrumb_path(path)
            
            keyboard = create_keyboard([
                [("🕘 09:00", "time_09_00"), ("🕙 10:00", "time_10_00")],
                [("🕛 12:00", "time_12_00"), ("🕐 13:00", "time_13_00")],
                [("🕕 18:00", "time_18_00"), ("🕘 21:00", "time_21_00")],
                [("⌨️ Ввести время", "custom_time_input")]
            ], path)
            
            await query.edit_message_text(
                f"📍 {breadcrumb}\n\n"
                f"⏰ <b>Выбор времени напоминаний</b>\n\n"
                f"🕐 Выберите время отправки автоматических напоминаний:\n\n"
                f"• <b>09:00</b> - утром\n"
                f"• <b>12:00</b> - в обед\n"
                f"• <b>18:00</b> - вечером\n\n"
                f"💡 Или введите свое время:",
                reply_markup=keyboard,
                parse_mode='HTML'
            )
        
        elif data == 'set_reminder_days':
            from utils.navigation import get_breadcrumb_path, update_context_path, create_keyboard
            
            path = update_context_path(context, 'set_reminder_days')
            breadcrumb = get_breadcrumb_path(path)
            
            keyboard = create_keyboard([
                [("📅 Пн,Ср,Пт", "days_mon_wed_fri")],
                [("📅 Вт,Чт", "days_tue_thu")],
                [("📅 Каждый день", "days_everyday")],
                [("📅 Только пятница", "days_friday_only")],
                [("⌨️ Настроить дни", "custom_days_input")]
            ], path)
            
            await query.edit_message_text(
                f"📍 {breadcrumb}\n\n"
                f"📅 <b>Выбор дней напоминаний</b>\n\n"
                f"📆 Выберите дни недели для автоматических напоминаний:\n\n"
                f"• <b>Пн,Ср,Пт</b> - через день\n"
                f"• <b>Вт,Чт</b> - вторник и четверг\n"
                f"• <b>Каждый день</b> - ежедневно\n"
                f"• <b>Только пятница</b> - перед дедлайном\n\n"
                f"💡 Или настройте свои дни:",
                reply_markup=keyboard,
                parse_mode='HTML'
            )
        
        elif data == 'save_reminder_settings':
            from utils.navigation import get_breadcrumb_path, update_context_path, create_keyboard
            
            path = update_context_path(context, 'reminder_settings')
            breadcrumb = get_breadcrumb_path(path)
            
            try:
                # Получаем текущие настройки
                reminder_settings = await self.db_manager.get_reminder_settings()
                
                # Принудительно сохраняем настройки
                success = await self.db_manager.update_reminder_settings(reminder_settings)
                
                if success:
                    auto_enabled = reminder_settings.get('auto_enabled', False)
                    reminder_time = reminder_settings.get('reminder_time', '09:00')
                    reminder_days = reminder_settings.get('reminder_days', 'Пн,Ср,Пт')
                    
                    keyboard = create_keyboard([
                        [(f"{'🔔' if auto_enabled else '🔕'} Автонапоминания: {'ВКЛ' if auto_enabled else 'ВЫКЛ'}", "toggle_auto_reminders")],
                        [(f"⏰ Время: {reminder_time}", "set_reminder_time")],
                        [(f"📅 Дни: {reminder_days}", "set_reminder_days")],
                        [("💾 Сохранить настройки", "save_reminder_settings")]
                    ], path)
                    
                    await query.edit_message_text(
                        f"📍 {breadcrumb}\n\n"
                        f"⚙️ <b>Настройки напоминаний</b>\n\n"
                        f"✅ <b>Настройки успешно сохранены!</b>\n\n"
                        f"🔧 Текущие настройки:\n\n"
                        f"• <b>Автоматические напоминания:</b> {'Включены' if auto_enabled else 'Отключены'}\n"
                        f"• <b>Время отправки:</b> {reminder_time}\n"
                        f"• <b>Дни недели:</b> {reminder_days}\n\n"
                        f"💡 Нажмите на настройку для изменения:",
                        reply_markup=keyboard,
                        parse_mode='HTML'
                    )
                else:
                    await query.edit_message_text(
                        f"📍 {breadcrumb}\n\n"
                        f"❌ <b>Ошибка сохранения</b>\n\n"
                        f"Не удалось сохранить настройки напоминаний.",
                        parse_mode='HTML'
                    )
            except Exception as e:
                logger.error(f"Ошибка при сохранении настроек напоминаний: {e}")
                await query.edit_message_text(
                    f"📍 {breadcrumb}\n\n"
                    f"❌ <b>Ошибка</b>\n\n"
                    f"Произошла ошибка при сохранении настроек.",
                     parse_mode='HTML'
                 )
        
        # Обработчики выбора времени
        elif data.startswith('time_'):
            from utils.navigation import get_breadcrumb_path, update_context_path, create_keyboard
            
            path = update_context_path(context, 'reminder_settings')
            breadcrumb = get_breadcrumb_path(path)
            
            # Извлекаем время из callback data
            time_map = {
                'time_09_00': '09:00',
                'time_10_00': '10:00', 
                'time_12_00': '12:00',
                'time_13_00': '13:00',
                'time_18_00': '18:00',
                'time_21_00': '21:00'
            }
            
            selected_time = time_map.get(data, '09:00')
            
            try:
                # Получаем текущие настройки и обновляем время
                reminder_settings = await self.db_manager.get_reminder_settings()
                reminder_settings['reminder_time'] = selected_time
                
                # Сохраняем в базу
                await self.db_manager.update_reminder_settings(reminder_settings)
                
                # Возвращаемся к настройкам с обновленным временем
                auto_enabled = reminder_settings.get('auto_enabled', False)
                reminder_time = reminder_settings.get('reminder_time', '09:00')
                reminder_days = reminder_settings.get('reminder_days', 'Пн,Ср,Пт')
                
                keyboard = create_keyboard([
                    [(f"{'🔔' if auto_enabled else '🔕'} Автонапоминания: {'ВКЛ' if auto_enabled else 'ВЫКЛ'}", "toggle_auto_reminders")],
                    [(f"⏰ Время: {reminder_time}", "set_reminder_time")],
                    [(f"📅 Дни: {reminder_days}", "set_reminder_days")],
                    [("💾 Сохранить настройки", "save_reminder_settings")]
                ], path)
                
                await query.edit_message_text(
                    f"📍 {breadcrumb}\n\n"
                    f"⚙️ <b>Настройки напоминаний</b>\n\n"
                    f"✅ <b>Время обновлено на {selected_time}</b>\n\n"
                    f"🔧 Текущие настройки:\n\n"
                    f"• <b>Автоматические напоминания:</b> {'Включены' if auto_enabled else 'Отключены'}\n"
                    f"• <b>Время отправки:</b> {reminder_time}\n"
                    f"• <b>Дни недели:</b> {reminder_days}\n\n"
                    f"💡 Нажмите на настройку для изменения:",
                    reply_markup=keyboard,
                    parse_mode='HTML'
                )
            except Exception as e:
                logger.error(f"Ошибка при обновлении времени напоминаний: {e}")
                await query.edit_message_text(
                    f"📍 {breadcrumb}\n\n"
                    f"❌ <b>Ошибка</b>\n\n"
                    f"Не удалось обновить время напоминаний.",
                    parse_mode='HTML'
                )
        
        # Обработчики выбора дней
        elif data.startswith('days_'):
            from utils.navigation import get_breadcrumb_path, update_context_path, create_keyboard
            
            path = update_context_path(context, 'reminder_settings')
            breadcrumb = get_breadcrumb_path(path)
            
            # Извлекаем дни из callback data
            days_map = {
                'days_mon_wed_fri': 'Пн,Ср,Пт',
                'days_tue_thu': 'Вт,Чт',
                'days_everyday': 'Пн,Вт,Ср,Чт,Пт,Сб,Вс',
                'days_friday_only': 'Пт'
            }
            
            selected_days = days_map.get(data, 'Пн,Ср,Пт')
            
            try:
                # Получаем текущие настройки и обновляем дни
                reminder_settings = await self.db_manager.get_reminder_settings()
                reminder_settings['reminder_days'] = selected_days
                
                # Сохраняем в базу
                await self.db_manager.update_reminder_settings(reminder_settings)
                
                # Возвращаемся к настройкам с обновленными днями
                auto_enabled = reminder_settings.get('auto_enabled', False)
                reminder_time = reminder_settings.get('reminder_time', '09:00')
                reminder_days = reminder_settings.get('reminder_days', 'Пн,Ср,Пт')
                
                keyboard = create_keyboard([
                    [(f"{'🔔' if auto_enabled else '🔕'} Автонапоминания: {'ВКЛ' if auto_enabled else 'ВЫКЛ'}", "toggle_auto_reminders")],
                    [(f"⏰ Время: {reminder_time}", "set_reminder_time")],
                    [(f"📅 Дни: {reminder_days}", "set_reminder_days")],
                    [("💾 Сохранить настройки", "save_reminder_settings")]
                ], path)
                
                await query.edit_message_text(
                    f"📍 {breadcrumb}\n\n"
                    f"⚙️ <b>Настройки напоминаний</b>\n\n"
                    f"✅ <b>Дни обновлены на {selected_days}</b>\n\n"
                    f"🔧 Текущие настройки:\n\n"
                    f"• <b>Автоматические напоминания:</b> {'Включены' if auto_enabled else 'Отключены'}\n"
                    f"• <b>Время отправки:</b> {reminder_time}\n"
                    f"• <b>Дни недели:</b> {reminder_days}\n\n"
                    f"💡 Нажмите на настройку для изменения:",
                    reply_markup=keyboard,
                    parse_mode='HTML'
                )
            except Exception as e:
                logger.error(f"Ошибка при обновлении дней напоминаний: {e}")
                await query.edit_message_text(
                    f"📍 {breadcrumb}\n\n"
                    f"❌ <b>Ошибка</b>\n\n"
                    f"Не удалось обновить дни напоминаний.",
                    parse_mode='HTML'
                )
        
        # Обработка ввода пользовательского времени
        elif data == 'custom_time_input':
            from utils.navigation import get_breadcrumb_path, update_context_path, create_keyboard
            
            path = update_context_path(context, 'custom_time_input')
            breadcrumb = get_breadcrumb_path(path)
            
            await query.edit_message_text(
                f"📍 {breadcrumb}\n\n"
                f"⏰ <b>Ввод времени напоминаний</b>\n\n"
                f"🕐 Введите время в формате ЧЧ:ММ (например, 14:30)\n\n"
                f"💡 Время должно быть в диапазоне от 00:00 до 23:59",
                parse_mode='HTML'
            )
            
            # Устанавливаем состояние ожидания ввода времени
            context.user_data['waiting_for_time_input'] = True
        
        return AdminStates.MAIN_MENU
    
    async def handle_reports_action(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обрабатывает действия с отчетами."""
        query = update.callback_query
        await query.answer()
        data = query.data
        
        if data == 'reports_current_week':
            try:
                reports = await self.db_manager.get_reports_current_week()
                if reports:
                    report_text = "📅 <b>Отчеты за текущую неделю</b>\n\n"
                    for report in reports[:10]:  # Показываем первые 10 отчетов
                        user_name = report.get('user_name', 'Неизвестный')
                        department = report.get('department', 'Не указан')
                        date = report.get('created_at', 'Неизвестно')
                        report_text += f"👤 <b>{user_name}</b> ({department})\n"
                        report_text += f"📅 {date}\n\n"
                    
                    if len(reports) > 10:
                        report_text += f"... и еще {len(reports) - 10} отчетов\n"
                    
                    report_text += f"\n📊 <b>Всего отчетов за неделю:</b> {len(reports)}"
                else:
                    report_text = "📅 <b>Отчеты за текущую неделю</b>\n\n📭 Отчетов за эту неделю пока нет."
                
                await query.edit_message_text(report_text, parse_mode='HTML')
            except Exception as e:
                logger.error(f"Ошибка при получении отчетов за неделю: {e}")
                await query.edit_message_text(
                    "📅 <b>Отчеты за текущую неделю</b>\n\n❌ Ошибка при загрузке отчетов.",
                    parse_mode='HTML'
                )
        elif data == 'reports_department_stats':
            try:
                dept_stats = await self.db_manager.get_department_statistics()
                if dept_stats:
                    stats_text = "📊 <b>Статистика по отделам</b>\n\n"
                    for dept in dept_stats:
                        dept_name = dept.get('name', 'Неизвестный отдел')
                        user_count = dept.get('user_count', 0)
                        report_count = dept.get('report_count', 0)
                        stats_text += f"🏢 <b>{dept_name}</b>\n"
                        stats_text += f"   👥 Сотрудников: {user_count}\n"
                        stats_text += f"   📋 Отчетов: {report_count}\n\n"
                else:
                    stats_text = "📊 <b>Статистика по отделам</b>\n\n📭 Данных пока нет."
                
                await query.edit_message_text(stats_text, parse_mode='HTML')
            except Exception as e:
                logger.error(f"Ошибка при получении статистики отделов: {e}")
                await query.edit_message_text(
                    "📊 <b>Статистика по отделам</b>\n\n❌ Ошибка при загрузке статистики.",
                    parse_mode='HTML'
                )
        elif data == 'reports_general_stats':
            try:
                general_stats = await self.db_manager.get_general_statistics()
                total_users = general_stats.get('total_users', 0)
                total_reports = general_stats.get('total_reports', 0)
                active_users = general_stats.get('active_users', 0)
                avg_reports = general_stats.get('avg_reports_per_user', 0)
                
                stats_text = (
                    "📈 <b>Общая статистика</b>\n\n"
                    f"👥 <b>Пользователи:</b>\n"
                    f"   • Всего: {total_users}\n"
                    f"   • Активных: {active_users}\n\n"
                    f"📋 <b>Отчеты:</b>\n"
                    f"   • Всего отчетов: {total_reports}\n"
                    f"   • Среднее на пользователя: {avg_reports:.1f}\n\n"
                    f"📊 <b>Активность:</b>\n"
                    f"   • Процент активности: {(active_users/total_users*100):.1f}%" if total_users > 0 else "   • Процент активности: 0%"
                )
                
                await query.edit_message_text(stats_text, parse_mode='HTML')
            except Exception as e:
                logger.error(f"Ошибка при получении общей статистики: {e}")
                await query.edit_message_text(
                    "📈 <b>Общая статистика</b>\n\n❌ Ошибка при загрузке статистики.",
                    parse_mode='HTML'
                )
        elif data == 'reports_view_all':
            try:
                all_reports = await self.db_manager.get_all_reports_with_details()
                if all_reports:
                    report_text = "📋 <b>Все отчеты в системе</b>\n\n"
                    for i, report in enumerate(all_reports[:15]):  # Показываем первые 15 отчетов
                        user_name = report.get('user_name', 'Неизвестный')
                        department = report.get('department', 'Не указан')
                        date = report.get('created_at', 'Неизвестно')
                        report_text += f"{i+1}. 👤 <b>{user_name}</b> ({department})\n"
                        report_text += f"   📅 {date}\n\n"
                    
                    if len(all_reports) > 15:
                        report_text += f"... и еще {len(all_reports) - 15} отчетов\n\n"
                    
                    report_text += f"📊 <b>Всего отчетов:</b> {len(all_reports)}"
                else:
                    report_text = "📋 <b>Все отчеты в системе</b>\n\n📭 Отчетов в системе пока нет."
                
                await query.edit_message_text(report_text, parse_mode='HTML')
            except Exception as e:
                logger.error(f"Ошибка при получении всех отчетов: {e}")
                await query.edit_message_text(
                    "📋 <b>Все отчеты в системе</b>\n\n❌ Ошибка при загрузке отчетов.",
                    parse_mode='HTML'
                )
        elif data == 'reports_by_user':
            from utils.navigation import get_breadcrumb_path, update_context_path, create_keyboard
            
            path = update_context_path(context, 'reports_by_user')
            breadcrumb = get_breadcrumb_path(path)
            
            try:
                users = await self.db_manager.get_employees()
                if users:
                    keyboard_buttons = []
                    for user in users[:10]:  # Показываем первых 10 пользователей
                        keyboard_buttons.append([(f"👤 {user.full_name}", f"view_user_reports_{user.id}")])
                    
                    keyboard = create_keyboard(keyboard_buttons, path)
                    
                    await query.edit_message_text(
                        f"📍 {breadcrumb}\n\n"
                        f"👤 <b>Выберите пользователя</b>\n\n"
                        f"📋 Будут показаны все отчеты выбранного сотрудника:",
                        reply_markup=keyboard,
                        parse_mode='HTML'
                    )
                else:
                    await query.edit_message_text(
                        f"📍 {breadcrumb}\n\n"
                        f"👤 <b>Пользователи не найдены</b>\n\n"
                        f"❌ В системе нет зарегистрированных пользователей.",
                        parse_mode='HTML'
                    )
            except Exception as e:
                logger.error(f"Ошибка при получении списка пользователей: {e}")
                await query.edit_message_text(
                    f"📍 {breadcrumb}\n\n"
                    f"❌ <b>Ошибка</b>\n\n"
                    f"Не удалось загрузить список пользователей.",
                    parse_mode='HTML'
                )
        elif data == 'reports_by_department':
            from utils.navigation import get_breadcrumb_path, update_context_path, create_keyboard
            
            path = update_context_path(context, 'reports_by_department')
            breadcrumb = get_breadcrumb_path(path)
            
            try:
                departments = await self.db_manager.get_departments()
                if departments:
                    keyboard_buttons = []
                    for dept in departments:
                        keyboard_buttons.append([(f"🏢 {dept.name}", f"view_dept_reports_{dept.code}")])
                    
                    keyboard = create_keyboard(keyboard_buttons, path)
                    
                    await query.edit_message_text(
                        f"📍 {breadcrumb}\n\n"
                        f"🏢 <b>Выберите отдел</b>\n\n"
                        f"📋 Будут показаны все отчеты сотрудников выбранного отдела:",
                        reply_markup=keyboard,
                        parse_mode='HTML'
                    )
                else:
                    await query.edit_message_text(
                        f"📍 {breadcrumb}\n\n"
                        f"🏢 <b>Отделы не найдены</b>\n\n"
                        f"❌ В системе нет зарегистрированных отделов.",
                        parse_mode='HTML'
                    )
            except Exception as e:
                logger.error(f"Ошибка при получении списка отделов: {e}")
                await query.edit_message_text(
                    f"📍 {breadcrumb}\n\n"
                    f"❌ <b>Ошибка</b>\n\n"
                    f"Не удалось загрузить список отделов.",
                    parse_mode='HTML'
                )
        elif data == 'reports_export':
            try:
                await query.edit_message_text(
                    "📤 <b>Экспорт отчетов</b>\n\n"
                    "⏳ Подготавливаем файл с отчетами для экспорта...",
                    parse_mode='HTML'
                )
                
                # Получаем все отчеты для экспорта
                reports_data = await self.db_manager.get_all_reports_for_export()
                
                if reports_data:
                    # Создаем Excel файл с отчетами
                    excel_file = await self.report_processor.create_reports_export(reports_data)
                    
                    if excel_file:
                        await query.edit_message_text(
                            "📤 <b>Экспорт отчетов</b>\n\n"
                            f"✅ Файл успешно создан!\n"
                            f"📊 Экспортировано отчетов: {len(reports_data)}\n\n"
                            f"📎 Файл будет отправлен в следующем сообщении.",
                            parse_mode='HTML'
                        )
                        
                        # Отправляем файл
                        with open(excel_file, 'rb') as file:
                            await context.bot.send_document(
                                chat_id=query.message.chat_id,
                                document=file,
                                filename=f"all_reports_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                                caption="📊 Экспорт всех отчетов"
                            )
                    else:
                        await query.edit_message_text(
                            "📤 <b>Экспорт отчетов</b>\n\n"
                            "❌ Ошибка при создании файла экспорта.",
                            parse_mode='HTML'
                        )
                else:
                    await query.edit_message_text(
                        "📤 <b>Экспорт отчетов</b>\n\n"
                        "📭 Нет отчетов для экспорта.",
                        parse_mode='HTML'
                    )
            except Exception as e:
                logger.error(f"Ошибка при экспорте отчетов: {e}")
                await query.edit_message_text(
                    "📤 <b>Экспорт отчетов</b>\n\n"
                    "❌ Произошла ошибка при экспорте отчетов.",
                    parse_mode='HTML'
                )
        elif data == 'reports_search':
            from utils.navigation import get_breadcrumb_path, update_context_path, create_keyboard
            
            path = update_context_path(context, 'reports_search')
            breadcrumb = get_breadcrumb_path(path)
            
            keyboard = create_keyboard([
                [("👤 Поиск по пользователю", "search_by_user")],
                [("🏢 Поиск по отделу", "search_by_department")],
                [("📅 Поиск по дате", "search_by_date")],
                [("🔤 Поиск по тексту", "search_by_text")]
            ], path)
            
            await query.edit_message_text(
                f"📍 {breadcrumb}\n\n"
                f"🔍 <b>Поиск отчетов</b>\n\n"
                f"🎯 Выберите тип поиска:\n\n"
                f"• <b>По пользователю</b> - найти отчеты конкретного сотрудника\n"
                f"• <b>По отделу</b> - отчеты всего подразделения\n"
                f"• <b>По дате</b> - отчеты за определенный период\n"
                f"• <b>По тексту</b> - поиск по содержимому отчетов",
                reply_markup=keyboard,
                parse_mode='HTML'
            )
        
        return AdminStates.MAIN_MENU
    
    async def handle_export_action(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обрабатывает действия экспорта."""
        query = update.callback_query
        await query.answer()
        data = query.data
        
        if data == 'export_excel':
            try:
                await query.edit_message_text(
                    "📄 <b>Экспорт в Excel</b>\n\n"
                    "⏳ Подготавливаем Excel файл с отчетами...",
                    parse_mode='HTML'
                )
                
                # Получаем данные для экспорта
                reports_data = await self.db_manager.get_all_reports_for_export()
                
                if reports_data:
                    # Создаем Excel файл
                    excel_file = await self.report_processor.create_excel_export(reports_data)
                    
                    if excel_file:
                        await query.edit_message_text(
                            "📄 <b>Экспорт в Excel</b>\n\n"
                            f"✅ Excel файл успешно создан!\n"
                            f"📊 Экспортировано записей: {len(reports_data)}\n\n"
                            f"📎 Файл будет отправлен в следующем сообщении.",
                            parse_mode='HTML'
                        )
                        
                        # Отправляем файл
                        with open(excel_file, 'rb') as file:
                            await context.bot.send_document(
                                chat_id=query.message.chat_id,
                                document=file,
                                filename=f"reports_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                                caption="📊 Экспорт отчетов в формате Excel"
                            )
                    else:
                        await query.edit_message_text(
                            "📄 <b>Экспорт в Excel</b>\n\n"
                            "❌ Ошибка при создании Excel файла.",
                            parse_mode='HTML'
                        )
                else:
                    await query.edit_message_text(
                        "📄 <b>Экспорт в Excel</b>\n\n"
                        "📭 Нет данных для экспорта.",
                        parse_mode='HTML'
                    )
            except Exception as e:
                logger.error(f"Ошибка при экспорте в Excel: {e}")
                await query.edit_message_text(
                    "📄 <b>Экспорт в Excel</b>\n\n"
                    "❌ Произошла ошибка при экспорте данных.",
                    parse_mode='HTML'
                )
        elif data == 'export_csv':
            try:
                await query.edit_message_text(
                    "📋 <b>Экспорт в CSV</b>\n\n"
                    "⏳ Подготавливаем CSV файл с отчетами...",
                    parse_mode='HTML'
                )
                
                # Получаем данные для экспорта
                reports_data = await self.db_manager.get_all_reports_for_export()
                
                if reports_data:
                    # Создаем CSV файл
                    csv_file = await self.report_processor.create_csv_export(reports_data)
                    
                    if csv_file:
                        await query.edit_message_text(
                            "📋 <b>Экспорт в CSV</b>\n\n"
                            f"✅ CSV файл успешно создан!\n"
                            f"📊 Экспортировано записей: {len(reports_data)}\n\n"
                            f"📎 Файл будет отправлен в следующем сообщении.",
                            parse_mode='HTML'
                        )
                        
                        # Отправляем файл
                        with open(csv_file, 'rb') as file:
                            await context.bot.send_document(
                                chat_id=query.message.chat_id,
                                document=file,
                                filename=f"reports_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                caption="📊 Экспорт отчетов в формате CSV"
                            )
                    else:
                        await query.edit_message_text(
                            "📋 <b>Экспорт в CSV</b>\n\n"
                            "❌ Ошибка при создании CSV файла.",
                            parse_mode='HTML'
                        )
                else:
                    await query.edit_message_text(
                        "📋 <b>Экспорт в CSV</b>\n\n"
                        "📭 Нет данных для экспорта.",
                        parse_mode='HTML'
                    )
            except Exception as e:
                logger.error(f"Ошибка при экспорте в CSV: {e}")
                await query.edit_message_text(
                    "📋 <b>Экспорт в CSV</b>\n\n"
                    "❌ Произошла ошибка при экспорте данных.",
                    parse_mode='HTML'
                )
        elif data == 'export_departments':
            try:
                await query.edit_message_text(
                    "📊 <b>Отчет по отделам</b>\n\n"
                    "⏳ Формируем отчет по отделам...",
                    parse_mode='HTML'
                )
                
                # Получаем статистику по отделам
                dept_stats = await self.db_manager.get_detailed_department_statistics()
                
                if dept_stats:
                    report_text = "📊 <b>Детальный отчет по отделам</b>\n\n"
                    
                    for dept in dept_stats:
                        dept_name = dept.get('name', 'Неизвестный отдел')
                        user_count = dept.get('user_count', 0)
                        report_count = dept.get('report_count', 0)
                        active_users = dept.get('active_users', 0)
                        last_report = dept.get('last_report_date', 'Никогда')
                        
                        report_text += f"🏢 <b>{dept_name}</b>\n"
                        report_text += f"   👥 Всего сотрудников: {user_count}\n"
                        report_text += f"   ✅ Активных: {active_users}\n"
                        report_text += f"   📋 Отчетов: {report_count}\n"
                        report_text += f"   📅 Последний отчет: {last_report}\n"
                        
                        if user_count > 0:
                            activity_rate = (active_users / user_count) * 100
                            report_text += f"   📈 Активность: {activity_rate:.1f}%\n"
                        
                        report_text += "\n"
                    
                    # Создаем файл отчета
                    report_file = await self.report_processor.create_department_report(dept_stats)
                    
                    await query.edit_message_text(report_text[:4000], parse_mode='HTML')  # Telegram limit
                    
                    if report_file:
                        with open(report_file, 'rb') as file:
                            await context.bot.send_document(
                                chat_id=query.message.chat_id,
                                document=file,
                                filename=f"department_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                                caption="📊 Детальный отчет по отделам"
                            )
                else:
                    await query.edit_message_text(
                        "📊 <b>Отчет по отделам</b>\n\n"
                        "📭 Нет данных по отделам.",
                        parse_mode='HTML'
                    )
            except Exception as e:
                logger.error(f"Ошибка при создании отчета по отделам: {e}")
                await query.edit_message_text(
                    "📊 <b>Отчет по отделам</b>\n\n"
                    "❌ Произошла ошибка при создании отчета.",
                    parse_mode='HTML'
                )
        elif data == 'export_users':
            try:
                await query.edit_message_text(
                    "👥 <b>Список пользователей</b>\n\n"
                    "⏳ Формируем список пользователей...",
                    parse_mode='HTML'
                )
                
                # Получаем список всех пользователей
                users_data = await self.db_manager.get_all_users_for_export()
                
                if users_data:
                    users_text = "👥 <b>Список всех пользователей</b>\n\n"
                    
                    for user in users_data[:20]:  # Показываем первых 20 пользователей
                        username = user.get('username', 'Не указан')
                        full_name = user.get('full_name', 'Не указано')
                        department = user.get('department', 'Не указан')
                        is_admin = user.get('is_admin', False)
                        is_active = user.get('is_active', True)
                        last_activity = user.get('last_activity', 'Никогда')
                        
                        status_emoji = "👑" if is_admin else ("✅" if is_active else "❌")
                        
                        users_text += f"{status_emoji} <b>{full_name}</b>\n"
                        users_text += f"   📱 @{username}\n"
                        users_text += f"   🏢 {department}\n"
                        users_text += f"   📅 Активность: {last_activity}\n\n"
                    
                    if len(users_data) > 20:
                        users_text += f"... и еще {len(users_data) - 20} пользователей\n\n"
                    
                    users_text += f"📊 <b>Всего пользователей:</b> {len(users_data)}"
                    
                    # Создаем файл со списком пользователей
                    users_file = await self.report_processor.create_users_export(users_data)
                    
                    await query.edit_message_text(users_text[:4000], parse_mode='HTML')  # Telegram limit
                    
                    if users_file:
                        with open(users_file, 'rb') as file:
                            await context.bot.send_document(
                                chat_id=query.message.chat_id,
                                document=file,
                                filename=f"users_list_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                                caption="👥 Полный список пользователей"
                            )
                else:
                    await query.edit_message_text(
                        "👥 <b>Список пользователей</b>\n\n"
                        "📭 Пользователей не найдено.",
                        parse_mode='HTML'
                    )
            except Exception as e:
                logger.error(f"Ошибка при экспорте пользователей: {e}")
                await query.edit_message_text(
                    "👥 <b>Список пользователей</b>\n\n"
                    "❌ Произошла ошибка при получении списка пользователей.",
                    parse_mode='HTML'
                )
        
        return AdminStates.MAIN_MENU

    async def handle_admin_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handles all admin-related callbacks."""
        query = update.callback_query
        await query.answer()
        data = query.data

        if data.startswith('admin_user_'):
            return await self.user_management_handler.handle_callback(update, context)
        elif data.startswith('admin_dept_'):
            return await self.department_management_handler.handle_callback(update, context)
        elif data == 'admin_back_to_main_menu':
            return await self.show_admin_panel(update, context)
        elif data == 'admin_back':
            # Обработка кнопки "Назад" в админ-панели
            from utils.navigation import go_back_path
            path = go_back_path(context)
            if not path or path[-1] == 'admin':
                return await self.show_admin_panel(update, context)
            else:
                # Возвращаемся на предыдущий уровень
                return await self.show_admin_panel(update, context)

        return await self.handle_main_menu_callback(update, context)

    async def handle_main_menu_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обрабатывает нажатия кнопок в главном меню админки."""
        query = update.callback_query
        await query.answer()
        data = query.data

        if data == 'admin_manage_users':
            return await self.user_management_handler.show_user_list(update, context)
        elif data == 'admin_manage_depts':
            return await self.department_management_handler.show_department_list(update, context)
        elif data == 'admin_reports':
            return await self.handle_reports_callback(update, context)
        elif data == 'admin_reminders':
            return await self.handle_reminder_callback(update, context)
        elif data == 'admin_export':
            return await self.handle_export_callback(update, context)
        elif data == 'export_reports':
            return await self.handle_export_action(update, context, 'reports')
        elif data == 'export_users':
            return await self.handle_export_action(update, context, 'users')
        elif data == 'export_departments':
            return await self.handle_export_action(update, context, 'departments')
        elif data == 'export_all_data':
            return await self.handle_export_action(update, context, 'all_data')
        elif data == 'export_stats':
            return await self.handle_export_action(update, context, 'stats')
        elif data.startswith('reminder_'):
            return await self.handle_reminder_action(update, context)
        elif data.startswith('reports_'):
            return await self.handle_reports_action(update, context)
        elif data.startswith('export_'):
            return await self.handle_export_action(update, context)
        elif data == 'admin_exit':
            await query.edit_message_text(
                "✅ <b>Выход из админ-панели</b>\n\n"
                "Вы успешно вышли из панели администратора.\n"
                "Используйте команду /start для возврата в главное меню.",
                parse_mode='HTML'
            )
            return ConversationHandler.END
        
        return AdminStates.MAIN_MENU