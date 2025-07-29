# -*- coding: utf-8 -*-
"""
Модуль для управления отделами через админ-панель.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from loguru import logger

from handlers.states import AdminStates
from database import DatabaseManager

class DepartmentManagementHandler:
    """Обработчик для управления отделами."""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    async def show_department_list(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Displays the list of departments with management buttons."""
        query = update.callback_query
        await query.answer()

        departments = await self.db_manager.get_departments()
        
        keyboard = []
        if departments:
            for dept in departments:
                keyboard.append([InlineKeyboardButton(f"{dept.name}", callback_data=f"admin_edit_dept_{dept.code}")])
        
        keyboard.append([InlineKeyboardButton("➕ Добавить отдел", callback_data="admin_add_dept")])
        keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="admin_back")])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text="🗄️ Управление отделами:",
            reply_markup=reply_markup
        )
        return AdminStates.MANAGE_DEPARTMENTS

    async def add_department_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Saves the department name and asks for the code."""
        department_name = update.message.text
        context.user_data['new_department_name'] = department_name
        await update.message.reply_text(f"Название отдела: {department_name}.\nВведите код отдела (например, 'IT'):")
        return AdminStates.ADD_DEPARTMENT_CODE

    async def edit_department_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handles the request to edit a department's name."""
        query = update.callback_query
        await query.answer()
        dept_code = query.data.split('_')[-1]
        context.user_data['department_to_edit'] = dept_code
        await query.message.reply_text("Введите новое название отдела:")
        return AdminStates.EDIT_DEPARTMENT_NAME

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handles callbacks for department management."""
        query = update.callback_query
        await query.answer()
        data = query.data

        if data.startswith("admin_edit_dept_"):
            return await self.edit_department_name(update, context)
        elif data == "admin_add_dept":
            await query.message.reply_text("Введите название нового отдела:")
            return AdminStates.ADD_DEPARTMENT_NAME
        elif data.startswith("admin_edit_dept_"):
            dept_code = data.split('_')[-1]
            await query.edit_message_text(f"Редактирование отдела {dept_code} (не реализовано).")
            return AdminStates.MANAGE_DEPARTMENTS
        elif data == "admin_back":
            return AdminStates.MAIN_MENU

        return AdminStates.MANAGE_DEPARTMENTS