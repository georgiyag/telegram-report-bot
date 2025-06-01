from datetime import datetime, timedelta, timezone
from typing import Tuple, Optional
import pytz
from loguru import logger

from config import settings

def get_timezone() -> pytz.BaseTzInfo:
    """Получение часового пояса из настроек"""
    try:
        return pytz.timezone(settings.timezone)
    except pytz.UnknownTimeZoneError:
        logger.warning(f"Неизвестный часовой пояс {settings.timezone}, используется UTC")
        return pytz.UTC

def get_current_datetime() -> datetime:
    """Получение текущего времени в настроенном часовом поясе"""
    tz = get_timezone()
    return datetime.now(tz)

def get_current_week_range() -> Tuple[datetime, datetime]:
    """Получение диапазона текущей недели (понедельник - воскресенье)"""
    now = get_current_datetime()
    
    # Понедельник текущей недели
    monday = now - timedelta(days=now.weekday())
    monday = monday.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Воскресенье текущей недели
    sunday = monday + timedelta(days=6)
    sunday = sunday.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    return monday, sunday

def get_week_range(date: datetime) -> Tuple[datetime, datetime]:
    """Получение диапазона недели для указанной даты"""
    # Приводим к нужному часовому поясу если нужно
    if date.tzinfo is None:
        tz = get_timezone()
        date = tz.localize(date)
    elif date.tzinfo != get_timezone():
        date = date.astimezone(get_timezone())
    
    # Понедельник недели
    monday = date - timedelta(days=date.weekday())
    monday = monday.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Воскресенье недели
    sunday = monday + timedelta(days=6)
    sunday = sunday.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    return monday, sunday

def get_previous_week_range() -> Tuple[datetime, datetime]:
    """Получение диапазона предыдущей недели"""
    now = get_current_datetime()
    previous_week = now - timedelta(weeks=1)
    return get_week_range(previous_week)

def get_next_week_range() -> Tuple[datetime, datetime]:
    """Получение диапазона следующей недели"""
    now = get_current_datetime()
    next_week = now + timedelta(weeks=1)
    return get_week_range(next_week)

def format_week_range(start_date: datetime, end_date: datetime) -> str:
    """Форматирование диапазона недели в читаемый вид"""
    if start_date.month == end_date.month:
        # Если месяц одинаковый
        return f"{start_date.day}-{end_date.day} {start_date.strftime('%B %Y')}"
    elif start_date.year == end_date.year:
        # Если год одинаковый, но месяцы разные
        return f"{start_date.day} {start_date.strftime('%B')} - {end_date.day} {end_date.strftime('%B %Y')}"
    else:
        # Если годы разные
        return f"{start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}"

def format_datetime(dt: datetime, format_type: str = 'full') -> str:
    """Форматирование даты и времени
    
    Args:
        dt: Дата и время для форматирования
        format_type: Тип форматирования ('full', 'date', 'time', 'short')
    """
    if dt.tzinfo is None:
        tz = get_timezone()
        dt = tz.localize(dt)
    elif dt.tzinfo != get_timezone():
        dt = dt.astimezone(get_timezone())
    
    formats = {
        'full': '%d.%m.%Y %H:%M:%S',
        'date': '%d.%m.%Y',
        'time': '%H:%M:%S',
        'short': '%d.%m %H:%M',
        'datetime': '%d.%m.%Y %H:%M'
    }
    
    return dt.strftime(formats.get(format_type, formats['full']))

def parse_date_string(date_string: str, format_string: str = '%d.%m.%Y') -> Optional[datetime]:
    """Парсинг строки даты"""
    try:
        dt = datetime.strptime(date_string, format_string)
        tz = get_timezone()
        return tz.localize(dt)
    except ValueError as e:
        logger.error(f"Ошибка парсинга даты '{date_string}': {e}")
        return None

def is_weekend(date: datetime) -> bool:
    """Проверка, является ли дата выходным днем (суббота или воскресенье)"""
    return date.weekday() >= 5  # 5 = суббота, 6 = воскресенье

def is_working_day(date: datetime) -> bool:
    """Проверка, является ли дата рабочим днем"""
    return not is_weekend(date)

def get_working_days_in_week(start_date: datetime) -> int:
    """Получение количества рабочих дней в неделе"""
    monday, sunday = get_week_range(start_date)
    working_days = 0
    
    current_date = monday
    while current_date <= sunday:
        if is_working_day(current_date):
            working_days += 1
        current_date += timedelta(days=1)
    
    return working_days

def get_weeks_between_dates(start_date: datetime, end_date: datetime) -> int:
    """Получение количества недель между датами"""
    delta = end_date - start_date
    return delta.days // 7

def get_monday_of_week(date: datetime) -> datetime:
    """Получение понедельника недели для указанной даты"""
    monday = date - timedelta(days=date.weekday())
    return monday.replace(hour=0, minute=0, second=0, microsecond=0)

def get_sunday_of_week(date: datetime) -> datetime:
    """Получение воскресенья недели для указанной даты"""
    monday = get_monday_of_week(date)
    sunday = monday + timedelta(days=6)
    return sunday.replace(hour=23, minute=59, second=59, microsecond=999999)

def is_same_week(date1: datetime, date2: datetime) -> bool:
    """Проверка, находятся ли две даты в одной неделе"""
    monday1 = get_monday_of_week(date1)
    monday2 = get_monday_of_week(date2)
    return monday1.date() == monday2.date()

def get_week_number(date: datetime) -> int:
    """Получение номера недели в году"""
    return date.isocalendar()[1]

def get_year_week_string(date: datetime) -> str:
    """Получение строки вида '2024-W15' для недели"""
    year, week, _ = date.isocalendar()
    return f"{year}-W{week:02d}"

def convert_to_utc(dt: datetime) -> datetime:
    """Конвертация времени в UTC"""
    if dt.tzinfo is None:
        tz = get_timezone()
        dt = tz.localize(dt)
    
    return dt.astimezone(pytz.UTC)

def convert_from_utc(dt: datetime) -> datetime:
    """Конвертация времени из UTC в локальный часовой пояс"""
    if dt.tzinfo is None:
        dt = pytz.UTC.localize(dt)
    
    tz = get_timezone()
    return dt.astimezone(tz)

def get_deadline_datetime() -> datetime:
    """Получение времени дедлайна для отчетов
    
    Парсит строку из настроек типа 'Friday 18:00' и возвращает datetime
    для ближайшего такого времени
    """
    try:
        # Парсим строку дедлайна (например, "Friday 18:00")
        deadline_parts = settings.report_deadline.split()
        if len(deadline_parts) != 2:
            raise ValueError("Неверный формат дедлайна")
        
        day_name, time_str = deadline_parts
        
        # Словарь дней недели
        days = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6
        }
        
        target_weekday = days.get(day_name.lower())
        if target_weekday is None:
            raise ValueError(f"Неизвестный день недели: {day_name}")
        
        # Парсим время
        hour, minute = map(int, time_str.split(':'))
        
        # Получаем текущее время
        now = get_current_datetime()
        
        # Вычисляем дату ближайшего дедлайна
        days_ahead = target_weekday - now.weekday()
        if days_ahead <= 0:  # Если день уже прошел на этой неделе
            days_ahead += 7
        
        deadline = now + timedelta(days=days_ahead)
        deadline = deadline.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        return deadline
        
    except Exception as e:
        logger.error(f"Ошибка парсинга дедлайна '{settings.report_deadline}': {e}")
        # Возвращаем пятницу 18:00 по умолчанию
        now = get_current_datetime()
        days_ahead = 4 - now.weekday()  # 4 = пятница
        if days_ahead <= 0:
            days_ahead += 7
        
        deadline = now + timedelta(days=days_ahead)
        return deadline.replace(hour=18, minute=0, second=0, microsecond=0)

def time_until_deadline() -> timedelta:
    """Получение времени до дедлайна"""
    deadline = get_deadline_datetime()
    now = get_current_datetime()
    return deadline - now

def is_deadline_passed() -> bool:
    """Проверка, прошел ли дедлайн"""
    return time_until_deadline().total_seconds() <= 0

def format_time_delta(delta: timedelta) -> str:
    """Форматирование временного интервала в читаемый вид"""
    total_seconds = int(delta.total_seconds())
    
    if total_seconds < 0:
        return "Время истекло"
    
    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60
    
    if days > 0:
        return f"{days} дн. {hours} ч. {minutes} мин."
    elif hours > 0:
        return f"{hours} ч. {minutes} мин."
    else:
        return f"{minutes} мин."

def get_report_period_string(date: datetime) -> str:
    """Получение строки периода отчета для указанной даты"""
    monday, sunday = get_week_range(date)
    return format_week_range(monday, sunday)