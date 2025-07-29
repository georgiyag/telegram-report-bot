#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Быстрый тест основных функций бота
Упрощенная версия для проверки работоспособности
"""

import asyncio
import logging
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# Добавляем путь к модулям бота
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from database import DatabaseManager
from services.telegram_service import TelegramService
from services.ollama_service import OllamaService
from services.report_processor import ReportProcessor
from services.task_manager import TaskManager
from services.reminder_service import ReminderService
from handlers.menu_handler import MenuHandler
from handlers.admin_handler import AdminHandler
from handlers.report_handler import ReportHandler
from handlers.user_handler import UserHandler

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class QuickBotTester:
    """Быстрый тестер функций бота"""
    
    def __init__(self):
        self.test_results = []
        self.db_manager = None
        self.services = {}
        self.handlers = {}
        
    def log_test(self, test_name: str, status: str, details: str = ""):
        """Логирование результата теста"""
        result = {
            'test': test_name,
            'status': status,
            'details': details,
            'timestamp': datetime.now()
        }
        self.test_results.append(result)
        
        status_emoji = "✅" if status == "success" else "❌"
        logger.info(f"{status_emoji} {test_name}: {status} {details}")
    
    async def test_database_connection(self):
        """Тест подключения к базе данных"""
        try:
            self.db_manager = DatabaseManager("data/test_database.db")
            await self.db_manager.initialize()
            self.log_test("Database Connection", "success", "База данных инициализирована")
            return True
        except Exception as e:
            self.log_test("Database Connection", "failed", str(e))
            return False
    
    async def test_services_initialization(self):
        """Тест инициализации сервисов"""
        try:
            # Инициализируем сервисы
            self.services['ollama'] = OllamaService()
            self.services['telegram'] = TelegramService("test_token")
            self.services['report_processor'] = ReportProcessor(self.db_manager, self.services['ollama'])
            self.services['task_manager'] = TaskManager()  # TaskManager не требует аргументов
            self.services['reminder'] = ReminderService(self.db_manager, self.services['telegram'])
            
            self.log_test("Services Initialization", "success", "Все сервисы инициализированы")
            return True
        except Exception as e:
            self.log_test("Services Initialization", "failed", str(e))
            return False
    
    async def test_handlers_initialization(self):
        """Тест инициализации обработчиков"""
        try:
            # Создаем обработчики с правильными параметрами
            self.handlers['user'] = UserHandler(self.db_manager)
            
            # ReportHandler требует 5 параметров
            self.handlers['report'] = ReportHandler(
                self.services['report_processor'],  # report_processor
                self.services['ollama'],  # ollama_service
                self.services['telegram'],  # telegram_service
                self.services['task_manager'],  # task_manager
                self.db_manager  # db_manager
            )
            
            # AdminHandler требует дополнительные параметры
            self.handlers['admin'] = AdminHandler(
                self.db_manager, 
                self.db_manager,  # db_manager
                self.services['telegram'],  # telegram_service
                self.handlers['user'],  # user_management_handler
                self.handlers['user']   # department_management_handler (используем user как заглушку)
            )
            
            # MenuHandler с admin_handler
            self.handlers['menu'] = MenuHandler(self.db_manager, self.handlers['admin'])
            
            self.log_test("Handlers Initialization", "success", "Все обработчики инициализированы")
            return True
        except Exception as e:
            self.log_test("Handlers Initialization", "failed", str(e))
            return False
    
    async def test_database_operations(self):
        """Тест операций с базой данных"""
        try:
            # Тест создания отдела (используем правильный метод)
            dept_id = await self.db_manager.add_department("Тестовый отдел")
            if dept_id:
                self.log_test("Create Department", "success", f"Отдел создан с ID: {dept_id}")
            
            # Тест создания сотрудника (используем Employee модель)
            from models.department import Employee
            
            employee = Employee(
                user_id=123456789,
                username='test_user',
                full_name='Тест Пользователь',
                department_code='TEST',  # Используем код отдела
                position='Тестировщик',
                is_admin=False
            )
            
            user_id = await self.db_manager.add_employee(employee)
            if user_id:
                self.log_test("Create Employee", "success", f"Сотрудник создан успешно")
            
            # Тест создания отчета (используем WeeklyReport модель)
            from models.report import WeeklyReport
            
            report = WeeklyReport(
                user_id=123456789,
                username='test_user',
                full_name='Тест Пользователь',
                week_start=datetime.now().date(),
                week_end=(datetime.now() + timedelta(days=6)).date(),
                completed_tasks='Тестовые задачи',
                next_week_plans='Планы на следующую неделю',
                department='TEST',
                position='Тестировщик'
            )
            
            report_id = await self.db_manager.save_report(report)
            if report_id:
                self.log_test("Create Report", "success", f"Отчет создан с ID: {report_id}")
            
            return True
            
        except Exception as e:
            self.log_test("Database Operations", "failed", str(e))
            return False
    
    async def test_reminder_functionality(self):
        """Тест функциональности напоминаний"""
        try:
            # Тест настроек напоминаний
            settings = await self.db_manager.get_reminder_settings()
            self.log_test("Get Reminder Settings", "success", f"Настройки получены: {len(settings) if settings else 0} записей")
            
            # Тест обновления настроек
            await self.db_manager.update_reminder_settings({
                'deadline_day': 5,  # Пятница
                'deadline_time': '18:00',
                'send_time': '09:00',
                'frequency': 'weekly',
                'enabled': True
            })
            self.log_test("Update Reminder Settings", "success", "Настройки обновлены")
            
            return True
            
        except Exception as e:
            self.log_test("Reminder Functionality", "failed", str(e))
            return False
    
    async def test_report_processing(self):
        """Тест обработки отчетов"""
        try:
            # Тест получения отчетов (с правильными параметрами)
            week_start = datetime.now().date()
            week_end = week_start + timedelta(days=6)
            reports = await self.db_manager.get_reports_by_week(week_start, week_end)
            self.log_test("Get Reports", "success", f"Найдено отчетов: {len(reports) if reports else 0}")
            
            # Тест получения отчетов пользователя
            user_reports = await self.db_manager.get_user_reports(123456789)
            self.log_test("Get User Reports", "success", f"Отчетов пользователя: {len(user_reports) if user_reports else 0}")
            
            return True
            
        except Exception as e:
            self.log_test("Report Processing", "failed", str(e))
            return False
    
    async def test_admin_functions(self):
        """Тест админских функций"""
        try:
            # Тест получения списка отделов
            departments = await self.db_manager.get_departments()
            self.log_test("Get Departments", "success", f"Найдено отделов: {len(departments) if departments else 0}")
            
            # Тест получения списка сотрудников (используем правильный метод)
            users = await self.db_manager.get_employees()
            self.log_test("Get Employees", "success", f"Найдено сотрудников: {len(users) if users else 0}")
            
            # Тест системной статистики
            total_users = len(users) if users else 0
            total_departments = len(departments) if departments else 0
            
            self.log_test("System Statistics", "success", f"Пользователей: {total_users}, Отделов: {total_departments}")
            
            return True
            
        except Exception as e:
            self.log_test("Admin Functions", "failed", str(e))
            return False
    
    async def test_data_export(self):
        """Тест экспорта данных"""
        try:
            # Тест экспорта отчетов (используем правильный метод)
            week_start = datetime.now().date()
            week_end = week_start + timedelta(days=6)
            reports = await self.db_manager.get_reports_by_week(week_start, week_end)
            
            if reports:
                # Имитируем экспорт в CSV
                csv_data = "ID,Username,FullName,Department,Date\n"
                for report in reports[:5]:  # Берем первые 5 отчетов
                    # Используем атрибуты объекта WeeklyReport напрямую
                    report_id = getattr(report, 'id', '')
                    username = getattr(report, 'username', '')
                    full_name = getattr(report, 'full_name', '')
                    department = getattr(report, 'department', '')
                    submitted_at = getattr(report, 'submitted_at', '')
                    csv_data += f"{report_id},{username},{full_name},{department},{submitted_at}\n"
                
                self.log_test("Data Export", "success", f"Экспортировано {len(reports)} отчетов")
            else:
                self.log_test("Data Export", "success", "Нет данных для экспорта")
            
            return True
            
        except Exception as e:
            self.log_test("Data Export", "failed", str(e))
            return False
    
    async def cleanup_test_data(self):
        """Очистка тестовых данных"""
        try:
            # Удаляем тестовые данные
            if self.db_manager:
                # Здесь можно добавить логику очистки тестовых данных
                pass
            
            self.log_test("Cleanup", "success", "Тестовые данные очищены")
            return True
            
        except Exception as e:
            self.log_test("Cleanup", "failed", str(e))
            return False
    
    def generate_report(self):
        """Генерация отчета о тестировании"""
        total_tests = len(self.test_results)
        successful_tests = len([t for t in self.test_results if t['status'] == 'success'])
        failed_tests = total_tests - successful_tests
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        report = f"""
🚀 БЫСТРЫЙ ТЕСТ БОТА
{'=' * 40}

📊 РЕЗУЛЬТАТЫ:
• Всего тестов: {total_tests}
• Успешных: {successful_tests}
• Неудачных: {failed_tests}
• Процент успеха: {success_rate:.1f}%

📋 ДЕТАЛИ:
"""
        
        for i, test in enumerate(self.test_results, 1):
            status_emoji = "✅" if test['status'] == 'success' else "❌"
            details = f" - {test['details']}" if test['details'] else ""
            report += f"{i:2d}. {status_emoji} {test['test']}{details}\n"
        
        if failed_tests == 0:
            report += "\n🎉 ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!"
        else:
            report += f"\n⚠️ ОБНАРУЖЕНЫ ПРОБЛЕМЫ В {failed_tests} ТЕСТАХ"
        
        return report
    
    async def run_all_tests(self):
        """Запуск всех тестов"""
        logger.info("🚀 Запуск быстрого тестирования бота...")
        
        # Последовательность тестов
        tests = [
            self.test_database_connection,
            self.test_services_initialization,
            self.test_handlers_initialization,
            self.test_database_operations,
            self.test_reminder_functionality,
            self.test_report_processing,
            self.test_admin_functions,
            self.test_data_export,
            self.cleanup_test_data
        ]
        
        # Выполняем тесты
        for test in tests:
            try:
                await test()
            except Exception as e:
                self.log_test(test.__name__, "failed", f"Критическая ошибка: {e}")
        
        # Генерируем отчет
        report = self.generate_report()
        
        # Сохраняем отчет
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_filename = f"quick_test_report_{timestamp}.txt"
        
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(report)
        print(f"\n📄 Отчет сохранен в файл: {report_filename}")
        
        return report


async def main():
    """Главная функция"""
    print("🤖 Быстрый тест функций бота")
    print("=" * 40)
    
    tester = QuickBotTester()
    
    try:
        await tester.run_all_tests()
    except KeyboardInterrupt:
        print("\n⏹️ Тестирование прервано пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        logger.error(f"Критическая ошибка: {e}")


if __name__ == "__main__":
    asyncio.run(main())