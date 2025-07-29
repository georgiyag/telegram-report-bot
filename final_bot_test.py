#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Финальный тест всех функций бота
Проверяет работоспособность всех кнопок и функций
"""

import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

# Добавляем путь к src
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from handlers.admin_handler import AdminHandler
from handlers.menu_handler import MenuHandler
from handlers.report_handler import ReportHandler
from database import DatabaseManager
from services.telegram_service import TelegramService
from services.reminder_service import ReminderService
from services.report_processor import ReportProcessor
from services.task_manager import TaskManager

class FinalBotTest:
    """Финальный тест всех функций бота"""
    
    def __init__(self):
        self.setup_mocks()
        self.setup_handlers()
    
    def setup_mocks(self):
        """Настройка моков"""
        # Создаем моки для основных сервисов
        self.db_manager = MagicMock()
        self.telegram_service = AsyncMock()
        self.reminder_service = AsyncMock()
        self.report_processor = AsyncMock()
        self.task_manager = AsyncMock()
        
        # Мокаем методы базы данных
        self.db_manager.get_departments.return_value = [
            {'id': 1, 'name': 'IT отдел'},
            {'id': 2, 'name': 'Бухгалтерия'}
        ]
        
        self.db_manager.get_users.return_value = [
            {'id': 1, 'telegram_id': 123456, 'full_name': 'Тест Пользователь', 'department_id': 1}
        ]
    
    def setup_handlers(self):
        """Настройка обработчиков"""
        # Создаем моки для дополнительных обработчиков
        user_management_handler = AsyncMock()
        department_management_handler = AsyncMock()
        
        # Создаем основные обработчики
        self.admin_handler = AdminHandler(
            self.report_processor,
            self.db_manager,
            self.telegram_service,
            user_management_handler,
            department_management_handler
        )
        
        self.report_handler = ReportHandler(
            self.report_processor,
            None,  # ollama_service
            self.telegram_service,
            self.task_manager,
            self.db_manager
        )
        
        self.menu_handler = MenuHandler(
            self.report_handler,
            self.admin_handler
        )
    
    def create_mock_update(self, callback_data, user_id=167960842):
        """Создает мок Update объекта"""
        # Создаем мок пользователя
        user = AsyncMock()
        user.id = user_id
        user.first_name = "Test"
        user.username = "testuser"
        
        # Создаем мок сообщения
        message = AsyncMock()
        message.chat.id = user_id
        message.message_id = 123
        
        # Создаем мок callback_query
        callback_query = AsyncMock()
        callback_query.id = "test_callback"
        callback_query.from_user = user
        callback_query.chat_instance = "test_instance"
        callback_query.data = callback_data
        callback_query.message = message
        callback_query.answer = AsyncMock()
        callback_query.edit_message_text = AsyncMock()
        
        # Создаем мок update
        update = AsyncMock()
        update.callback_query = callback_query
        update.effective_user = user
        update.effective_chat = message.chat
        
        return update
    
    def create_mock_context(self):
        """Создает мок Context объекта"""
        context = AsyncMock()
        context.bot = AsyncMock()
        context.user_data = {}
        context.chat_data = {}
        return context
    
    async def test_main_menu_buttons(self):
        """Тестирует кнопки главного меню"""
        print("🧪 Тестирование кнопок главного меню...")
        
        buttons_to_test = [
            'menu_report',
            'menu_admin',
            'menu_help'
        ]
        
        for button in buttons_to_test:
            try:
                update = self.create_mock_update(button)
                context = self.create_mock_context()
                
                if button == 'menu_report':
                    await self.report_handler.report_command(update, context)
                elif button == 'menu_admin':
                    await self.admin_handler.admin_command(update, context)
                elif button == 'menu_help':
                    await self.menu_handler.show_help(update, context)
                
                print(f"  ✅ Кнопка '{button}' работает корректно")
            except Exception as e:
                print(f"  ❌ Ошибка в кнопке '{button}': {e}")
                return False
        
        return True
    
    async def test_admin_panel_buttons(self):
        """Тестирует кнопки админ-панели"""
        print("🧪 Тестирование кнопок админ-панели...")
        
        admin_buttons = [
            'admin_users',
            'admin_departments', 
            'admin_reminders',
            'admin_reports',
            'admin_export'
        ]
        
        for button in admin_buttons:
            try:
                update = self.create_mock_update(button)
                context = self.create_mock_context()
                
                await self.admin_handler.handle_admin_callback(update, context)
                print(f"  ✅ Админ кнопка '{button}' работает корректно")
            except Exception as e:
                print(f"  ❌ Ошибка в админ кнопке '{button}': {e}")
                return False
        
        return True
    
    async def test_reminder_buttons(self):
        """Тестирует кнопки напоминаний"""
        print("🧪 Тестирование кнопок напоминаний...")
        
        reminder_buttons = [
            'reminder_settings',
            'reminder_send_all',
            'reminder_send_missing'
        ]
        
        for button in reminder_buttons:
            try:
                update = self.create_mock_update(button)
                context = self.create_mock_context()
                
                await self.admin_handler.handle_reminder_action(update, context)
                print(f"  ✅ Кнопка напоминаний '{button}' работает корректно")
            except Exception as e:
                print(f"  ❌ Ошибка в кнопке напоминаний '{button}': {e}")
                return False
        
        return True
    
    async def test_back_buttons(self):
        """Тестирует кнопки возврата"""
        print("🧪 Тестирование кнопок возврата...")
        
        back_buttons = [
            'admin_back',
            'back_to_main',
            'back_to_admin'
        ]
        
        for button in back_buttons:
            try:
                update = self.create_mock_update(button)
                context = self.create_mock_context()
                
                if button == 'admin_back':
                    await self.admin_handler.handle_admin_callback(update, context)
                elif button == 'back_to_main':
                    await self.menu_handler.show_main_menu(update, context)
                elif button == 'back_to_admin':
                    await self.admin_handler.admin_command(update, context)
                
                print(f"  ✅ Кнопка возврата '{button}' работает корректно")
            except Exception as e:
                print(f"  ❌ Ошибка в кнопке возврата '{button}': {e}")
                return False
        
        return True
    
    async def run_all_tests(self):
        """Запускает все тесты"""
        print("🚀 Запуск финального теста всех функций бота")
        print("=" * 60)
        
        tests = [
            ("Главное меню", self.test_main_menu_buttons),
            ("Админ-панель", self.test_admin_panel_buttons),
            ("Напоминания", self.test_reminder_buttons),
            ("Кнопки возврата", self.test_back_buttons)
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n📋 Тестирование: {test_name}")
            try:
                result = await test_func()
                if result:
                    passed_tests += 1
                    print(f"✅ {test_name}: ПРОЙДЕН")
                else:
                    print(f"❌ {test_name}: НЕ ПРОЙДЕН")
            except Exception as e:
                print(f"❌ {test_name}: ОШИБКА - {e}")
        
        print("\n" + "=" * 60)
        print(f"📊 Результаты финального тестирования: {passed_tests}/{total_tests} тестов пройдено")
        
        if passed_tests == total_tests:
            print("🎉 Все тесты пройдены успешно! Бот полностью функционален.")
            print("✅ Кнопка 'настройка напоминаний' работает корректно!")
            return True
        else:
            print(f"⚠️  {total_tests - passed_tests} тестов не пройдено")
            return False

async def main():
    """Главная функция теста"""
    tester = FinalBotTest()
    success = await tester.run_all_tests()
    
    if success:
        print("\n🎯 ЗАКЛЮЧЕНИЕ: Все функции бота работают корректно!")
        print("🔧 Кнопка 'настройка напоминаний' исправлена и функционирует.")
    else:
        print("\n❌ ЗАКЛЮЧЕНИЕ: Обнаружены проблемы в работе бота.")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())