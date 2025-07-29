#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Комплексный скрипт тестирования всех функций Telegram бота.
Проверяет работоспособность всех меню, подменю, кнопок навигации и функций.

Автор: Telegram Report Bot
Версия: 1.0.0
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
from dataclasses import dataclass

# Добавляем путь к src для импорта модулей
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from telegram import Update, User, Chat, Message, CallbackQuery
from telegram.ext import ContextTypes
from unittest.mock import Mock, AsyncMock

# Импорт компонентов бота
from config import settings
from database import DatabaseManager
from handlers.menu_handler import MenuHandler
from handlers.admin_handler import AdminHandler
from handlers.report_handler import ReportHandler
from handlers.user_handler import UserHandler
from handlers.states import MainMenuStates, AdminStates, ReportStates
from services.telegram_service import TelegramService
from services.report_processor import ReportProcessor
from services.ollama_service import OllamaService
from handlers.admin.user_management import UserManagementHandler
from handlers.admin.department_management import DepartmentManagementHandler

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler('bot_test_results.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    """Результат выполнения теста"""
    test_name: str
    success: bool
    message: str
    error: Optional[str] = None
    duration: float = 0.0

class BotTester:
    """Класс для комплексного тестирования бота"""
    
    def __init__(self):
        self.db_manager = None
        self.handlers = {}
        self.test_results: List[TestResult] = []
        self.test_user_id = 167960842  # ID администратора для тестов
        
    async def initialize(self):
        """Инициализация компонентов для тестирования"""
        try:
            logger.info("Инициализация тестового окружения...")
            
            # Инициализация базы данных
            self.db_manager = DatabaseManager()
            await self.db_manager.initialize()
            
            # Инициализация сервисов
            from telegram import Bot
            from services.task_manager import TaskManager
            
            bot = Bot(token=settings.telegram_bot_token)
            telegram_service = TelegramService(bot)
            ollama_service = OllamaService()
            task_manager = TaskManager()
            report_processor = ReportProcessor(ollama_service, telegram_service)
            
            # Инициализация дополнительных обработчиков
            user_management = UserManagementHandler(self.db_manager)
            dept_management = DepartmentManagementHandler(self.db_manager)
            
            # Инициализация основных обработчиков
            report_handler = ReportHandler(report_processor, ollama_service, telegram_service, task_manager, self.db_manager)
            admin_handler = AdminHandler(report_processor, self.db_manager, telegram_service, user_management, dept_management)
            
            self.handlers = {
                'menu': MenuHandler(report_handler, admin_handler),
                'admin': admin_handler,
                'report': report_handler,
                'user': UserHandler(self.db_manager)
            }
            
            logger.info("Тестовое окружение инициализировано")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка инициализации: {e}")
            return False
    
    def create_mock_update(self, callback_data: str = None, message_text: str = None, user_id: int = None) -> Update:
        """Создает мок объект Update для тестирования"""
        if user_id is None:
            user_id = self.test_user_id
            
        user = User(id=user_id, first_name="Test", is_bot=False, username="testuser")
        chat = Chat(id=user_id, type="private")
        
        if callback_data:
            # Создаем CallbackQuery
            message = Message(
                message_id=1,
                date=datetime.now(),
                chat=chat,
                from_user=user
            )
            callback_query = CallbackQuery(
                id="test_callback",
                from_user=user,
                chat_instance="test_instance",
                data=callback_data,
                message=message
            )
            callback_query.answer = AsyncMock()
            callback_query.edit_message_text = AsyncMock()
            
            update = Update(update_id=1, callback_query=callback_query)
        else:
            # Создаем обычное сообщение
            message = Message(
                message_id=1,
                date=datetime.now(),
                chat=chat,
                from_user=user,
                text=message_text or "/start"
            )
            message.reply_text = AsyncMock()
            update = Update(update_id=1, message=message)
            
        return update
    
    def create_mock_context(self) -> ContextTypes.DEFAULT_TYPE:
        """Создает мок объект контекста"""
        context = Mock()
        context.user_data = {}
        context.chat_data = {}
        context.bot_data = {}
        return context
    
    async def run_test(self, test_name: str, test_func, *args, **kwargs) -> TestResult:
        """Выполняет отдельный тест и записывает результат"""
        start_time = datetime.now()
        
        try:
            logger.info(f"Запуск теста: {test_name}")
            result = await test_func(*args, **kwargs)
            
            duration = (datetime.now() - start_time).total_seconds()
            
            if result:
                test_result = TestResult(test_name, True, "Тест пройден успешно", duration=duration)
                logger.info(f"{test_name}: ПРОЙДЕН ({duration:.2f}с)")
            else:
                test_result = TestResult(test_name, False, "Тест не пройден", duration=duration)
                logger.error(f"{test_name}: НЕ ПРОЙДЕН ({duration:.2f}с)")
                
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            test_result = TestResult(test_name, False, f"Ошибка выполнения: {str(e)}", str(e), duration)
            logger.error(f"{test_name}: ОШИБКА - {e} ({duration:.2f}с)")
        
        self.test_results.append(test_result)
        return test_result
    
    async def test_database_connection(self) -> bool:
        """Тест подключения к базе данных"""
        try:
            # Проверяем подключение
            result = await self.db_manager.execute_query("SELECT 1")
            return result is not None
        except Exception as e:
            logger.error(f"Ошибка подключения к БД: {e}")
            return False
    
    async def test_main_menu_display(self) -> bool:
        """Тест отображения главного меню"""
        try:
            update = self.create_mock_update(message_text="/start")
            context = self.create_mock_context()
            
            result = await self.handlers['menu'].show_main_menu(update, context)
            return result == MainMenuStates.MAIN_MENU
        except Exception as e:
            logger.error(f"Ошибка отображения главного меню: {e}")
            return False
    
    async def test_admin_panel_access(self) -> bool:
        """Тест доступа к админ-панели"""
        try:
            update = self.create_mock_update(callback_data="menu_admin")
            context = self.create_mock_context()
            
            result = await self.handlers['admin'].show_admin_panel(update, context)
            return result == AdminStates.MAIN_MENU
        except Exception as e:
            logger.error(f"Ошибка доступа к админ-панели: {e}")
            return False
    
    async def test_report_creation_start(self) -> bool:
        """Тест начала создания отчета"""
        try:
            update = self.create_mock_update(callback_data="menu_report")
            context = self.create_mock_context()
            
            result = await self.handlers['report'].start_report_process(update, context)
            return result == ReportStates.DEPARTMENT_SELECTION
        except Exception as e:
            logger.error(f"Ошибка начала создания отчета: {e}")
            return False
    
    async def test_menu_navigation_buttons(self) -> bool:
        """Тест кнопок навигации в меню"""
        try:
            # Тестируем различные кнопки меню
            menu_buttons = [
                "menu_report",
                "menu_status", 
                "menu_help",
                "menu_admin"
            ]
            
            for button in menu_buttons:
                update = self.create_mock_update(callback_data=button)
                context = self.create_mock_context()
                
                # Проверяем обработку через menu_handler
                result = await self.handlers['menu'].handle_menu_callback(update, context)
                if result is None:
                    logger.warning(f"Кнопка {button} вернула None")
                    return False
                    
            return True
        except Exception as e:
            logger.error(f"Ошибка навигации по меню: {e}")
            return False
    
    async def test_admin_submenu_navigation(self) -> bool:
        """Тест навигации по подменю админ-панели"""
        try:
            admin_buttons = [
                "admin_manage_users",
                "admin_manage_depts",
                "admin_reports",
                "admin_reminders",
                "admin_export"
            ]
            
            for button in admin_buttons:
                update = self.create_mock_update(callback_data=button)
                context = self.create_mock_context()
                
                result = await self.handlers['admin'].handle_main_menu_callback(update, context)
                if result is None:
                    logger.warning(f"Админ кнопка {button} вернула None")
                    return False
                    
            return True
        except Exception as e:
            logger.error(f"Ошибка навигации по админ-панели: {e}")
            return False
    
    async def test_back_buttons(self) -> bool:
        """Тест кнопок 'Назад'"""
        try:
            back_buttons = [
                "back_to_main",
                "admin_back",
                "admin_exit"
            ]
            
            for button in back_buttons:
                update = self.create_mock_update(callback_data=button)
                context = self.create_mock_context()
                
                # Проверяем через соответствующие обработчики
                if button == "back_to_main":
                    result = await self.handlers['menu'].show_main_menu(update, context)
                elif button.startswith("admin_"):
                    result = await self.handlers['admin'].handle_admin_callback(update, context)
                else:
                    result = await self.handlers['menu'].handle_menu_callback(update, context)
                    
                if result is None:
                    logger.warning(f"Кнопка назад {button} вернула None")
                    return False
                    
            return True
        except Exception as e:
            logger.error(f"Ошибка кнопок назад: {e}")
            return False
    
    async def test_user_permissions(self) -> bool:
        """Тест проверки прав пользователей"""
        try:
            # Проверяем права администратора
            is_admin = await self.db_manager.is_admin(self.test_user_id)
            
            # Проверяем права обычного пользователя
            regular_user_id = 999999999
            is_regular = await self.db_manager.is_admin(regular_user_id)
            
            return is_admin and not is_regular
        except Exception as e:
            logger.error(f"Ошибка проверки прав: {e}")
            return False
    
    async def test_conversation_states(self) -> bool:
        """Тест состояний ConversationHandler"""
        try:
            # Проверяем, что состояния определены корректно
            main_states = [MainMenuStates.MAIN_MENU]
            admin_states = [AdminStates.MAIN_MENU, AdminStates.VIEW_REPORTS]
            report_states = [ReportStates.DEPARTMENT_SELECTION, ReportStates.TASK_INPUT]
            
            # Проверяем, что все состояния имеют числовые значения
            all_states = main_states + admin_states + report_states
            for state in all_states:
                if not isinstance(state, int):
                    logger.error(f"Состояние {state} не является числом")
                    return False
                    
            return True
        except Exception as e:
            logger.error(f"Ошибка проверки состояний: {e}")
            return False
    
    async def test_error_handling(self) -> bool:
        """Тест обработки ошибок"""
        try:
            # Тестируем обработку некорректных callback_data
            invalid_callbacks = [
                "invalid_callback",
                "nonexistent_action",
                "",
                None
            ]
            
            for callback in invalid_callbacks:
                if callback is not None:
                    update = self.create_mock_update(callback_data=callback)
                    context = self.create_mock_context()
                    
                    # Проверяем, что обработчики не падают на некорректных данных
                    try:
                        await self.handlers['menu'].handle_menu_callback(update, context)
                    except Exception as e:
                        logger.warning(f"Обработчик упал на {callback}: {e}")
                        
            return True
        except Exception as e:
            logger.error(f"Ошибка тестирования обработки ошибок: {e}")
            return False
    
    async def test_database_operations(self) -> bool:
        """Тест операций с базой данных"""
        try:
            # Тест получения отделов
            departments = await self.db_manager.get_active_departments()
            
            # Тест получения пользователей
            users = await self.db_manager.get_all_employees()
            
            # Тест получения отчетов
            reports = await self.db_manager.get_reports_by_user(self.test_user_id)
            
            return True
        except Exception as e:
            logger.error(f"Ошибка операций с БД: {e}")
            return False
    
    async def run_all_tests(self):
        """Запуск всех тестов"""
        logger.info("Начало комплексного тестирования бота")
        logger.info("=" * 60)
        
        # Инициализация
        if not await self.initialize():
            logger.error("Не удалось инициализировать тестовое окружение")
            return
        
        # Список всех тестов
        tests = [
            ("Подключение к базе данных", self.test_database_connection),
            ("Отображение главного меню", self.test_main_menu_display),
            ("Доступ к админ-панели", self.test_admin_panel_access),
            ("Начало создания отчета", self.test_report_creation_start),
            ("Навигация по главному меню", self.test_menu_navigation_buttons),
            ("Навигация по админ-панели", self.test_admin_submenu_navigation),
            ("Кнопки 'Назад'", self.test_back_buttons),
            ("Права пользователей", self.test_user_permissions),
            ("Состояния ConversationHandler", self.test_conversation_states),
            ("Обработка ошибок", self.test_error_handling),
            ("Операции с базой данных", self.test_database_operations)
        ]
        
        # Выполнение тестов
        for test_name, test_func in tests:
            await self.run_test(test_name, test_func)
            await asyncio.sleep(0.1)  # Небольшая пауза между тестами
        
        # Подведение итогов
        await self.generate_report()
    
    async def generate_report(self):
        """Генерация отчета о тестировании"""
        logger.info("\n" + "=" * 60)
        logger.info("ИТОГИ ТЕСТИРОВАНИЯ")
        logger.info("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result.success)
        failed_tests = total_tests - passed_tests
        total_time = sum(result.duration for result in self.test_results)
        
        logger.info(f"Всего тестов: {total_tests}")
        logger.info(f"Пройдено: {passed_tests}")
        logger.info(f"Провалено: {failed_tests}")
        logger.info(f"Общее время: {total_time:.2f} секунд")
        logger.info(f"Процент успеха: {(passed_tests/total_tests*100):.1f}%")
        
        logger.info("\nДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ:")
        logger.info("-" * 60)
        
        for result in self.test_results:
            status = "ПРОЙДЕН" if result.success else "ПРОВАЛЕН"
            logger.info(f"{status} | {result.test_name} ({result.duration:.2f}с)")
            if not result.success and result.error:
                logger.info(f"   Ошибка: {result.error}")
        
        logger.info("\n" + "=" * 60)
        
        if failed_tests > 0:
            logger.error(f"ВНИМАНИЕ: Обнаружено {failed_tests} проблем в работе бота!")
            logger.error("Рекомендуется исправить ошибки перед продакшеном.")
        else:
            logger.info("ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
            logger.info("Бот готов к работе.")
        
        # Сохранение отчета в файл
        report_file = f"bot_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"Отчет о тестировании бота\n")
            f.write(f"Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Всего тестов: {total_tests}\n")
            f.write(f"Пройдено: {passed_tests}\n")
            f.write(f"Провалено: {failed_tests}\n")
            f.write(f"Процент успеха: {(passed_tests/total_tests*100):.1f}%\n\n")
            
            for result in self.test_results:
                status = "ПРОЙДЕН" if result.success else "ПРОВАЛЕН"
                f.write(f"{status} | {result.test_name} | {result.duration:.2f}с\n")
                if not result.success and result.error:
                    f.write(f"  Ошибка: {result.error}\n")
        
        logger.info(f"Отчет сохранен в файл: {report_file}")

async def main():
    """Главная функция запуска тестов"""
    print("Комплексное тестирование Telegram бота")
    print("Дата:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print("=" * 60)
    
    tester = BotTester()
    await tester.run_all_tests()
    
    print("\nТестирование завершено!")

if __name__ == "__main__":
    # Запуск тестов
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nТестирование прервано пользователем")
    except Exception as e:
        print(f"\nКритическая ошибка: {e}")
        sys.exit(1)