import os
from typing import List, Optional
from dotenv import load_dotenv
from pydantic import field_validator
from pydantic_settings import BaseSettings
import pytz

# Загрузка переменных окружения
load_dotenv()

class Settings(BaseSettings):
    """Настройки приложения"""
    
    # Telegram Bot Configuration
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    group_chat_id: str = os.getenv("GROUP_CHAT_ID", "")
    thread_id: Optional[int] = None
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Преобразование thread_id из строки в int
        thread_id_str = os.getenv("THREAD_ID", "")
        if thread_id_str and thread_id_str.isdigit():
            self.thread_id = int(thread_id_str)
        else:
            self.thread_id = None
    
    # Ollama Configuration
    ollama_url: str = os.getenv("OLLAMA_URL", "http://localhost:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "gemma3:4b")
    
    # Application Settings
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    timezone: str = os.getenv("TIMEZONE", "Europe/Moscow")
    
    # Admin Settings
    admin_user_ids: str = os.getenv("ADMIN_USER_IDS", "")
    
    # Report Settings
    report_deadline: str = os.getenv("REPORT_DEADLINE", "Friday 18:00")
    
    # Database
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///reports.db")
    
    def get_admin_ids(self) -> List[int]:
        """Получить список ID администраторов"""
        if not self.admin_user_ids:
            return []
        return [int(x.strip()) for x in self.admin_user_ids.split(',') if x.strip().isdigit()]
    
    def get_timezone(self) -> pytz.BaseTzInfo:
        """Получить объект временной зоны"""
        try:
            return pytz.timezone(self.timezone)
        except pytz.exceptions.UnknownTimeZoneError:
            return pytz.timezone('Europe/Moscow')
    
    @field_validator('telegram_bot_token')
    def validate_bot_token(cls, v):
        if not v:
            raise ValueError('TELEGRAM_BOT_TOKEN is required')
        return v
    
    @field_validator('group_chat_id')
    def validate_group_chat_id(cls, v):
        if not v:
            raise ValueError('GROUP_CHAT_ID is required')
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

# Создание экземпляра настроек
settings = Settings()

# Константы для бота
COMPANY_NAME = "АО ЭМЗ ФИРМА СЭЛМА"
REPORT_DEADLINE_DAY = 5  # Пятница
REPORT_DEADLINE_HOUR = 18  # 18:00

# Список отделов компании
DEPARTMENTS = [
    "ОТК",
    "ОК",
    "ОГК",
    "ОГТ",
    "ОМТС",
    "ПЭО",
    "РСУ",
    "ЭМО",
    "IT отдел",
    "ИЛ",
    "БИК"
]

# Сообщения бота
MESSAGES = {
    "welcome": "Добро пожаловать в систему отчетности АО ЭМЗ \"ФИРМА СЭЛМА\"!\n\n"
               "Этот бот поможет вам отправлять еженедельные отчеты.\n\n"
               "Используйте кнопки меню для навигации.",
    
    "help": "📋 <b>Система еженедельных отчетов</b>\n\n"
            "🔹 Создайте отчет, нажав кнопку 'Создать отчет'\n"
            "🔹 Проверьте статус отчета\n"
            "🔹 Проверьте статус обработки отчета (/task_status)\n"
            "🔹 Получите помощь по использованию системы\n\n"
            "💡 Отчеты необходимо отправлять каждую пятницу до 18:00",
    
    "report_created": "✅ Отчет успешно создан и отправлен!",
    "report_exists": "ℹ️ Вы уже отправили отчет на эту неделю.",
    "report_deadline_passed": "⚠️ Срок подачи отчета истек.",
    
    "cancel": "❌ Операция отменена. Возвращаемся в главное меню.",
    "back_to_main": "🏠 Возвращаемся в главное меню",
    
    "admin_access_denied": "❌ У вас нет прав администратора.",
    "admin_welcome": "👨‍💼 Добро пожаловать в панель администратора!",
    
    "error_general": "❌ Произошла ошибка. Попробуйте позже.",
    "error_invalid_input": "❌ Некорректный ввод. Попробуйте еще раз.",
    
    "menu_main": "🏠 <b>Главное меню</b>\n\nВыберите действие:",
    "menu_report": "📋 <b>Создание отчета</b>\n\nВыберите действие:",
    "menu_admin": "👨‍💼 <b>Панель администратора</b>\n\nВыберите действие:",
    
    "menu_help_extended": "📖 <b>Справка по системе</b>\n\n"
                          "🔹 <b>Создать отчет</b> - отправить еженедельный отчет\n"
                          "🔹 <b>Статус отчета</b> - проверить статус текущего отчета\n"
                          "🔹 <b>Помощь</b> - показать эту справку\n\n"
                          "Для администраторов:\n"
                          "🔹 <b>Панель администратора</b> - управление системой\n\n"
                          "💡 Используйте кнопки для навигации по системе.",
    
    "unknown_command": "❓ Неизвестная команда.\n\n"
                       "Используйте кнопки ниже для навигации:"
}