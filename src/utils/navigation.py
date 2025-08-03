# -*- coding: utf-8 -*-
"""
Утилиты для управления навигацией и "хлебными крошками" в боте.
"""

from typing import List, Tuple, Optional
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Словарь с названиями для хлебных крошек
BREADCRUMB_TITLES = {
    'main': '🏠 Главное меню',
    'admin': '👑 Админ-панель',
    'admin_users': '👥 Управление пользователями',
    'admin_departments': '🗄️ Управление отделами',
    'admin_reports': '📊 Просмотр отчетов',
    'admin_reminders': '🔔 Управление напоминаниями',
    'admin_export': '📤 Экспорт данных',
    'report': '📝 Отчеты',
    'report_create': '✍️ Создать отчет',
    'report_view': '👁️ Просмотр отчетов',
    'help': '❓ Помощь',
    'status': '📊 Статус',
    'users': '👥 Пользователи',
    'settings': '⚙️ Настройки',
    'profile': '👤 Профиль'
}

def get_breadcrumb_path(path: List[str]) -> str:
    """Генерирует текстовый путь хлебных крошек."""
    if not path:
        return BREADCRUMB_TITLES.get('main', '')
    return ' > '.join([BREADCRUMB_TITLES.get(p, p) for p in path])

def create_keyboard(buttons: List[List[Tuple[str, str]]], path: Optional[List[str]] = None, show_home: bool = True) -> InlineKeyboardMarkup:
    """Создает Inline-клавиатуру с возможностью добавления кнопок навигации."""
    keyboard = []
    for row in buttons:
        keyboard.append([InlineKeyboardButton(text, callback_data=data) for text, data in row])

    # Добавляем навигационные кнопки
    nav_buttons = []
    
    if path and len(path) > 1:
        # Добавляем кнопку "Назад", которая ведет на предыдущий уровень
        if path[-1] == 'admin' or any('admin' in p for p in path):
            nav_buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data='admin_back'))
        else:
            parent_path = 'back_' + '_'.join(path[:-1])
            nav_buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=parent_path))
    
    if show_home and path and path != ['main']:
        # Добавляем кнопку "В главное меню"
        nav_buttons.append(InlineKeyboardButton("🏠 Главное меню", callback_data='back_to_main'))
    
    if nav_buttons:
        keyboard.append(nav_buttons)

    return InlineKeyboardMarkup(keyboard)


def update_context_path(context, new_path: str):
    """Обновляет путь в контексте пользователя."""
    if 'path' not in context.user_data:
        context.user_data['path'] = []
    
    # Предотвращаем дублирование последнего элемента
    if not context.user_data['path'] or context.user_data['path'][-1] != new_path:
        context.user_data['path'].append(new_path)
    return context.user_data['path']

def go_back_path(context):
    """Возвращает пользователя на один уровень назад в пути."""
    if 'path' in context.user_data and context.user_data['path']:
        context.user_data['path'].pop()
    return context.user_data.get('path', [])

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