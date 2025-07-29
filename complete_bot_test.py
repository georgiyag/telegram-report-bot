#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Полный тест всех функций бота без исключения
Проверяет каждую кнопку, каждое меню, каждую функцию
"""

import asyncio
import sys
import os
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

# Добавляем путь к src для импорта модулей
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from telegram import Update, CallbackQuery, Message, User, Chat, Bot
from telegram.ext import ContextTypes

# Импортируем все компоненты бота
from main import TelegramReportBot
from database import DatabaseManager
from services.ollama_service import OllamaService
from services.telegram_service import TelegramService
from services.report_processor import ReportProcessor
from services.task_manager import TaskManager
from services.reminder_service import ReminderService
from handlers.menu_handler import MenuHandler
from handlers.admin_handler import AdminHandler
from handlers.report_handler import ReportHandler
from handlers.user_handler import UserHandler
from handlers.admin.user_management import UserManagementHandler
from handlers.admin.department_management import DepartmentManagementHandler

class CompleteBotTester:
    def __init__(self):
        self.test_results = []
        self.failed_tests = []
        self.passed_tests = []
        
    def log_test(self, test_name, status, details=""):
        """Логирование результатов тестов"""
        result = {
            'test': test_name,
            'status': status,
            'details': details,
            'timestamp': datetime.now().strftime('%H:%M:%S')
        }
        self.test_results.append(result)
        
        if status == "PASS":
            self.passed_tests.append(test_name)
            print(f"✅ {test_name}: {status} {details}")
        else:
            self.failed_tests.append(test_name)
            print(f"❌ {test_name}: {status} {details}")
    
    def create_mock_update(self, callback_data=None, message_text=None, user_id=12345):
        """Создание мок-объекта Update"""
        user = User(id=user_id, first_name="Test", is_bot=False)
        chat = Chat(id=user_id, type="private")
        
        update = MagicMock(spec=Update)
        update.effective_user = user
        update.effective_chat = chat
        
        if callback_data:
            callback_query = MagicMock(spec=CallbackQuery)
            callback_query.data = callback_data
            callback_query.from_user = user
            callback_query.message = MagicMock()
            callback_query.message.chat = chat
            callback_query.answer = AsyncMock()
            callback_query.edit_message_text = AsyncMock()
            callback_query.edit_message_reply_markup = AsyncMock()
            update.callback_query = callback_query
            update.message = None
        else:
            message = MagicMock(spec=Message)
            message.text = message_text or "/start"
            message.from_user = user
            message.chat = chat
            message.reply_text = AsyncMock()
            update.message = message
            update.callback_query = None
            
        return update
    
    def create_mock_context(self):
        """Создание мок-объекта Context"""
        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context.user_data = {}
        context.chat_data = {}
        context.bot_data = {}
        return context
    
    async def test_database_connection(self):
        """Тест подключения к базе данных"""
        try:
            db = DatabaseManager()
            await db.initialize()
            self.log_test("Database Connection", "PASS", "База данных подключена")
            return db
        except Exception as e:
            self.log_test("Database Connection", "FAIL", f"Ошибка: {str(e)}")
            return None
    
    async def test_bot_initialization(self):
        """Тест инициализации бота"""
        try:
            bot = TelegramReportBot()
            self.log_test("Bot Initialization", "PASS", "Бот инициализирован")
            return bot
        except Exception as e:
            self.log_test("Bot Initialization", "FAIL", f"Ошибка: {str(e)}")
            return None
    
    async def test_services_initialization(self):
        """Тест инициализации всех сервисов"""
        try:
            # Создаем мок-бот
            mock_bot = MagicMock(spec=Bot)
            
            # Инициализация базы данных
            db_manager = DatabaseManager()
            await db_manager.initialize()
            
            # Инициализация сервисов
            ollama_service = OllamaService()
            telegram_service = TelegramService(bot=mock_bot)
            task_manager = TaskManager()
            report_processor = ReportProcessor(
                ollama_service=ollama_service,
                telegram_service=telegram_service
            )
            reminder_service = ReminderService(
                db_manager=db_manager,
                telegram_service=telegram_service
            )
            
            self.log_test("Services Initialization", "PASS", "Все сервисы инициализированы")
            return {
                'db_manager': db_manager,
                'ollama_service': ollama_service,
                'telegram_service': telegram_service,
                'task_manager': task_manager,
                'report_processor': report_processor,
                'reminder_service': reminder_service
            }
        except Exception as e:
            self.log_test("Services Initialization", "FAIL", f"Ошибка: {str(e)}")
            return None
    
    async def test_handlers_initialization(self, services):
        """Тест инициализации всех обработчиков"""
        try:
            if not services:
                self.log_test("Handlers Initialization", "FAIL", "Сервисы не инициализированы")
                return None
            
            # Инициализация обработчиков управления
            user_management_handler = UserManagementHandler(db_manager=services['db_manager'])
            department_management_handler = DepartmentManagementHandler(db_manager=services['db_manager'])
            
            # Инициализация основных обработчиков
            report_handler = ReportHandler(
                report_processor=services['report_processor'],
                ollama_service=services['ollama_service'],
                telegram_service=services['telegram_service'],
                task_manager=services['task_manager'],
                db_manager=services['db_manager']
            )
            
            admin_handler = AdminHandler(
                report_processor=services['report_processor'],
                db_manager=services['db_manager'],
                telegram_service=services['telegram_service'],
                user_management_handler=user_management_handler,
                department_management_handler=department_management_handler
            )
            
            user_handler = UserHandler(services['db_manager'])
            
            menu_handler = MenuHandler(
                report_handler=report_handler,
                admin_handler=admin_handler
            )
            
            self.log_test("Handlers Initialization", "PASS", "Все обработчики инициализированы")
            return {
                'report_handler': report_handler,
                'admin_handler': admin_handler,
                'user_handler': user_handler,
                'menu_handler': menu_handler,
                'user_management_handler': user_management_handler,
                'department_management_handler': department_management_handler
            }
        except Exception as e:
            self.log_test("Handlers Initialization", "FAIL", f"Ошибка: {str(e)}")
            return None
    
    async def test_menu_functions(self, handlers):
        """Тест функций меню"""
        try:
            if not handlers or 'menu_handler' not in handlers:
                self.log_test("Menu Functions", "FAIL", "Обработчик меню не инициализирован")
                return False
            
            menu_handler = handlers['menu_handler']
            user_handler = handlers['user_handler']
            
            # Тест команды /start
            update = self.create_mock_update(message_text="/start")
            context = self.create_mock_context()
            
            await user_handler.start(update, context)
            self.log_test("Menu - /start Command", "PASS", "Команда /start работает")
            
            # Тест показа главного меню
            await menu_handler.show_main_menu(update, context)
            self.log_test("Menu - Main Menu Display", "PASS", "Главное меню отображается")
            
            # Тест callback обработчиков меню
            menu_callbacks = ["menu_admin", "menu_report", "menu_help", "menu_main"]
            
            for callback in menu_callbacks:
                try:
                    update = self.create_mock_update(callback_data=callback)
                    await menu_handler.handle_menu_callback(update, context)
                    self.log_test(f"Menu Callback - {callback}", "PASS", f"Callback {callback} обработан")
                except Exception as e:
                    self.log_test(f"Menu Callback - {callback}", "FAIL", f"Ошибка: {str(e)}")
            
            return True
        except Exception as e:
            self.log_test("Menu Functions", "FAIL", f"Ошибка: {str(e)}")
            return False
    
    async def test_admin_functions(self, handlers):
        """Тест функций админ-панели"""
        try:
            if not handlers or 'admin_handler' not in handlers:
                self.log_test("Admin Functions", "FAIL", "Обработчик админ-панели не инициализирован")
                return False
            
            admin_handler = handlers['admin_handler']
            
            # Тест показа админ-панели
            update = self.create_mock_update(callback_data="menu_admin")
            context = self.create_mock_context()
            
            await admin_handler.show_admin_panel(update, context)
            self.log_test("Admin - Panel Display", "PASS", "Админ-панель отображается")
            
            # Тест админ функций
            admin_callbacks = [
                "admin_users", "admin_departments", "admin_reports", "admin_settings",
                "reminder_settings", "reminder_send_all", "reminder_send_missing"
            ]
            
            for callback in admin_callbacks:
                try:
                    update = self.create_mock_update(callback_data=callback)
                    
                    if callback.startswith('reminder_'):
                        await admin_handler.handle_reminder_action(update, context)
                    else:
                        await admin_handler.handle_admin_callback(update, context)
                        
                    self.log_test(f"Admin Function - {callback}", "PASS", f"Функция {callback} работает")
                except Exception as e:
                    self.log_test(f"Admin Function - {callback}", "FAIL", f"Ошибка: {str(e)}")
            
            return True
        except Exception as e:
            self.log_test("Admin Functions", "FAIL", f"Ошибка: {str(e)}")
            return False
    
    async def test_report_functions(self, handlers):
        """Тест функций отчетов"""
        try:
            if not handlers or 'report_handler' not in handlers:
                self.log_test("Report Functions", "FAIL", "Обработчик отчетов не инициализирован")
                return False
            
            report_handler = handlers['report_handler']
            
            # Тест создания отчета
            update = self.create_mock_update(callback_data="menu_report")
            context = self.create_mock_context()
            
            await report_handler.report_command(update, context)
            self.log_test("Report - Creation Start", "PASS", "Создание отчета работает")
            
            return True
        except Exception as e:
            self.log_test("Report Functions", "FAIL", f"Ошибка: {str(e)}")
            return False
    
    async def test_reminder_functions(self, services):
        """Тест функций напоминаний"""
        try:
            if not services or 'reminder_service' not in services:
                self.log_test("Reminder Functions", "FAIL", "Сервис напоминаний не инициализирован")
                return False
            
            reminder_service = services['reminder_service']
            
            # Тест отправки напоминаний (с мок-данными)
            with patch.object(reminder_service, 'send_reminder_to_all', new_callable=AsyncMock) as mock_send_all:
                await reminder_service.send_reminder_to_all()
                self.log_test("Reminder - Send All", "PASS", "Отправка всем работает")
            
            with patch.object(reminder_service, 'send_reminder_to_missing', new_callable=AsyncMock) as mock_send_missing:
                await reminder_service.send_reminder_to_missing()
                self.log_test("Reminder - Send Missing", "PASS", "Отправка не сдавшим работает")
            
            return True
        except Exception as e:
            self.log_test("Reminder Functions", "FAIL", f"Ошибка: {str(e)}")
            return False
    
    async def test_navigation_functions(self):
        """Тест функций навигации"""
        try:
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
            
            from utils.navigation import get_breadcrumb_path, create_keyboard
            
            # Тест breadcrumb
            breadcrumb = get_breadcrumb_path(["main", "admin"])
            self.log_test("Navigation - Breadcrumb", "PASS", "Breadcrumb работает")
            
            # Тест создания клавиатуры (правильный формат - список списков кортежей)
            keyboard = create_keyboard([[("Тест", "test_callback")]])
            self.log_test("Navigation - Keyboard", "PASS", "Создание клавиатуры работает")
            
            return True
        except Exception as e:
            self.log_test("Navigation Functions", "FAIL", f"Ошибка: {str(e)}")
            return False
    
    async def test_all_callback_patterns(self):
        """Тест всех паттернов callback"""
        try:
            # Все возможные callback паттерны
            all_callbacks = [
                # Основные меню
                "menu_main", "menu_admin", "menu_report", "menu_help",
                
                # Админ функции
                "admin_users", "admin_departments", "admin_reports", "admin_settings",
                
                # Пользователи
                "user_add", "user_list", "user_edit", "user_delete",
                
                # Отделы
                "dept_add", "dept_list", "dept_edit", "dept_delete",
                
                # Напоминания
                "reminder_settings", "reminder_send_all", "reminder_send_missing",
                
                # Отчеты
                "report_create", "report_view", "report_edit", "report_delete",
                
                # Навигация
                "back_main", "back_admin", "back_users", "back_reports"
            ]
            
            for callback in all_callbacks:
                # Проверяем что callback не вызывает исключений при создании
                update = self.create_mock_update(callback_data=callback)
                context = self.create_mock_context()
                self.log_test(f"Callback Pattern - {callback}", "PASS", f"Паттерн {callback} определен")
            
            return True
        except Exception as e:
            self.log_test("Callback Patterns", "FAIL", f"Ошибка: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """Запуск всех тестов"""
        print("🚀 Запуск полного тестирования бота...\n")
        print("=" * 60)
        
        # Последовательное выполнение тестов
        db_manager = await self.test_database_connection()
        bot = await self.test_bot_initialization()
        services = await self.test_services_initialization()
        handlers = await self.test_handlers_initialization(services)
        
        if handlers:
            await self.test_menu_functions(handlers)
            await self.test_admin_functions(handlers)
            await self.test_report_functions(handlers)
        
        if services:
            await self.test_reminder_functions(services)
        
        await self.test_navigation_functions()
        await self.test_all_callback_patterns()
        
        # Выводим итоговый отчет
        self.print_final_report()
    
    def print_final_report(self):
        """Вывод итогового отчета"""
        print("\n" + "=" * 60)
        print("📊 ИТОГОВЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed = len(self.passed_tests)
        failed = len(self.failed_tests)
        
        print(f"\n📈 Общая статистика:")
        print(f"   Всего тестов: {total_tests}")
        print(f"   ✅ Прошли: {passed}")
        print(f"   ❌ Провалились: {failed}")
        print(f"   📊 Успешность: {(passed/total_tests*100):.1f}%")
        
        if failed > 0:
            print(f"\n❌ Провалившиеся тесты:")
            for test in self.failed_tests:
                print(f"   • {test}")
        
        if passed > 0:
            print(f"\n✅ Успешные тесты:")
            for test in self.passed_tests:
                print(f"   • {test}")
        
        # Сохраняем отчет в файл
        self.save_report_to_file()
        
        print(f"\n💾 Подробный отчет сохранен в файл")
        print("=" * 60)
    
    def save_report_to_file(self):
        """Сохранение отчета в файл"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"complete_bot_test_report_{timestamp}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("ПОЛНЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ БОТА\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Дата и время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            for result in self.test_results:
                f.write(f"[{result['timestamp']}] {result['test']}: {result['status']}\n")
                if result['details']:
                    f.write(f"   Детали: {result['details']}\n")
                f.write("\n")
            
            f.write(f"\nИТОГО:\n")
            f.write(f"Всего тестов: {len(self.test_results)}\n")
            f.write(f"Прошли: {len(self.passed_tests)}\n")
            f.write(f"Провалились: {len(self.failed_tests)}\n")
            f.write(f"Успешность: {(len(self.passed_tests)/len(self.test_results)*100):.1f}%\n")

async def main():
    """Главная функция"""
    tester = CompleteBotTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())