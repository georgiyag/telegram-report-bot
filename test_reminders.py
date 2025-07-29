#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест функциональности напоминаний
"""

import asyncio
import sys
import os
from datetime import datetime

# Добавляем путь к src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from unittest.mock import AsyncMock, MagicMock
from telegram import Update, CallbackQuery, User, Message, Chat
from telegram.ext import ContextTypes

# Импортируем необходимые модули
from handlers.admin_handler import AdminHandler
from database import DatabaseManager
from services.reminder_service import ReminderService
from services.telegram_service import TelegramService

class ReminderTest:
    """Класс для тестирования функциональности напоминаний"""
    
    def __init__(self):
        self.db_manager = None
        self.admin_handler = None
        self.reminder_service = None
        self.telegram_service = None
        
    async def setup(self):
        """Настройка тестового окружения"""
        print("🔧 Настройка тестового окружения...")
        
        # Создаем моки
        self.db_manager = AsyncMock(spec=DatabaseManager)
        self.telegram_service = AsyncMock(spec=TelegramService)
        
        # Настраиваем моки
        self.db_manager.is_admin.return_value = True
        
        # Создаем моки для обработчиков
        report_processor = AsyncMock()
        user_management_handler = AsyncMock()
        department_management_handler = AsyncMock()
        
        # Создаем обработчики
        self.admin_handler = AdminHandler(
            report_processor,
            self.db_manager, 
            self.telegram_service, 
            user_management_handler, 
            department_management_handler
        )
        self.reminder_service = ReminderService(self.db_manager, self.telegram_service)
        
        print("✅ Тестовое окружение настроено")
    
    def create_mock_update(self, callback_data: str, user_id: int = 123456789) -> Update:
        """Создает мок Update для тестирования"""
        user = User(id=user_id, first_name="Test", is_bot=False)
        chat = Chat(id=user_id, type="private")
        message = Message(
            message_id=1,
            date=datetime.now(),
            chat=chat,
            from_user=user
        )
        
        # Создаем мок callback_query
        callback_query = AsyncMock()
        callback_query.id = "test_callback"
        callback_query.from_user = user
        callback_query.chat_instance = "test_instance"
        callback_query.data = callback_data
        callback_query.message = message
        callback_query.answer = AsyncMock()
        callback_query.edit_message_text = AsyncMock()
        
        update = Update(update_id=1, callback_query=callback_query)
        return update
    
    def create_mock_context(self) -> ContextTypes.DEFAULT_TYPE:
        """Создает мок контекста"""
        context = MagicMock()
        context.user_data = {}
        context.chat_data = {}
        context.bot_data = {}
        return context
    
    async def test_reminder_callback_handler(self):
        """Тест обработчика callback для напоминаний"""
        print("\n🧪 Тестирование обработчика callback для напоминаний...")
        
        try:
            # Создаем мок update и context
            update = self.create_mock_update("admin_reminders")
            context = self.create_mock_context()
            
            # Вызываем обработчик
            result = await self.admin_handler.handle_reminder_callback(update, context)
            
            # Проверяем результат
            assert result is not None, "Обработчик должен возвращать состояние"
            
            # Проверяем, что callback был отвечен
            update.callback_query.answer.assert_called_once()
            
            # Проверяем, что сообщение было отредактировано
            update.callback_query.edit_message_text.assert_called_once()
            
            print("✅ Обработчик callback для напоминаний работает корректно")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка в тесте обработчика callback: {e}")
            return False
    
    async def test_reminder_settings_button(self):
        """Тест кнопки настроек напоминаний"""
        print("\n🧪 Тестирование кнопки 'Настройки напоминаний'...")
        
        try:
            # Создаем мок update для кнопки настроек
            update = self.create_mock_update("reminder_settings")
            context = self.create_mock_context()
            
            # Вызываем обработчик действий с напоминаниями
            result = await self.admin_handler.handle_reminder_action(update, context)
            
            # Проверяем результат
            assert result is not None, "Обработчик должен возвращать состояние"
            
            # Проверяем, что callback был отвечен
            update.callback_query.answer.assert_called_once()
            
            # Проверяем, что сообщение было отредактировано
            update.callback_query.edit_message_text.assert_called_once()
            
            # Проверяем содержимое сообщения
            call_args = update.callback_query.edit_message_text.call_args
            message_text = call_args[0][0] if call_args[0] else ""
            
            assert "Настройки напоминаний" in message_text, "Сообщение должно содержать 'Настройки напоминаний'"
            
            print("✅ Кнопка 'Настройки напоминаний' работает корректно")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка в тесте кнопки настроек: {e}")
            return False
    
    async def test_reminder_send_all_button(self):
        """Тест кнопки отправки напоминаний всем"""
        print("\n🧪 Тестирование кнопки 'Отправить напоминание всем'...")
        
        try:
            # Создаем мок update для кнопки отправки всем
            update = self.create_mock_update("reminder_send_all")
            context = self.create_mock_context()
            
            # Вызываем обработчик
            result = await self.admin_handler.handle_reminder_action(update, context)
            
            # Проверяем результат
            assert result is not None, "Обработчик должен возвращать состояние"
            
            # Проверяем, что callback был отвечен
            update.callback_query.answer.assert_called_once()
            
            # Проверяем, что сообщение было отредактировано
            update.callback_query.edit_message_text.assert_called_once()
            
            print("✅ Кнопка 'Отправить напоминание всем' работает корректно")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка в тесте кнопки отправки всем: {e}")
            return False
    
    async def test_reminder_send_missing_button(self):
        """Тест кнопки напоминания не сдавшим"""
        print("\n🧪 Тестирование кнопки 'Напомнить не сдавшим'...")
        
        try:
            # Создаем мок update для кнопки напоминания не сдавшим
            update = self.create_mock_update("reminder_send_missing")
            context = self.create_mock_context()
            
            # Вызываем обработчик
            result = await self.admin_handler.handle_reminder_action(update, context)
            
            # Проверяем результат
            assert result is not None, "Обработчик должен возвращать состояние"
            
            # Проверяем, что callback был отвечен
            update.callback_query.answer.assert_called_once()
            
            # Проверяем, что сообщение было отредактировано
            update.callback_query.edit_message_text.assert_called_once()
            
            print("✅ Кнопка 'Напомнить не сдавшим' работает корректно")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка в тесте кнопки напоминания не сдавшим: {e}")
            return False
    
    async def test_reminder_service_basic(self):
        """Базовый тест сервиса напоминаний"""
        print("\n🧪 Тестирование базовой функциональности сервиса напоминаний...")
        
        try:
            # Проверяем инициализацию
            assert self.reminder_service is not None, "Сервис напоминаний должен быть инициализирован"
            assert not self.reminder_service.is_running, "Сервис не должен быть запущен изначально"
            
            # Тестируем запуск сервиса
            await self.reminder_service.start()
            assert self.reminder_service.is_running, "Сервис должен быть запущен после start()"
            
            # Тестируем остановку сервиса
            await self.reminder_service.stop()
            assert not self.reminder_service.is_running, "Сервис должен быть остановлен после stop()"
            
            print("✅ Базовая функциональность сервиса напоминаний работает корректно")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка в тесте сервиса напоминаний: {e}")
            return False
    
    async def run_all_tests(self):
        """Запуск всех тестов"""
        print("🚀 Запуск тестов функциональности напоминаний")
        print("=" * 60)
        
        await self.setup()
        
        tests = [
            self.test_reminder_callback_handler,
            self.test_reminder_settings_button,
            self.test_reminder_send_all_button,
            self.test_reminder_send_missing_button,
            self.test_reminder_service_basic
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            try:
                result = await test()
                if result:
                    passed += 1
            except Exception as e:
                print(f"❌ Критическая ошибка в тесте {test.__name__}: {e}")
        
        print("\n" + "=" * 60)
        print(f"📊 Результаты тестирования: {passed}/{total} тестов пройдено")
        
        if passed == total:
            print("🎉 Все тесты функциональности напоминаний пройдены успешно!")
        else:
            print(f"⚠️  {total - passed} тестов не пройдено")
        
        return passed == total

async def main():
    """Главная функция"""
    tester = ReminderTest()
    success = await tester.run_all_tests()
    
    if success:
        print("\n✅ Все тесты напоминаний пройдены успешно!")
        return 0
    else:
        print("\n❌ Некоторые тесты не пройдены")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)