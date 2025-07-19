# -*- coding: utf-8 -*-
"""
Обработчик главного меню с визуальными кнопками
"""

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from loguru import logger

from config import settings, MESSAGES
from .states import MainMenuStates, get_main_menu_keyboard, get_back_to_main_keyboard, get_persistent_menu_keyboard

class MenuHandler:
    """Обработчик главного меню с кнопками"""
    
    def __init__(self, report_handler, admin_handler):
        self.report_handler = report_handler
        self.admin_handler = admin_handler
    
    async def show_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Показать главное меню с кнопками"""
        user = update.effective_user
        is_admin = user.id in settings.get_admin_ids()
        
        # Определяем, откуда пришел запрос
        if update.callback_query:
            query = update.callback_query
            await query.answer()
            
            welcome_text = (
                f"🏠 <b>Главное меню</b>\n\n"
                f"🏢 <b>Система отправки резюме за неделю АО ЭМЗ ФИРМА СЭЛМА</b>\n\n"
                f"Добро пожаловать, {user.first_name}!\n\n"
                f"Выберите действие:"
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
        
        if callback_data == "menu_status":
            # Показать статус отчета
            await query.edit_message_text(
                text="📊 <b>Статус отчета</b>\n\nПроверяем ваш статус...",
                parse_mode='HTML'
            )
            # Вызываем метод статуса и добавляем кнопку возврата
            await self.report_handler.status_command(update, context)
            return MainMenuStates.MAIN_MENU
            
        elif callback_data == "menu_help":
            # Показать справку
            await query.edit_message_text(
                text=MESSAGES['menu_help_extended'],
                reply_markup=get_back_to_main_keyboard(),
                parse_mode='HTML'
            )
            return MainMenuStates.MAIN_MENU
            
        elif callback_data == "menu_admin":
            # Эта кнопка обрабатывается отдельным handler'ом в main.py
            pass
            
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