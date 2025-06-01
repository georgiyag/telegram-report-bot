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
    EXPORT_DATA = 14

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
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

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

def get_report_confirmation_keyboard():
    """Клавиатура для подтверждения отчета"""
    keyboard = [
        [InlineKeyboardButton("✅ Отправить отчет", callback_data="confirm_report")],
        [InlineKeyboardButton("✏️ Редактировать", callback_data="edit_report")],
        [InlineKeyboardButton("❌ Отменить", callback_data="cancel_report")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_admin_main_keyboard():
    """Главная клавиатура админ-панели"""
    keyboard = [
        [InlineKeyboardButton("📊 Просмотр отчетов", callback_data="admin_view_reports")],
        [InlineKeyboardButton("📢 Отправить напоминание", callback_data="admin_send_reminder")],
        [InlineKeyboardButton("👥 Управление пользователями", callback_data="admin_manage_users")],
        [InlineKeyboardButton("📤 Экспорт данных", callback_data="admin_export_data")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_main")],
        [InlineKeyboardButton("❌ Закрыть", callback_data="admin_close")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_cancel_keyboard():
    """Клавиатура для отмены операции"""
    keyboard = [
        [InlineKeyboardButton("❌ Отменить", callback_data="cancel")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_skip_keyboard():
    """Клавиатура для пропуска необязательного поля"""
    keyboard = [
        [InlineKeyboardButton("⏭️ Пропустить", callback_data="skip")],
        [InlineKeyboardButton("❌ Отменить", callback_data="cancel")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_back_to_main_keyboard():
    """Клавиатура для возврата в главное меню"""
    keyboard = [
        [InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_departments_keyboard():
    """Клавиатура для выбора отдела"""
    from config import DEPARTMENTS
    
    keyboard = []
    # Добавляем кнопки отделов по 1 в ряд для удобства
    for dept in DEPARTMENTS:
        keyboard.append([InlineKeyboardButton(dept, callback_data=f"dept_{dept}")])
    
    # Добавляем кнопку отмены
    keyboard.append([InlineKeyboardButton("❌ Отменить", callback_data="cancel")])
    
    return InlineKeyboardMarkup(keyboard)