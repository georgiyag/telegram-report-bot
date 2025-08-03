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
            dept_code = data.split('_')[-1]
            try:
                department = await self.db_manager.get_department_by_code(dept_code)
                if department:
                    await query.edit_message_text(
                        f"✏️ <b>Редактирование отдела</b>\n\n"
                        f"🏢 <b>Название:</b> {department.name}\n"
                        f"🔤 <b>Код:</b> {department.code}\n\n"
                        f"🔧 Функция редактирования будет добавлена в следующих обновлениях.\n\n"
                        f"💡 Пока вы можете удалить отдел и создать новый.",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("🗑️ Удалить отдел", callback_data=f"admin_delete_dept_{dept_code}")],
                            [InlineKeyboardButton("⬅️ Назад", callback_data="admin_back")]
                        ]),
                        parse_mode='HTML'
                    )
                else:
                    await query.edit_message_text(
                        "❌ Отдел не найден.",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("⬅️ Назад", callback_data="admin_back")]
                        ])
                    )
            except Exception as e:
                logger.error(f"Ошибка при получении отдела для редактирования: {e}")
                await query.edit_message_text(
                    "❌ Ошибка при получении данных отдела.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("⬅️ Назад", callback_data="admin_back")]
                    ])
                )
            return AdminStates.MANAGE_DEPARTMENTS
        elif data.startswith("admin_delete_dept_"):
            dept_code = data.split('_')[-1]
            try:
                department = await self.db_manager.get_department_by_code(dept_code)
                if department:
                    # Проверяем, есть ли пользователи в этом отделе
                    users_count = await self.db_manager.get_users_count_by_department(dept_code)
                    
                    if users_count > 0:
                        await query.edit_message_text(
                            f"⚠️ <b>Невозможно удалить отдел</b>\n\n"
                            f"🏢 <b>Отдел:</b> {department.name}\n"
                            f"👥 <b>Сотрудников в отделе:</b> {users_count}\n\n"
                            f"❌ Нельзя удалить отдел, в котором есть сотрудники.\n"
                            f"Сначала переведите всех сотрудников в другие отделы.",
                            reply_markup=InlineKeyboardMarkup([
                                [InlineKeyboardButton("⬅️ Назад", callback_data="admin_back")]
                            ]),
                            parse_mode='HTML'
                        )
                    else:
                        await query.edit_message_text(
                            f"🗑️ <b>Удаление отдела</b>\n\n"
                            f"🏢 <b>Отдел:</b> {department.name}\n"
                            f"🔤 <b>Код:</b> {department.code}\n\n"
                            f"⚠️ Вы уверены, что хотите удалить этот отдел?\n"
                            f"Это действие нельзя отменить!",
                            reply_markup=InlineKeyboardMarkup([
                                [InlineKeyboardButton("✅ Да, удалить", callback_data=f"confirm_delete_dept_{dept_code}")],
                                [InlineKeyboardButton("❌ Отмена", callback_data="admin_back")]
                            ]),
                            parse_mode='HTML'
                        )
                else:
                    await query.edit_message_text(
                        "❌ Отдел не найден.",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("⬅️ Назад", callback_data="admin_back")]
                        ])
                    )
            except Exception as e:
                logger.error(f"Ошибка при получении отдела для удаления: {e}")
                await query.edit_message_text(
                    "❌ Ошибка при получении данных отдела.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("⬅️ Назад", callback_data="admin_back")]
                    ])
                )
            return AdminStates.MANAGE_DEPARTMENTS
        elif data.startswith("confirm_delete_dept_"):
            dept_code = data.split('_')[-1]
            try:
                success = await self.db_manager.delete_department(dept_code)
                if success:
                    await query.edit_message_text(
                        "✅ <b>Отдел успешно удален</b>\n\n"
                        "Возвращаемся к списку отделов...",
                        parse_mode='HTML'
                    )
                    # Возвращаемся к списку отделов
                    return await self.show_department_list(update, context)
                else:
                    await query.edit_message_text(
                        "❌ Ошибка при удалении отдела.",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("⬅️ Назад", callback_data="admin_back")]
                        ])
                    )
            except Exception as e:
                logger.error(f"Ошибка при удалении отдела: {e}")
                await query.edit_message_text(
                    "❌ Произошла ошибка при удалении отдела.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("⬅️ Назад", callback_data="admin_back")]
                    ])
                )
            return AdminStates.MANAGE_DEPARTMENTS
        elif data == "admin_add_dept":
            await query.message.reply_text("Введите название нового отдела:")
            return AdminStates.ADD_DEPARTMENT_NAME
        elif data == "admin_back":
            return AdminStates.MAIN_MENU

        return AdminStates.MANAGE_DEPARTMENTS