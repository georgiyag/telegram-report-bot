"""Сервисы для работы с внешними API и обработки данных"""

from .ollama_service import OllamaService
from .telegram_service import TelegramService
from .report_processor import ReportProcessor
from .task_manager import TaskManager, TaskStatus, TaskInfo

__all__ = [
    'OllamaService',
    'TelegramService', 
    'ReportProcessor',
    'TaskManager',
    'TaskStatus',
    'TaskInfo'
]