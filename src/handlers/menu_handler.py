# -*- coding: utf-8 -*-
"""
Обработчик главного меню с визуальными кнопками
"""

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from loguru import logger

from config import settings, MESSAGES
from .states import MainMenuStates, get_main_menu_keyboard, get_back_to_main_keyboard, get_persistent_menu_keyboard
from utils.navigation import get_breadcrumb_path, update_context_path, go_back_path

class MenuHandler:
    """Обработчик главного меню с кнопками"""
    
    def __init__(self, report_handler, admin_handler):
        self.report_handler = report_handler
        self.admin_handler = admin_handler
    
    async def show_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Показать главное меню с кнопками"""
        user = update.effective_user
        is_admin = user.id in settings.get_admin_ids()
        
        # Сбрасываем путь навигации до главного меню
        context.user_data['path'] = ['main']
        breadcrumb = get_breadcrumb_path(context.user_data['path'])
        
        # Определяем, откуда пришел запрос
        if update.callback_query:
            query = update.callback_query
            await query.answer()
            
            welcome_text = (
                f"📍 {breadcrumb}\n\n"
                f"🏢 <b>Система отправки резюме за неделю</b>\n"
                f"<i>АО ЭМЗ ФИРМА СЭЛМА</i>\n\n"
                f"👋 Добро пожаловать, <b>{user.first_name}</b>!\n\n"
                f"🎯 Выберите действие:"
            )
            
            await query.edit_message_text(
                text=welcome_text,
                reply_markup=get_main_menu_keyboard(is_admin),
                parse_mode='HTML'
            )
        else:
            # Обычное сообщение
            if not update.message:
                logger.error("update.message is None in show_main_menu")
                return MainMenuStates.MAIN_MENU
                
            welcome_text = MESSAGES['menu_main']
            
            await update.message.reply_text(
                text=welcome_text,
                reply_markup=get_main_menu_keyboard(is_admin),
                parse_mode='HTML'
            )
            
            # Добавляем постоянную клавиатуру с кнопкой меню
            await update.message.reply_text(
                "Используйте кнопку 'Меню' внизу для быстрого доступа к главному меню.",
                reply_markup=get_persistent_menu_keyboard()
            )
        
        return MainMenuStates.MAIN_MENU
    
    async def handle_menu_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обработка нажатий кнопок главного меню"""
        query = update.callback_query
        await query.answer()
        
        user = update.effective_user
        callback_data = query.data
        
        logger.info(f"Пользователь {user.id} выбрал: {callback_data}")
        
        # Обработка навигации назад
        if callback_data.startswith('back_'):
            path = go_back_path(context)
            if not path or path[-1] == 'main':
                return await self.show_main_menu(update, context)
        
        if callback_data == "menu_status":
            # Показать статус отчета
            path = update_context_path(context, 'status')
            breadcrumb = get_breadcrumb_path(path)
            
            await query.edit_message_text(
                text=f"📍 {breadcrumb}\n\n📊 <b>Статус отчета</b>\n\n⏳ Проверяем ваш статус...",
                parse_mode='HTML'
            )
            # Вызываем метод статуса и добавляем кнопку возврата
            await self.report_handler.status_command(update, context)
            return MainMenuStates.MAIN_MENU
            
        elif callback_data == "menu_help":
            # Показать справку
            path = update_context_path(context, 'help')
            breadcrumb = get_breadcrumb_path(path)
            
            help_text = (
                f"📍 {breadcrumb}\n\n"
                f"❓ <b>Справка по системе</b>\n\n"
                f"📝 <b>Как создать отчет:</b>\n"
                f"• Нажмите кнопку 'Создать отчет'\n"
                f"• Опишите свою работу за неделю\n"
                f"• Отправьте отчет\n\n"
                f"📊 <b>Проверка статуса:</b>\n"
                f"• Используйте кнопку 'Статус отчета'\n"
                f"• Просматривайте историю отчетов\n\n"
                f"🔔 <b>Напоминания:</b>\n"
                f"• Отчеты принимаются до понедельника\n"
                f"• Система автоматически напоминает о сроках\n\n"
                f"❓ <b>Нужна помощь?</b> Обратитесь к администратору."
            )
            
            await query.edit_message_text(
                text=help_text,
                reply_markup=get_back_to_main_keyboard(),
                parse_mode='HTML'
            )
            return MainMenuStates.MAIN_MENU
            

        elif callback_data == "menu_report":
            # Создание отчета - передаем управление report_handler
            path = update_context_path(context, 'report')
            # Завершаем текущий conversation и передаем управление report_handler
            return ConversationHandler.END
            
        elif callback_data == "menu_admin":
            # Обновляем путь для админ-панели
            update_context_path(context, 'admin')
            # Возвращаем состояние для обработки админ-панели
            return MainMenuStates.MAIN_MENU
            
        elif callback_data == "back_to_main":
            # Возврат в главное меню
            return await self.show_main_menu(update, context)
        
        return MainMenuStates.MAIN_MENU
    
    async def handle_menu_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обработка нажатия кнопки 'Меню' из постоянной клавиатуры"""
        if update.message and update.message.text == "🏠 Меню":
            user = update.effective_user
            is_admin = user.id in settings.get_admin_ids()
            await update.message.reply_text(
                text=MESSAGES['menu_main'],
                reply_markup=get_main_menu_keyboard(is_admin),
                parse_mode='HTML'
            )
            return MainMenuStates.MAIN_MENU
        return MainMenuStates.MAIN_MENU
    
    async def cancel_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Отмена и возврат в главное меню"""
        if update.callback_query:
            query = update.callback_query
            await query.answer()
            await query.edit_message_text(
                text="Операция отменена.",
                reply_markup=get_back_to_main_keyboard()
            )
        else:
            if not update.message:
                logger.error("update.message is None in cancel_menu")
                return MainMenuStates.MAIN_MENU
                
            await update.message.reply_text(
                text="Операция отменена.",
                reply_markup=get_back_to_main_keyboard()
            )
        
        return MainMenuStates.MAIN_MENU