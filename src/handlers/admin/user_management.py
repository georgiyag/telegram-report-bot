# -*- coding: utf-8 -*-
"""
Модуль для управления пользователями через админ-панель.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from loguru import logger

from handlers.states import AdminStates
from database import DatabaseManager

class UserManagementHandler:
    """Обработчик для управления пользователями."""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    async def show_user_list(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Показывает список пользователей с кнопками управления."""
        query = update.callback_query
        await query.answer()

        users = await self.db_manager.get_employees()

        if not users:
            await query.edit_message_text(
                text="👥 Пользователи не найдены.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ Добавить пользователя", callback_data="admin_add_user")],
                    [InlineKeyboardButton("⬅️ Назад", callback_data="admin_back")]
                ])
            )
            return AdminStates.MANAGE_USERS

    async def add_user_id(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Prompts for the new user's Telegram ID."""
        query = update.callback_query
        await query.answer()
        await query.edit_message_text("Введите Telegram ID нового пользователя:")
        return AdminStates.ADD_USER_ID

    async def cancel_user_action(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Cancels the current user action and returns to the user list."""
        query = update.callback_query
        await query.answer()
        return await self.show_user_list(update, context)

    async def add_user_full_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Saves the user's Telegram ID and prompts for their full name."""
        user_id = update.message.text
        context.user_data['new_user_id'] = user_id
        await update.message.reply_text(f"Telegram ID: {user_id}.\nВведите ФИО пользователя:")
        return AdminStates.ADD_USER_FULL_NAME

    async def add_user_department(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Saves the user's full name and prompts for their department."""
        full_name = update.message.text
        context.user_data['new_user_full_name'] = full_name
        # Here you would typically show a list of departments to choose from
        await update.message.reply_text(f"ФИО: {full_name}.\nВведите код отдела:")
        return AdminStates.ADD_USER_DEPARTMENT

        keyboard = []
        for user in users:
            keyboard.append([InlineKeyboardButton(f"{user.full_name}", callback_data=f"admin_edit_user_{user.id}")])
        
        keyboard.append([InlineKeyboardButton("➕ Добавить пользователя", callback_data="admin_add_user")])
        keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="admin_back")])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text="👥 Управление пользователями:",
            reply_markup=reply_markup
        )
        return AdminStates.MANAGE_USERS

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обрабатывает нажатия на кнопки в меню управления пользователями."""
        query = update.callback_query
        await query.answer()
        data = query.data

        if data == 'admin_add_user':
            return await self.add_user_id(update, context)
        elif data.startswith('admin_edit_user_'):
            user_id = int(data.split('_')[-1])
            # Логика редактирования пользователя
            await query.edit_message_text(f"Редактирование пользователя {user_id} (не реализовано).")
            return AdminStates.MANAGE_USERS
        elif data == 'admin_back':
            # Возврат в главное меню админки
            # Это должно обрабатываться в ConversationHandler админки
            return AdminStates.MAIN_MENU

        return AdminStates.MANAGE_USERS