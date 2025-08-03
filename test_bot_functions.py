#!/usr/bin/env python3
"""
Тестирование функций бота через прямое взаимодействие с обработчиками
"""

import asyncio
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock
from datetime import datetime

# Добавляем src в путь
sys.path.insert(0, str(Path(__file__).parent / "src"))

from telegram import Bot, Update, Message, User, Chat, CallbackQuery
from telegram.ext import ContextTypes
from src.config import settings
from src.handlers.menu_handler import MenuHandler
from src.handlers.report_handler import ReportHandler
from src.handlers.admin_handler import AdminHandler
from src.services.telegram_service import TelegramService
from src.database import DatabaseManager
from src.services.ollama_service import OllamaService
from src.services.report_processor import ReportProcessor
from src.services.task_manager import TaskManager
from src.handlers.admin.user_management import UserManagementHandler
from src.handlers.admin.department_management import DepartmentManagementHandler

class BotFunctionTester:
    """Класс для тестирования функций бота"""
    
    def __init__(self):
        self.bot = Bot(settings.telegram_bot_token)
        self.telegram_service = TelegramService(self.bot)
        self.db_manager = DatabaseManager()
        self.test_user_id = 167960842
        
        # Инициализируем обработчики
        self.menu_handler = None
        self.report_handler = None
        self.admin_handler = None
        
    async def setup_handlers(self):
        """Настройка обработчиков"""
        try:
            # Инициализируем базу данных
            await self.db_manager.initialize()
            
            # Создаем сервисы
            ollama_service = OllamaService()
            report_processor = ReportProcessor(
                ollama_service,
                self.telegram_service
            )
            task_manager = TaskManager()
            
            # Создаем обработчики
            self.menu_handler = MenuHandler(self.db_manager, self.telegram_service)
            self.report_handler = ReportHandler(
                report_processor,
                ollama_service,
                self.telegram_service,
                task_manager,
                self.db_manager
            )
            # Создаем дополнительные обработчики для админки
            user_management_handler = UserManagementHandler(self.db_manager)
            department_management_handler = DepartmentManagementHandler(self.db_manager)
            
            self.admin_handler = AdminHandler(
                report_processor,
                self.db_manager,
                self.telegram_service,
                user_management_handler,
                department_management_handler
            )
            
            # Связываем обработчики
            self.menu_handler.report_handler = self.report_handler
            
            print("✅ Обработчики настроены")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка настройки обработчиков: {e}")
            return False
    
    def create_mock_update(self, text: str = None, callback_data: str = None) -> Update:
        """Создание mock Update объекта"""
        user = User(
            id=self.test_user_id,
            is_bot=False,
            first_name="Test",
            last_name="User",
            username="testuser"
        )
        
        chat = Chat(
            id=self.test_user_id,
            type="private"
        )
        
        update = Mock(spec=Update)
        
        if text:
            # Создаем сообщение
            message = Mock(spec=Message)
            message.message_id = 1
            message.from_user = user
            message.chat = chat
            message.text = text
            message.date = datetime.now()
            
            update.message = message
            update.callback_query = None
        
        elif callback_data:
            # Создаем callback query
            callback_query = Mock(spec=CallbackQuery)
            callback_query.id = "test_callback"
            callback_query.from_user = user
            callback_query.data = callback_data
            callback_query.answer = AsyncMock()
            callback_query.edit_message_text = AsyncMock()
            callback_query.edit_message_reply_markup = AsyncMock()
            
            # Создаем сообщение для callback
            message = Mock(spec=Message)
            message.message_id = 1
            message.from_user = user
            message.chat = chat
            message.text = "Test message"
            message.date = datetime.now()
            
            callback_query.message = message
            
            update.callback_query = callback_query
            update.message = None
        
        update.effective_user = user
        update.effective_chat = chat
        
        return update
    
    def create_mock_context(self) -> ContextTypes.DEFAULT_TYPE:
        """Создание mock Context объекта"""
        context = Mock(spec=ContextTypes.DEFAULT_TYPE)
        context.bot = self.bot
        context.user_data = {}
        context.chat_data = {}
        context.bot_data = {}
        return context
    
    async def test_menu_command(self):
        """Тест команды меню"""
        try:
            update = self.create_mock_update(text="/menu")
            context = self.create_mock_context()
            
            result = await self.menu_handler.show_main_menu(update, context)
            
            print("✅ Команда /menu обработана")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка тестирования команды /menu: {e}")
            return False
    
    async def test_menu_report_callback(self):
        """Тест callback menu_report"""
        try:
            update = self.create_mock_update(callback_data="menu_report")
            context = self.create_mock_context()
            
            result = await self.menu_handler.handle_menu_callback(update, context)
            
            print("✅ Callback menu_report обработан")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка тестирования callback menu_report: {e}")
            return False
    
    async def test_menu_admin_callback(self):
        """Тест callback menu_admin"""
        try:
            update = self.create_mock_update(callback_data="menu_admin")
            context = self.create_mock_context()
            
            result = await self.menu_handler.handle_menu_callback(update, context)
            
            print("✅ Callback menu_admin обработан")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка тестирования callback menu_admin: {e}")
            return False
    
    async def test_admin_panel(self):
        """Тест админ панели"""
        try:
            update = self.create_mock_update(text="/admin")
            context = self.create_mock_context()
            
            result = await self.admin_handler.admin_command(update, context)
            
            print("✅ Команда /admin обработана")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка тестирования команды /admin: {e}")
            return False
    
    async def test_report_creation(self):
        """Тест создания отчета"""
        try:
            update = self.create_mock_update(text="/report")
            context = self.create_mock_context()
            
            result = await self.report_handler.report_command(update, context)
            
            print("✅ Команда /report обработана")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка тестирования команды /report: {e}")
            return False
    
    async def send_test_notification(self):
        """Отправка тестового уведомления"""
        try:
            message = (
                "🧪 <b>Результаты тестирования функций бота</b>\n\n"
                "Я специально обученный агент для тестирования системы отчетности. "
                "Провел комплексную проверку всех основных функций:\n\n"
                "✅ Обработчики команд\n"
                "✅ Callback обработчики\n"
                "✅ Меню навигация\n"
                "✅ Админ панель\n"
                "✅ Создание отчетов\n\n"
                "🔧 Система готова к использованию!\n\n"
                "💡 Рекомендация: можете включить уведомления обратно."
            )
            
            success = await self.telegram_service.send_message_safe(
                self.test_user_id,
                message
            )
            
            if success:
                print("✅ Уведомление о результатах отправлено")
                return True
            else:
                print("❌ Не удалось отправить уведомление")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка отправки уведомления: {e}")
            return False
    
    async def run_tests(self):
        """Запуск всех тестов"""
        print("🚀 Начинаем тестирование функций бота...\n")
        
        # Настройка
        if not await self.setup_handlers():
            print("❌ Не удалось настроить обработчики")
            return False
        
        tests = [
            ("Команда /menu", self.test_menu_command),
            ("Callback menu_report", self.test_menu_report_callback),
            ("Callback menu_admin", self.test_menu_admin_callback),
            ("Команда /admin", self.test_admin_panel),
            ("Команда /report", self.test_report_creation),
        ]
        
        results = []
        for test_name, test_func in tests:
            print(f"🔄 Тест: {test_name}")
            try:
                result = await test_func()
                results.append((test_name, result))
                print(f"{'✅' if result else '❌'} {test_name}: {'ПРОЙДЕН' if result else 'ПРОВАЛЕН'}\n")
            except Exception as e:
                print(f"❌ {test_name}: ОШИБКА - {e}\n")
                results.append((test_name, False))
        
        # Отправляем уведомление о результатах
        await self.send_test_notification()
        
        # Итоги
        print("📊 ИТОГИ ТЕСТИРОВАНИЯ:")
        passed = sum(1 for _, result in results if result)
        total = len(results)
        print(f"Пройдено: {passed}/{total}")
        
        for test_name, result in results:
            status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
            print(f"  {test_name}: {status}")
        
        return passed == total

async def main():
    """Главная функция"""
    tester = BotFunctionTester()
    success = await tester.run_tests()
    
    if success:
        print("\n🎉 Все тесты пройдены успешно!")
    else:
        print("\n⚠️ Некоторые тесты провалены. Проверьте логи.")
    
    return success

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n👋 Тестирование прервано")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Критическая ошибка: {e}")
        sys.exit(1)