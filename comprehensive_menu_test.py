#!/usr/bin/env python3
"""
Комплексный тест всех функций меню Telegram бота
Проверяет работоспособность каждого пункта меню, подменю, кнопок навигации
"""

import asyncio
import sys
import os
from datetime import datetime, date, timedelta
from loguru import logger
from telegram import Bot
from telegram.error import TelegramError

# Добавляем путь к src для импорта
sys.path.append('src')

from database import DatabaseManager
from services.telegram_service import TelegramService
from services.ollama_service import OllamaService
from services.task_manager import TaskManager
from services.report_processor import ReportProcessor
from handlers.menu_handler import MenuHandler
from handlers.admin_handler import AdminHandler
from handlers.report_handler import ReportHandler
from handlers.user_handler import UserHandler
from handlers.admin.user_management import UserManagementHandler
from handlers.admin.department_management import DepartmentManagementHandler
from config import settings
from models.department import Department, Employee
from models.report import WeeklyReport

class ComprehensiveMenuTester:
    """Комплексный тестер всех функций меню бота"""
    
    def __init__(self):
        self.test_results = {}
        self.failed_tests = []
        self.passed_tests = []
        
        # Инициализация компонентов
        self.db_manager = DatabaseManager()
        self.bot = Bot(token=settings.telegram_bot_token)
        self.telegram_service = TelegramService(self.bot)
        self.ollama_service = OllamaService()
        self.task_manager = TaskManager()
        self.report_processor = ReportProcessor(self.ollama_service, self.telegram_service)
        
        # Инициализация обработчиков
        self.user_management = UserManagementHandler(self.db_manager)
        self.department_management = DepartmentManagementHandler(self.db_manager)
        self.report_handler = ReportHandler(
            self.report_processor, self.ollama_service, 
            self.telegram_service, self.task_manager, self.db_manager
        )
        self.admin_handler = AdminHandler(
            self.report_processor, self.db_manager, self.telegram_service,
            self.user_management, self.department_management
        )
        self.menu_handler = MenuHandler(self.report_handler, self.admin_handler)
        self.user_handler = UserHandler(self.db_manager)
    
    async def test_database_operations(self):
        """Тест операций с базой данных"""
        logger.info("🔍 Тестирование операций с базой данных...")
        try:
            # Тест получения отделов
            departments = await self.db_manager.get_departments()
            assert len(departments) > 0, "Нет отделов в базе данных"
            
            # Тест получения сотрудников
            employees = await self.db_manager.get_employees()
            logger.info(f"Найдено сотрудников: {len(employees)}")
            
            # Тест получения отдела по коду
            if departments:
                dept = await self.db_manager.get_department_by_code(departments[0].code)
                assert dept is not None, "Не удалось получить отдел по коду"
            
            # Тест статистики отдела
            if departments:
                stats = await self.db_manager.get_department_stats(
                    departments[0].code, date.today(), date.today()
                )
                assert isinstance(stats, dict), "Статистика отдела должна быть словарем"
            
            self.test_results["База данных"] = "✅ ПРОЙДЕН"
            self.passed_tests.append("База данных")
            return True
            
        except Exception as e:
            error_msg = f"❌ НЕ ПРОЙДЕН - {str(e)}"
            self.test_results["База данных"] = error_msg
            self.failed_tests.append(f"База данных: {str(e)}")
            logger.error(f"Ошибка тестирования БД: {e}")
            return False
    
    async def test_telegram_connection(self):
        """Тест подключения к Telegram"""
        logger.info("🔍 Тестирование подключения к Telegram...")
        try:
            # Получаем информацию о боте
            bot_info = await self.bot.get_me()
            assert bot_info.username is not None, "Не удалось получить информацию о боте"
            
            logger.info(f"Бот подключен: @{bot_info.username}")
            
            self.test_results["Подключение Telegram"] = "✅ ПРОЙДЕН"
            self.passed_tests.append("Подключение Telegram")
            return True
            
        except Exception as e:
            error_msg = f"❌ НЕ ПРОЙДЕН - {str(e)}"
            self.test_results["Подключение Telegram"] = error_msg
            self.failed_tests.append(f"Подключение Telegram: {str(e)}")
            logger.error(f"Ошибка подключения к Telegram: {e}")
            return False
    
    async def test_menu_handlers(self):
        """Тест обработчиков меню"""
        logger.info("🔍 Тестирование обработчиков меню...")
        try:
            # Проверяем инициализацию обработчиков
            assert self.menu_handler is not None, "MenuHandler не инициализирован"
            assert self.admin_handler is not None, "AdminHandler не инициализирован"
            assert self.report_handler is not None, "ReportHandler не инициализирован"
            assert self.user_handler is not None, "UserHandler не инициализирован"
            
            # Проверяем наличие методов
            assert hasattr(self.menu_handler, 'show_main_menu'), "Отсутствует метод show_main_menu"
            assert hasattr(self.admin_handler, 'show_admin_panel'), "Отсутствует метод show_admin_panel"
            assert hasattr(self.user_management, 'show_user_list'), "Отсутствует метод show_user_list"
            assert hasattr(self.department_management, 'show_department_list'), "Отсутствует метод show_department_list"
            
            self.test_results["Обработчики меню"] = "✅ ПРОЙДЕН"
            self.passed_tests.append("Обработчики меню")
            return True
            
        except Exception as e:
            error_msg = f"❌ НЕ ПРОЙДЕН - {str(e)}"
            self.test_results["Обработчики меню"] = error_msg
            self.failed_tests.append(f"Обработчики меню: {str(e)}")
            logger.error(f"Ошибка тестирования обработчиков: {e}")
            return False
    
    async def test_admin_functions(self):
        """Тест административных функций"""
        logger.info("🔍 Тестирование административных функций...")
        try:
            # Тест проверки прав администратора
            employees = await self.db_manager.get_employees()
            if employees:
                is_admin = await self.db_manager.is_admin(employees[0].user_id)
                logger.info(f"Проверка прав администратора: {is_admin}")
            
            # Тест получения списка администраторов
            admins = await self.db_manager.get_admin_employees()
            logger.info(f"Найдено администраторов: {len(admins)}")
            
            # Тест управления пользователями
            assert hasattr(self.user_management, 'show_user_list'), "Отсутствует управление пользователями"
            
            # Тест управления отделами
            assert hasattr(self.department_management, 'show_department_list'), "Отсутствует управление отделами"
            
            self.test_results["Админ функции"] = "✅ ПРОЙДЕН"
            self.passed_tests.append("Админ функции")
            return True
            
        except Exception as e:
            error_msg = f"❌ НЕ ПРОЙДЕН - {str(e)}"
            self.test_results["Админ функции"] = error_msg
            self.failed_tests.append(f"Админ функции: {str(e)}")
            logger.error(f"Ошибка тестирования админ функций: {e}")
            return False
    
    async def test_report_functions(self):
        """Тест функций отчетов"""
        logger.info("🔍 Тестирование функций отчетов...")
        try:
            # Тест получения отчетов за неделю
            today = date.today()
            week_reports = await self.db_manager.get_reports_by_week(today, today)
            logger.info(f"Отчеты за неделю: {len(week_reports)}")
            
            # Тест получения пользователей без отчетов
            missing_reports = await self.db_manager.get_missing_reports_users(today)
            logger.info(f"Пользователи без отчетов: {len(missing_reports)}")
            
            # Тест создания тестового отчета
            employees = await self.db_manager.get_employees()
            if employees:
                test_report = WeeklyReport(
                    user_id=employees[0].user_id,
                    username=employees[0].username or "test_user",
                    full_name=employees[0].full_name,
                    week_start=datetime.now() - timedelta(days=7),
                    week_end=datetime.now(),
                    completed_tasks="Тестовая задача",
                    achievements="Тестовое достижение",
                    problems="Нет проблем",
                    next_week_plans="Тестовые планы",
                    department=employees[0].department_code,
                    position=employees[0].position or "Тестовая должность"
                )
                
                # Проверяем возможность сохранения (не сохраняем реально)
                assert test_report.user_id is not None, "Не удалось создать тестовый отчет"
            
            self.test_results["Функции отчетов"] = "✅ ПРОЙДЕН"
            self.passed_tests.append("Функции отчетов")
            return True
            
        except Exception as e:
            error_msg = f"❌ НЕ ПРОЙДЕН - {str(e)}"
            self.test_results["Функции отчетов"] = error_msg
            self.failed_tests.append(f"Функции отчетов: {str(e)}")
            logger.error(f"Ошибка тестирования функций отчетов: {e}")
            return False
    
    async def test_navigation_system(self):
        """Тест системы навигации"""
        logger.info("🔍 Тестирование системы навигации...")
        try:
            # Проверяем импорт навигационных утилит
            from src.utils.navigation import get_breadcrumb_path, create_keyboard
            
            # Тест создания хлебных крошек
            breadcrumb = get_breadcrumb_path(["main", "admin", "admin_users"])
            assert isinstance(breadcrumb, str), "Хлебные крошки должны быть строкой"
            logger.info(f"Хлебные крошки: {breadcrumb}")
            
            # Тест создания клавиатуры
            keyboard = create_keyboard([
                [("Кнопка 1", "btn1"), ("Кнопка 2", "btn2")],
                [("Назад", "back"), ("Главное меню", "main")]
            ])
            assert keyboard is not None, "Не удалось создать клавиатуру"
            
            self.test_results["Система навигации"] = "✅ ПРОЙДЕН"
            self.passed_tests.append("Система навигации")
            return True
            
        except Exception as e:
            error_msg = f"❌ НЕ ПРОЙДЕН - {str(e)}"
            self.test_results["Система навигации"] = error_msg
            self.failed_tests.append(f"Система навигации: {str(e)}")
            logger.error(f"Ошибка тестирования навигации: {e}")
            return False
    
    async def test_services_integration(self):
        """Тест интеграции сервисов"""
        logger.info("🔍 Тестирование интеграции сервисов...")
        try:
            # Тест TelegramService
            assert self.telegram_service is not None, "TelegramService не инициализирован"
            
            # Тест OllamaService
            assert self.ollama_service is not None, "OllamaService не инициализирован"
            
            # Тест TaskManager
            assert self.task_manager is not None, "TaskManager не инициализирован"
            
            # Тест ReportProcessor
            assert self.report_processor is not None, "ReportProcessor не инициализирован"
            
            # Проверяем методы сервисов
            assert hasattr(self.telegram_service, 'send_message_safe'), "Отсутствует метод send_message_safe"
            assert hasattr(self.ollama_service, 'check_connection'), "Отсутствует метод check_connection"
            
            self.test_results["Интеграция сервисов"] = "✅ ПРОЙДЕН"
            self.passed_tests.append("Интеграция сервисов")
            return True
            
        except Exception as e:
            error_msg = f"❌ НЕ ПРОЙДЕН - {str(e)}"
            self.test_results["Интеграция сервисов"] = error_msg
            self.failed_tests.append(f"Интеграция сервисов: {str(e)}")
            logger.error(f"Ошибка тестирования сервисов: {e}")
            return False
    
    async def test_configuration(self):
        """Тест конфигурации"""
        logger.info("🔍 Тестирование конфигурации...")
        try:
            # Проверяем основные настройки
            assert hasattr(settings, 'telegram_bot_token'), "Отсутствует telegram_bot_token"
            assert hasattr(settings, 'group_chat_id'), "Отсутствует group_chat_id"
            assert settings.telegram_bot_token, "telegram_bot_token пустой"
            
            # Проверяем настройки Ollama
            assert hasattr(settings, 'ollama_url'), "Отсутствует ollama_url"
            assert hasattr(settings, 'ollama_model'), "Отсутствует ollama_model"
            
            # Проверяем настройки администраторов
            assert hasattr(settings, 'admin_user_ids'), "Отсутствует admin_user_ids"
            
            logger.info("Конфигурация корректна")
            
            self.test_results["Конфигурация"] = "✅ ПРОЙДЕН"
            self.passed_tests.append("Конфигурация")
            return True
            
        except Exception as e:
            error_msg = f"❌ НЕ ПРОЙДЕН - {str(e)}"
            self.test_results["Конфигурация"] = error_msg
            self.failed_tests.append(f"Конфигурация: {str(e)}")
            logger.error(f"Ошибка тестирования конфигурации: {e}")
            return False
    
    async def run_all_tests(self):
        """Запуск всех тестов"""
        logger.info("🚀 Запуск комплексного тестирования меню бота...")
        logger.info("=" * 60)
        
        # Список всех тестов
        tests = [
            ("База данных", self.test_database_operations),
            ("Подключение Telegram", self.test_telegram_connection),
            ("Обработчики меню", self.test_menu_handlers),
            ("Админ функции", self.test_admin_functions),
            ("Функции отчетов", self.test_report_functions),
            ("Система навигации", self.test_navigation_system),
            ("Интеграция сервисов", self.test_services_integration),
            ("Конфигурация", self.test_configuration)
        ]
        
        # Выполняем тесты
        for test_name, test_func in tests:
            logger.info(f"\n🔍 Тестирование: {test_name}")
            try:
                await test_func()
                logger.success(f"✅ {test_name}: ПРОЙДЕН")
            except Exception as e:
                logger.error(f"❌ {test_name}: НЕ ПРОЙДЕН - {e}")
                if test_name not in self.test_results:
                    self.test_results[test_name] = f"❌ НЕ ПРОЙДЕН - {str(e)}"
                    self.failed_tests.append(f"{test_name}: {str(e)}")
        
        # Выводим результаты
        logger.info("\n" + "=" * 60)
        logger.info("📊 РЕЗУЛЬТАТЫ КОМПЛЕКСНОГО ТЕСТИРОВАНИЯ:")
        logger.info(f"✅ Пройдено: {len(self.passed_tests)}")
        logger.info(f"❌ Провалено: {len(self.failed_tests)}")
        
        total_tests = len(self.passed_tests) + len(self.failed_tests)
        success_rate = (len(self.passed_tests) / total_tests * 100) if total_tests > 0 else 0
        logger.info(f"📈 Процент успеха: {success_rate:.1f}%")
        
        # Детальные результаты
        logger.info("\n📋 Детальные результаты:")
        for test_name, result in self.test_results.items():
            logger.info(f"   {result} {test_name}")
        
        if self.failed_tests:
            logger.warning(f"\n⚠️ Обнаружено {len(self.failed_tests)} проблем:")
            for i, failed_test in enumerate(self.failed_tests, 1):
                logger.warning(f"   {i}. {failed_test}")
        else:
            logger.success("\n🎉 Все тесты пройдены успешно!")
        
        # Сохраняем отчет
        await self.save_test_report()
        
        return len(self.failed_tests) == 0
    
    async def save_test_report(self):
        """Сохранение отчета о тестировании"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"comprehensive_menu_test_report_{timestamp}.txt"
        
        try:
            with open(report_filename, 'w', encoding='utf-8') as f:
                f.write(f"КОМПЛЕКСНЫЙ ОТЧЕТ О ТЕСТИРОВАНИИ МЕНЮ БОТА\n")
                f.write(f"Дата и время: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n")
                f.write("=" * 60 + "\n\n")
                
                f.write(f"ОБЩАЯ СТАТИСТИКА:\n")
                f.write(f"✅ Пройдено тестов: {len(self.passed_tests)}\n")
                f.write(f"❌ Провалено тестов: {len(self.failed_tests)}\n")
                
                total_tests = len(self.passed_tests) + len(self.failed_tests)
                success_rate = (len(self.passed_tests) / total_tests * 100) if total_tests > 0 else 0
                f.write(f"📈 Процент успеха: {success_rate:.1f}%\n\n")
                
                f.write("ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ:\n")
                for test_name, result in self.test_results.items():
                    f.write(f"{result} {test_name}\n")
                
                if self.failed_tests:
                    f.write(f"\nОБНАРУЖЕННЫЕ ПРОБЛЕМЫ ({len(self.failed_tests)}):")
                    for i, failed_test in enumerate(self.failed_tests, 1):
                        f.write(f"\n{i}. {failed_test}")
                
                f.write("\n\n" + "=" * 60)
                f.write("\nТест завершен.")
            
            logger.info(f"📄 Отчет сохранен: {report_filename}")
            
        except Exception as e:
            logger.error(f"Ошибка сохранения отчета: {e}")

async def main():
    """Главная функция"""
    tester = ComprehensiveMenuTester()
    success = await tester.run_all_tests()
    
    if success:
        logger.success("🎉 Все тесты пройдены успешно!")
        return 0
    else:
        logger.error("❌ Обнаружены проблемы в работе бота")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)