"""Пакет моделей данных для Telegram бота отчетности"""

from .report import WeeklyReport
from .department import Department, Employee

__all__ = [
    'WeeklyReport',
    'Department',
    'Employee'
]