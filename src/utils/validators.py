import re
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from loguru import logger

from .text_utils import count_words, validate_text_length

def validate_telegram_user_id(user_id: Any) -> Tuple[bool, Optional[str]]:
    """Валидация Telegram user ID"""
    try:
        user_id = int(user_id)
        if user_id <= 0:
            return False, "User ID должен быть положительным числом"
        if user_id > 2**63 - 1:  # Максимальное значение для int64
            return False, "User ID слишком большой"
        return True, None
    except (ValueError, TypeError):
        return False, "User ID должен быть числом"

def validate_telegram_username(username: str) -> Tuple[bool, Optional[str]]:
    """Валидация Telegram username"""
    if not username:
        return True, None  # Username может быть пустым
    
    # Убираем @ если есть
    username = username.lstrip('@')
    
    # Проверяем формат
    if not re.match(r'^[a-zA-Z0-9_]{5,32}$', username):
        return False, "Username должен содержать 5-32 символа (буквы, цифры, подчеркивания)"
    
    return True, None

def validate_full_name(name: str) -> Tuple[bool, Optional[str]]:
    """Валидация полного имени"""
    if not name or not name.strip():
        return False, "Имя не может быть пустым"
    
    name = name.strip()
    
    # Проверяем длину
    if len(name) < 2:
        return False, "Имя должно содержать минимум 2 символа"
    
    if len(name) > 100:
        return False, "Имя не может быть длиннее 100 символов"
    
    # Проверяем на допустимые символы (буквы, пробелы, дефисы, апострофы)
    if not re.match(r"^[a-zA-Zа-яА-ЯёЁ\s\-']+$", name):
        return False, "Имя может содержать только буквы, пробелы, дефисы и апострофы"
    
    # Проверяем, что есть хотя бы одна буква
    if not re.search(r'[a-zA-Zа-яА-ЯёЁ]', name):
        return False, "Имя должно содержать хотя бы одну букву"
    
    return True, None

def validate_department(department: str) -> Tuple[bool, Optional[str]]:
    """Валидация названия отдела"""
    if not department:
        return True, None  # Отдел может быть не указан
    
    department = department.strip()
    
    if len(department) < 2:
        return False, "Название отдела должно содержать минимум 2 символа"
    
    if len(department) > 100:
        return False, "Название отдела не может быть длиннее 100 символов"
    
    # Проверяем на допустимые символы
    if not re.match(r"^[a-zA-Zа-яА-ЯёЁ0-9\s\-.,()]+$", department):
        return False, "Название отдела содержит недопустимые символы"
    
    return True, None

def validate_position(position: str) -> Tuple[bool, Optional[str]]:
    """Валидация должности"""
    if not position:
        return True, None  # Должность может быть не указана
    
    position = position.strip()
    
    if len(position) < 2:
        return False, "Название должности должно содержать минимум 2 символа"
    
    if len(position) > 100:
        return False, "Название должности не может быть длиннее 100 символов"
    
    # Проверяем на допустимые символы
    if not re.match(r"^[a-zA-Zа-яА-ЯёЁ0-9\s\-.,()]+$", position):
        return False, "Название должности содержит недопустимые символы"
    
    return True, None

def validate_report_text(text: str, field_name: str, 
                        min_length: int = 10, max_length: int = 2000,
                        min_words: int = 3) -> Tuple[bool, Optional[str]]:
    """Валидация текста отчета"""
    if not text or not text.strip():
        return False, f"{field_name} не может быть пустым"
    
    text = text.strip()
    
    # Проверяем длину
    length_validation = validate_text_length(text, min_length, max_length)
    if not length_validation['valid']:
        return False, f"{field_name}: {', '.join(length_validation['errors'])}"
    
    # Проверяем количество слов
    word_count = count_words(text)
    if word_count < min_words:
        return False, f"{field_name} должно содержать минимум {min_words} слов"
    
    # Проверяем на спам (повторяющиеся символы)
    if re.search(r'(.)\1{10,}', text):  # 10+ одинаковых символов подряд
        return False, f"{field_name} содержит подозрительные повторения символов"
    
    # Проверяем на минимальное разнообразие символов
    unique_chars = len(set(text.lower().replace(' ', '')))
    if unique_chars < 5:
        return False, f"{field_name} должно содержать более разнообразный текст"
    
    return True, None

def validate_completed_tasks(tasks: str) -> Tuple[bool, Optional[str]]:
    """Валидация выполненных задач"""
    return validate_report_text(
        tasks, 
        "Выполненные задачи",
        min_length=20,
        max_length=2000,
        min_words=5
    )

def validate_achievements(achievements: str) -> Tuple[bool, Optional[str]]:
    """Валидация достижений"""
    return validate_report_text(
        achievements,
        "Достижения",
        min_length=10,
        max_length=1000,
        min_words=3
    )

def validate_problems(problems: str) -> Tuple[bool, Optional[str]]:
    """Валидация проблем"""
    # Проблемы могут быть пустыми
    if not problems or not problems.strip():
        return True, None
    
    return validate_report_text(
        problems,
        "Проблемы",
        min_length=5,
        max_length=1000,
        min_words=2
    )

def validate_next_week_plans(plans: str) -> Tuple[bool, Optional[str]]:
    """Валидация планов на следующую неделю"""
    return validate_report_text(
        plans,
        "Планы на следующую неделю",
        min_length=15,
        max_length=1500,
        min_words=4
    )

def validate_week_date(date: datetime) -> Tuple[bool, Optional[str]]:
    """Валидация даты недели"""
    if not isinstance(date, datetime):
        return False, "Дата должна быть объектом datetime"
    
    # Проверяем, что дата не слишком старая (не более года назад)
    now = datetime.now()
    year_ago = now.replace(year=now.year - 1)
    
    if date < year_ago:
        return False, "Дата не может быть старше года"
    
    # Проверяем, что дата не в будущем (не более недели вперед)
    week_ahead = now.replace(day=now.day + 7) if now.day <= 24 else now.replace(month=now.month + 1, day=7)
    
    if date > week_ahead:
        return False, "Дата не может быть более чем на неделю в будущем"
    
    return True, None

def validate_report_status(status: str) -> Tuple[bool, Optional[str]]:
    """Валидация статуса отчета"""
    valid_statuses = ['draft', 'submitted', 'processed']
    
    if status not in valid_statuses:
        return False, f"Статус должен быть одним из: {', '.join(valid_statuses)}"
    
    return True, None

def validate_email(email: str) -> Tuple[bool, Optional[str]]:
    """Валидация email адреса"""
    if not email:
        return True, None  # Email может быть пустым
    
    email = email.strip().lower()
    
    # Простая проверка формата email
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(email_pattern, email):
        return False, "Неверный формат email адреса"
    
    if len(email) > 254:  # RFC 5321
        return False, "Email адрес слишком длинный"
    
    return True, None

def validate_phone_number(phone: str) -> Tuple[bool, Optional[str]]:
    """Валидация номера телефона"""
    if not phone:
        return True, None  # Телефон может быть пустым
    
    # Убираем все кроме цифр и +
    clean_phone = re.sub(r'[^+\d]', '', phone)
    
    # Проверяем формат
    if not re.match(r'^\+?[1-9]\d{6,14}$', clean_phone):
        return False, "Неверный формат номера телефона"
    
    return True, None

def validate_bot_token(token: str) -> Tuple[bool, Optional[str]]:
    """Валидация токена Telegram бота"""
    if not token or not token.strip():
        return False, "Токен бота не может быть пустым"
    
    # Формат токена: число:строка_из_букв_и_цифр
    token_pattern = r'^\d+:[a-zA-Z0-9_-]+$'
    
    if not re.match(token_pattern, token):
        return False, "Неверный формат токена бота"
    
    # Проверяем длину
    if len(token) < 35 or len(token) > 50:
        return False, "Токен бота имеет неверную длину"
    
    return True, None

def validate_chat_id(chat_id: Any) -> Tuple[bool, Optional[str]]:
    """Валидация ID чата"""
    try:
        chat_id = int(chat_id)
        # Telegram chat ID может быть отрицательным для групп
        if abs(chat_id) > 2**63 - 1:
            return False, "Chat ID слишком большой"
        return True, None
    except (ValueError, TypeError):
        return False, "Chat ID должен быть числом"

def validate_url(url: str) -> Tuple[bool, Optional[str]]:
    """Валидация URL"""
    if not url or not url.strip():
        return False, "URL не может быть пустым"
    
    url = url.strip()
    
    # Простая проверка формата URL
    url_pattern = r'^https?://[a-zA-Z0-9.-]+(?:\.[a-zA-Z]{2,})?(?::\d+)?(?:/[^\s]*)?$'
    
    if not re.match(url_pattern, url):
        return False, "Неверный формат URL"
    
    if len(url) > 2048:
        return False, "URL слишком длинный"
    
    return True, None

def validate_timezone(timezone_str: str) -> Tuple[bool, Optional[str]]:
    """Валидация часового пояса"""
    if not timezone_str:
        return False, "Часовой пояс не может быть пустым"
    
    try:
        import pytz
        pytz.timezone(timezone_str)
        return True, None
    except pytz.UnknownTimeZoneError:
        return False, f"Неизвестный часовой пояс: {timezone_str}"
    except ImportError:
        logger.warning("Библиотека pytz не установлена, пропускаем валидацию часового пояса")
        return True, None

def validate_log_level(level: str) -> Tuple[bool, Optional[str]]:
    """Валидация уровня логирования"""
    valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    
    if not level:
        return False, "Уровень логирования не может быть пустым"
    
    level = level.upper()
    
    if level not in valid_levels:
        return False, f"Уровень логирования должен быть одним из: {', '.join(valid_levels)}"
    
    return True, None

def validate_admin_user_ids(user_ids_str: str) -> Tuple[bool, Optional[str]]:
    """Валидация списка ID администраторов"""
    if not user_ids_str or not user_ids_str.strip():
        return False, "Список администраторов не может быть пустым"
    
    # Разделяем по запятым
    user_ids = [uid.strip() for uid in user_ids_str.split(',')]
    
    for uid in user_ids:
        is_valid, error = validate_telegram_user_id(uid)
        if not is_valid:
            return False, f"Неверный ID администратора '{uid}': {error}"
    
    return True, None

def validate_report_data(data: Dict[str, Any]) -> Dict[str, List[str]]:
    """Комплексная валидация данных отчета
    
    Returns:
        Dict с ключами полей и списками ошибок для каждого поля
    """
    errors = {}
    
    # Валидация обязательных полей
    required_fields = {
        'user_id': validate_telegram_user_id,
        'full_name': validate_full_name,
        'completed_tasks': validate_completed_tasks,
        'achievements': validate_achievements,
        'next_week_plans': validate_next_week_plans
    }
    
    for field, validator in required_fields.items():
        value = data.get(field)
        is_valid, error = validator(value)
        if not is_valid:
            errors[field] = [error]
    
    # Валидация необязательных полей
    optional_fields = {
        'department': validate_department,
        'position': validate_position,
        'problems': validate_problems,
        'username': validate_telegram_username
    }
    
    for field, validator in optional_fields.items():
        value = data.get(field)
        if value is not None:
            is_valid, error = validator(value)
            if not is_valid:
                errors[field] = [error]
    
    return errors

def validate_employee_data(data: Dict[str, Any]) -> Dict[str, List[str]]:
    """Комплексная валидация данных сотрудника"""
    errors = {}
    
    # Валидация обязательных полей
    required_fields = {
        'user_id': validate_telegram_user_id,
        'full_name': validate_full_name
    }
    
    for field, validator in required_fields.items():
        value = data.get(field)
        is_valid, error = validator(value)
        if not is_valid:
            errors[field] = [error]
    
    # Валидация необязательных полей
    optional_fields = {
        'username': validate_telegram_username,
        'department': validate_department,
        'position': validate_position,
        'email': validate_email,
        'phone': validate_phone_number
    }
    
    for field, validator in optional_fields.items():
        value = data.get(field)
        if value is not None:
            is_valid, error = validator(value)
            if not is_valid:
                errors[field] = [error]
    
    return errors

def has_validation_errors(errors: Dict[str, List[str]]) -> bool:
    """Проверка наличия ошибок валидации"""
    return any(error_list for error_list in errors.values())

def format_validation_errors(errors: Dict[str, List[str]]) -> str:
    """Форматирование ошибок валидации в читаемый вид"""
    if not has_validation_errors(errors):
        return ""
    
    formatted_errors = []
    
    for field, error_list in errors.items():
        if error_list:
            field_name = {
                'user_id': 'ID пользователя',
                'full_name': 'Полное имя',
                'username': 'Имя пользователя',
                'department': 'Отдел',
                'position': 'Должность',
                'completed_tasks': 'Выполненные задачи',
                'achievements': 'Достижения',
                'problems': 'Проблемы',
                'next_week_plans': 'Планы на следующую неделю',
                'email': 'Email',
                'phone': 'Телефон'
            }.get(field, field)
            
            for error in error_list:
                formatted_errors.append(f"• {field_name}: {error}")
    
    return '\n'.join(formatted_errors)