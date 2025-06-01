import asyncio
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from loguru import logger

from models.report import WeeklyReport
from models.department import Employee, Department
from .ollama_service import OllamaService
from .telegram_service import TelegramService
from config import settings

class ReportProcessor:
    """Сервис для обработки и управления отчетами"""
    
    def __init__(self, ollama_service: OllamaService, telegram_service: TelegramService):
        self.ollama_service = ollama_service
        self.telegram_service = telegram_service
        self.reports_storage: List[WeeklyReport] = []  # В реальном проекте - база данных
        self.employees_storage: List[Employee] = []   # В реальном проекте - база данных
    
    async def process_new_report(self, report: WeeklyReport) -> bool:
        """Обработка нового отчета"""
        try:
            logger.info(f"Начало обработки отчета от пользователя {report.user_id}")
            
            # 1. Сохраняем отчет
            self.save_report(report)
            
            # 2. Отправляем подтверждение пользователю
            await self.telegram_service.send_report_confirmation(report.user_id, report)
            
            # 3. Обрабатываем через ИИ (если доступен)
            if await self.ollama_service.check_connection():
                processed_report = await self.ollama_service.process_report(report)
                self.update_report(processed_report)
            else:
                logger.warning("Ollama недоступен, отчет обработан без ИИ анализа")
                report.mark_as_processed(
                    summary="Автоматическая обработка недоступна",
                    analysis="ИИ анализ временно недоступен"
                )
                self.update_report(report)
            
            # 4. Отправляем в групповой чат
            await self.telegram_service.send_report_to_group(report)
            
            logger.info(f"Отчет пользователя {report.user_id} успешно обработан")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка обработки отчета пользователя {report.user_id}: {e}")
            # Уведомляем администраторов об ошибке
            await self.telegram_service.send_admin_notification(
                settings.admin_user_ids,
                f"Ошибка обработки отчета пользователя {report.user_id}: {str(e)}"
            )
            return False
    
    def save_report(self, report: WeeklyReport) -> None:
        """Сохранение отчета в хранилище"""
        # Проверяем, есть ли уже отчет от этого пользователя за эту неделю
        existing_report = self.get_user_report_for_week(report.user_id, report.week_start)
        
        if existing_report:
            # Обновляем существующий отчет
            existing_report.completed_tasks = report.completed_tasks
            existing_report.achievements = report.achievements
            existing_report.problems = report.problems
            existing_report.next_week_plans = report.next_week_plans
            existing_report.submitted_at = report.submitted_at
            existing_report.status = report.status
            logger.info(f"Обновлен существующий отчет пользователя {report.user_id}")
        else:
            # Добавляем новый отчет
            self.reports_storage.append(report)
            logger.info(f"Сохранен новый отчет пользователя {report.user_id}")
    
    def update_report(self, report: WeeklyReport) -> None:
        """Обновление существующего отчета"""
        for i, stored_report in enumerate(self.reports_storage):
            if (stored_report.user_id == report.user_id and 
                stored_report.week_start == report.week_start):
                self.reports_storage[i] = report
                logger.debug(f"Отчет пользователя {report.user_id} обновлен")
                return
        
        # Если отчет не найден, добавляем его
        self.reports_storage.append(report)
        logger.debug(f"Отчет пользователя {report.user_id} добавлен как новый")
    
    def get_user_report_for_week(self, user_id: int, week_start: datetime) -> Optional[WeeklyReport]:
        """Получение отчета пользователя за конкретную неделю"""
        for report in self.reports_storage:
            if report.user_id == user_id and report.week_start.date() == week_start.date():
                return report
        return None
    
    def get_user_reports(self, user_id: int, limit: int = 10) -> List[WeeklyReport]:
        """Получение отчетов пользователя"""
        user_reports = [r for r in self.reports_storage if r.user_id == user_id]
        user_reports.sort(key=lambda x: x.week_start, reverse=True)
        return user_reports[:limit]
    
    def get_reports_for_week(self, week_start: datetime) -> List[WeeklyReport]:
        """Получение всех отчетов за конкретную неделю"""
        return [r for r in self.reports_storage 
                if r.week_start.date() == week_start.date()]
    
    def get_reports_for_period(self, start_date: datetime, end_date: datetime) -> List[WeeklyReport]:
        """Получение отчетов за период"""
        return [r for r in self.reports_storage 
                if start_date.date() <= r.week_start.date() <= end_date.date()]
    
    def get_all_reports(self, limit: Optional[int] = None) -> List[WeeklyReport]:
        """Получение всех отчетов"""
        sorted_reports = sorted(self.reports_storage, key=lambda x: x.submitted_at, reverse=True)
        return sorted_reports[:limit] if limit else sorted_reports
    
    def get_statistics(self) -> Dict[str, any]:
        """Получение статистики по отчетам"""
        total_reports = len(self.reports_storage)
        
        # Статистика по статусам
        status_stats = {}
        for report in self.reports_storage:
            status_stats[report.status] = status_stats.get(report.status, 0) + 1
        
        # Статистика по отделам
        department_stats = {}
        for report in self.reports_storage:
            dept = report.department or 'Не указан'
            department_stats[dept] = department_stats.get(dept, 0) + 1
        
        # Статистика за последние недели
        now = datetime.now()
        week_stats = {}
        for i in range(4):  # Последние 4 недели
            week_start = now - timedelta(weeks=i)
            week_reports = self.get_reports_for_week(week_start)
            week_stats[f"week_{i}"] = len(week_reports)
        
        # Активные пользователи
        active_users = len(set(r.user_id for r in self.reports_storage 
                              if r.submitted_at >= now - timedelta(days=30)))
        
        return {
            'total_reports': total_reports,
            'status_distribution': status_stats,
            'department_distribution': department_stats,
            'weekly_stats': week_stats,
            'active_users_last_month': active_users,
            'total_users': len(self.employees_storage)
        }
    
    async def generate_weekly_summary(self, week_start: Optional[datetime] = None) -> str:
        """Генерация еженедельной сводки"""
        if not week_start:
            week_start = datetime.now() - timedelta(days=datetime.now().weekday())
        
        week_reports = self.get_reports_for_week(week_start)
        
        if not week_reports:
            return f"Отчеты за неделю {week_start.strftime('%d.%m.%Y')} отсутствуют."
        
        # Базовая статистика
        basic_summary = f"""📊 Сводка за неделю {week_start.strftime('%d.%m.%Y')} - {(week_start + timedelta(days=6)).strftime('%d.%m.%Y')}

📈 Общая статистика:
• Получено отчетов: {len(week_reports)}
• Зарегистрированных сотрудников: {len(self.employees_storage)}
• Процент сдачи: {len(week_reports) / max(len(self.employees_storage), 1) * 100:.1f}%

📋 По отделам:"""
        
        # Статистика по отделам
        dept_stats = {}
        for report in week_reports:
            dept = report.department or 'Не указан'
            dept_stats[dept] = dept_stats.get(dept, 0) + 1
        
        for dept, count in dept_stats.items():
            basic_summary += f"\n• {dept}: {count} отчетов"
        
        # Если доступен ИИ, генерируем расширенную сводку
        if await self.ollama_service.check_connection():
            ai_summary = await self.ollama_service.generate_weekly_summary(week_reports)
            return f"{basic_summary}\n\n🤖 ИИ Анализ:\n{ai_summary}"
        else:
            return basic_summary
    
    async def send_reminders_to_missing_users(self) -> Dict[str, int]:
        """Отправка напоминаний пользователям, не сдавшим отчеты"""
        # Определяем текущую неделю
        now = datetime.now()
        week_start = now - timedelta(days=now.weekday())
        
        # Получаем отчеты за текущую неделю
        week_reports = self.get_reports_for_week(week_start)
        submitted_user_ids = {r.user_id for r in week_reports}
        
        # Находим пользователей без отчетов
        missing_users = [emp for emp in self.employees_storage 
                        if emp.user_id not in submitted_user_ids]
        
        if not missing_users:
            return {'sent': 0, 'failed': 0, 'no_missing': True}
        
        # Отправляем напоминания
        results = await self.telegram_service.send_bulk_reminders(missing_users)
        
        logger.info(f"Отправлено напоминаний: {results['sent']} из {len(missing_users)}")
        return results
    
    def add_employee(self, employee: Employee) -> None:
        """Добавление сотрудника"""
        # Проверяем, есть ли уже такой сотрудник
        existing = self.get_employee_by_user_id(employee.user_id)
        if existing:
            # Обновляем информацию
            existing.full_name = employee.full_name
            existing.username = employee.username
            existing.department = employee.department
            existing.position = employee.position
            existing.is_active = employee.is_active
            logger.info(f"Обновлена информация о сотруднике {employee.user_id}")
        else:
            # Добавляем нового
            self.employees_storage.append(employee)
            logger.info(f"Добавлен новый сотрудник {employee.user_id}")
    
    def get_employee_by_user_id(self, user_id: int) -> Optional[Employee]:
        """Получение сотрудника по user_id"""
        for emp in self.employees_storage:
            if emp.user_id == user_id:
                return emp
        return None
    
    def get_all_employees(self) -> List[Employee]:
        """Получение всех сотрудников"""
        return self.employees_storage.copy()
    
    def get_employees_by_department(self, department: str) -> List[Employee]:
        """Получение сотрудников по отделу"""
        return [emp for emp in self.employees_storage if emp.department == department]
    
    async def export_reports_to_text(self, start_date: datetime, end_date: datetime) -> str:
        """Экспорт отчетов в текстовый формат"""
        reports = self.get_reports_for_period(start_date, end_date)
        
        if not reports:
            return "Отчеты за указанный период отсутствуют."
        
        export_text = f"""ЭКСПОРТ ОТЧЕТОВ
Период: {start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}
Всего отчетов: {len(reports)}
Сформировано: {datetime.now().strftime('%d.%m.%Y %H:%M')}

{'='*50}\n\n"""
        
        for i, report in enumerate(reports, 1):
            export_text += f"""ОТЧЕТ #{i}
Сотрудник: {report.full_name}
Отдел: {report.department or 'Не указан'}
Должность: {report.position or 'Не указана'}
Период: {report.get_week_string()}
Статус: {report.status}
Отправлено: {report.submitted_at.strftime('%d.%m.%Y %H:%M')}

Выполненные задачи:
{report.completed_tasks}

Достижения:
{report.achievements}

Проблемы:
{report.problems}

Планы на следующую неделю:
{report.next_week_plans}

{'-'*30}\n\n"""
        
        return export_text
    
    async def analyze_user_performance(self, user_id: int) -> str:
        """Анализ производительности пользователя"""
        user_reports = self.get_user_reports(user_id, limit=8)  # Последние 8 недель
        
        if not user_reports:
            return "Отчеты пользователя не найдены."
        
        # Базовая статистика
        employee = self.get_employee_by_user_id(user_id)
        employee_name = employee.full_name if employee else f"Пользователь {user_id}"
        
        basic_analysis = f"""📊 Анализ производительности: {employee_name}

📈 Статистика:
• Всего отчетов: {len(user_reports)}
• Период: {user_reports[-1].get_week_string()} - {user_reports[0].get_week_string()}
• Средняя длина отчета: {sum(len(r.completed_tasks) for r in user_reports) // len(user_reports)} символов
• Регулярность: {len(user_reports)} из последних 8 недель"""
        
        # Если доступен ИИ, добавляем детальный анализ
        if await self.ollama_service.check_connection():
            ai_analysis = await self.ollama_service.analyze_employee_performance(user_reports, user_id)
            return f"{basic_analysis}\n\n🤖 Детальный анализ:\n{ai_analysis}"
        else:
            return basic_analysis
    
    def cleanup_old_reports(self, days_to_keep: int = 90) -> int:
        """Очистка старых отчетов"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        initial_count = len(self.reports_storage)
        self.reports_storage = [r for r in self.reports_storage 
                               if r.submitted_at >= cutoff_date]
        
        removed_count = initial_count - len(self.reports_storage)
        
        if removed_count > 0:
            logger.info(f"Удалено {removed_count} старых отчетов")
        
        return removed_count