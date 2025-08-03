# -*- coding: utf-8 -*-
from telegram.ext import ConversationHandler

# Состояния для создания отчета
class ReportStates:
    """Состояния для процесса создания отчета"""
    WAITING_DEPARTMENT = 1
    WAITING_TASKS = 2
    WAITING_ACHIEVEMENTS = 3
    WAITING_PROBLEMS = 4
    WAITING_PLANS = 5
    WAITING_CONFIRMATION = 6

# Состояния для админ-панели
class AdminStates:
    """Состояния для админ-панели"""
    MAIN_MENU = 10
    VIEW_REPORTS = 11
    SEND_REMINDER = 12
    MANAGE_USERS = 13
    MANAGE_DEPARTMENTS = 40
    ADD_DEPARTMENT_NAME = 41
    ADD_DEPARTMENT_CODE = 42
    EDIT_DEPARTMENT_NAME = 43
    ADD_USER_ID = 44
    ADD_USER_FULL_NAME = 45
    EXPORT_DATA = 14
    WAITING_INPUT = 15
    
    # Состояния для мастера добавления пользователя
    ADD_USER_STEP1_ID = 16
    ADD_USER_STEP2_USERNAME = 17
    ADD_USER_STEP3_FULLNAME = 18
    ADD_USER_STEP4_DEPARTMENT = 19
    ADD_USER_STEP5_POSITION = 20
    ADD_USER_STEP6_EMPLOYEE_ID = 21
    ADD_USER_STEP7_EMAIL = 22
    ADD_USER_STEP8_PHONE = 23
    ADD_USER_CONFIRM = 24
    
    # Состояния для мастера добавления отдела
    ADD_DEPT_STEP1_CODE = 25
    ADD_DEPT_STEP2_NAME = 26
    ADD_DEPT_STEP3_DESCRIPTION = 27
    ADD_DEPT_STEP4_HEAD = 28
    ADD_DEPT_CONFIRM = 29

    # Состояния для редактирования отдела
    EDIT_DEPT_STEP1_SELECT = 35
    EDIT_DEPT_STEP2_NAME = 36
    EDIT_DEPT_CONFIRM = 37
    
    # Состояния для удаления
    DELETE_USER_SELECT = 30
    DELETE_USER_CONFIRM = 31
    DELETE_DEPT_SELECT = 32
    DELETE_DEPT_CONFIRM = 33
    DELETE_CONFIRM = 34
    
    # Состояния для управления административными правами
    ADMIN_RIGHTS = 35
    GRANT_ADMIN_SELECT = 36
    GRANT_ADMIN_CONFIRM = 37
    REVOKE_ADMIN_SELECT = 38
    REVOKE_ADMIN_CONFIRM = 39

# Состояния для настройки пользователя
class UserStates:
    """Состояния для настройки пользователя"""
    WAITING_DEPARTMENT = 20
    WAITING_POSITION = 21
    WAITING_FULL_NAME = 22

# Состояния для главного меню
class MainMenuStates:
    """Состояния для главного меню"""
    MAIN_MENU = 30

# Общие состояния
STATE_END = ConversationHandler.END
STATE_CANCEL = -1

# Словарь для удобного доступа к состояниям
STATES = {
    # Отчеты
    'REPORT_DEPARTMENT': ReportStates.WAITING_DEPARTMENT,
    'REPORT_TASKS': ReportStates.WAITING_TASKS,
    'REPORT_ACHIEVEMENTS': ReportStates.WAITING_ACHIEVEMENTS,
    'REPORT_PROBLEMS': ReportStates.WAITING_PROBLEMS,
    'REPORT_PLANS': ReportStates.WAITING_PLANS,
    'REPORT_CONFIRMATION': ReportStates.WAITING_CONFIRMATION,
    
    # Админ
    'ADMIN_MAIN': AdminStates.MAIN_MENU,
    'ADMIN_REPORTS': AdminStates.VIEW_REPORTS,
    'ADMIN_REMINDER': AdminStates.SEND_REMINDER,
    'ADMIN_USERS': AdminStates.MANAGE_USERS,
    'ADMIN_DEPARTMENTS': AdminStates.MANAGE_DEPARTMENTS,
    'ADMIN_EXPORT': AdminStates.EXPORT_DATA,
    
    # Пользователь
    'USER_DEPARTMENT': UserStates.WAITING_DEPARTMENT,
    'USER_POSITION': UserStates.WAITING_POSITION,
    'USER_NAME': UserStates.WAITING_FULL_NAME,
    
    # Главное меню
    'MAIN_MENU': MainMenuStates.MAIN_MENU,
    
    # Общие
    'END': STATE_END,
    'CANCEL': STATE_CANCEL
}

# Клавиатуры для состояний
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

def get_main_menu_keyboard(is_admin=False):
    """Главное меню с кнопками"""
    keyboard = [
        [InlineKeyboardButton("📝 Создать отчет", callback_data="menu_report")],
        [InlineKeyboardButton("📊 Статус отчета", callback_data="menu_status")],
        [InlineKeyboardButton("❓ Помощь", callback_data="menu_help")]
    ]
    
    if is_admin:
        keyboard.append([InlineKeyboardButton("⚙️ Панель администратора", callback_data="menu_admin")])
    
    return InlineKeyboardMarkup(keyboard)

def get_persistent_menu_keyboard():
    """Постоянная клавиатура с кнопкой меню"""
    keyboard = [
        [KeyboardButton("🏠 Меню")]
    ]
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=False,
        is_persistent=True
    )

def remove_persistent_keyboard():
    """Удаление постоянной клавиатуры"""
    return ReplyKeyboardRemove()

def get_report_confirmation_keyboard():
    """Клавиатура для подтверждения отчета"""
    keyboard = [
        [InlineKeyboardButton("✅ Отправить отчет", callback_data="confirm_report")],
        [InlineKeyboardButton("✏️ Редактировать", callback_data="edit_report")],
        [InlineKeyboardButton("❌ Отменить", callback_data="cancel")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_admin_main_keyboard():
    """Клавиатура главного меню администратора"""
    keyboard = [
        [InlineKeyboardButton("📊 Просмотр отчетов", callback_data="admin_reports")],
        [InlineKeyboardButton("📢 Отправить напоминание", callback_data="admin_reminders")],
        [InlineKeyboardButton("👥 Управление пользователями", callback_data="admin_manage_users")],
        [InlineKeyboardButton("🗄️ Управление отделами", callback_data="admin_manage_depts")],
        [InlineKeyboardButton("📤 Экспорт данных", callback_data="admin_export")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_main")],
        [InlineKeyboardButton("❌ Закрыть", callback_data="admin_exit")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_wizard_navigation_keyboard(back_callback=None, skip_callback=None, cancel_callback="wizard_cancel"):
    """Клавиатура навигации для мастеров"""
    keyboard = []
    
    row = []
    if back_callback:
        row.append(InlineKeyboardButton("⬅️ Назад", callback_data=back_callback))
    if skip_callback:
        row.append(InlineKeyboardButton("⏭️ Пропустить", callback_data=skip_callback))
    if row:
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("❌ Отменить", callback_data=cancel_callback)])
    return InlineKeyboardMarkup(keyboard)

def get_confirmation_keyboard(confirm_callback, cancel_callback="wizard_cancel"):
    """Клавиатура подтверждения"""
    keyboard = [
        [InlineKeyboardButton("✅ Подтвердить", callback_data=confirm_callback)],
        [InlineKeyboardButton("✏️ Редактировать", callback_data="wizard_edit")],
        [InlineKeyboardButton("❌ Отменить", callback_data=cancel_callback)]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_delete_confirmation_keyboard(confirm_callback, cancel_callback="delete_cancel"):
    """Клавиатура подтверждения удаления"""
    keyboard = [
        [InlineKeyboardButton("🗑️ Да, удалить", callback_data=confirm_callback)],
        [InlineKeyboardButton("❌ Отменить", callback_data=cancel_callback)]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_cancel_keyboard():
    """Клавиатура для отмены операции"""
    keyboard = [
        [InlineKeyboardButton("❌ Отменить", callback_data="cancel")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_skip_keyboard():
    """Клавиатура для пропуска необязательного поля"""
    keyboard = [
        [InlineKeyboardButton("⏭️ Пропустить", callback_data="skip")],
        [InlineKeyboardButton("❌ Отменить", callback_data="cancel")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_back_to_main_keyboard():
    """Клавиатура для возврата в главное меню"""
    keyboard = [
        [InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def admin_back(context):
    """Возврат в админ-панели"""
    if 'path' in context.user_data:
        # Если мы в админ-панели, возвращаемся к главному админ-меню
        if any('admin' in p for p in context.user_data['path']):
            context.user_data['path'] = ['admin']
        else:
            context.user_data['path'] = ['main']
    return context.user_data.get('path', ['admin'])

def back_to_main(context):
    """Возврат в главное меню"""
    if 'path' in context.user_data:
        context.user_data['path'] = ['main']
    return context.user_data.get('path', ['main'])

def cancel(context):
    """Отмена операции"""
    if 'path' in context.user_data and context.user_data['path']:
        # Возвращаемся на предыдущий уровень или в главное меню
        if len(context.user_data['path']) > 1:
            context.user_data['path'].pop()
        else:
            context.user_data['path'] = ['main']
    return context.user_data.get('path', ['main'])

async def get_departments_keyboard(db_manager):
    """Клавиатура для выбора отдела из базы данных"""
    keyboard = []
    
    try:
        # Получаем активные отделы из базы данных
        departments = await db_manager.get_departments()
        active_departments = [dept for dept in departments if dept.is_active]
        
        # Добавляем кнопки отделов по 1 в ряд для удобства
        for dept in active_departments:
            keyboard.append([InlineKeyboardButton(dept.name, callback_data=f"dept_{dept.name}")])
    except Exception as e:
        # В случае ошибки используем резервный список
        from config import DEPARTMENTS
        for dept in DEPARTMENTS:
            keyboard.append([InlineKeyboardButton(dept, callback_data=f"dept_{dept}")])
    
    # Добавляем кнопки отмены и возврата в главное меню
    keyboard.append([InlineKeyboardButton("❌ Отменить", callback_data="cancel")])
    keyboard.append([InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_main")])
    
    return InlineKeyboardMarkup(keyboard)