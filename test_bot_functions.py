#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для тестирования функций Telegram бота
"""

import asyncio
import sys
import os
from datetime import datetime
from loguru import logger

# Добавляем путь к src для импортов
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config import settings
from database import DatabaseManager
from services.telegram_service import TelegramService
from telegram import Bot

class BotFunctionTester:
    """Тестер функций бота"""
    
    def __init__(self):
        self.bot = Bot(token=settings.telegram_bot_token)
        self.telegram_service = TelegramService(self.bot)
        self.db_manager = DatabaseManager()
        self.test_user_id = 167960842  # ID администратора для тестов
        
    async def test_bot_info(self):
        """Тест получения информации о боте"""
        try:
            bot_info = await self.bot.get_me()
            logger.info(f"✅ Бот активен: @{bot_info.username} ({bot_info.first_name})")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка получения информации о боте: {e}")
            return False
    
    async def test_database_connection(self):
        """Тест подключения к базе данных"""
        try:
            # Проверяем подключение к БД
            departments = await self.db_manager.get_departments()
            logger.info(f"✅ База данных: найдено {len(departments)} отделов")
            
            employees = await self.db_manager.get_employees()
            logger.info(f"✅ База данных: найдено {len(employees)} сотрудников")
            
            self.test_results["Подключение к БД"] = "✅ ПРОЙДЕН"
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка БД: {e}")
            self.test_results["Подключение к БД"] = f"❌ НЕ ПРОЙДЕН - {str(e)}"
            return False
    
    async def test_send_message(self):
        """Тест отправки сообщения"""
        try:
            test_message = f"🧪 Тестовое сообщение от бота\nВремя: {datetime.now().strftime('%H:%M:%S')}"
            success = await self.telegram_service.send_message_safe(
                chat_id=self.test_user_id,
                text=test_message
            )
            
            if success:
                logger.info("✅ Отправка сообщений работает")
                return True
            else:
                logger.error("❌ Не удалось отправить тестовое сообщение")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка отправки сообщения: {e}")
            return False
    
    async def test_admin_permissions(self):
        """Тест проверки прав администратора"""
        try:
            admin_ids = settings.get_admin_ids()
            is_admin = self.test_user_id in admin_ids
            
            logger.info(f"✅ Права администратора: {'Да' if is_admin else 'Нет'}")
            logger.info(f"✅ Список администраторов: {admin_ids}")
            
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка проверки прав: {e}")
            return False
    
    async def test_config_settings(self):
        """Тест настроек конфигурации"""
        try:
            # Проверяем основные настройки
            logger.info(f"✅ Конфигурация: Токен бота настроен: {'Да' if settings.telegram_bot_token else 'Нет'}")
            logger.info(f"✅ Конфигурация: ID группы: {settings.group_chat_id}")
            logger.info(f"✅ Конфигурация: Часовой пояс: {settings.timezone}")
            
            admin_ids = settings.get_admin_ids()
            logger.info(f"✅ Конфигурация: Администраторы: {admin_ids}")
            
            timezone = settings.get_timezone()
            logger.info(f"✅ Конфигурация: Объект временной зоны: {timezone}")
            
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка конфигурации: {e}")
            return False
    
    async def test_departments_and_employees(self):
        """Тест работы с отделами и сотрудниками"""
        try:
            # Получаем отделы
            departments = await self.db_manager.get_departments()
            logger.info(f"✅ Отделы ({len(departments)}):")
            for dept in departments[:5]:  # Показываем первые 5
                logger.info(f"   - {dept.name} (ID: {dept.id})")
            
            # Получаем сотрудников
            employees = await self.db_manager.get_employees()
            logger.info(f"✅ Сотрудники ({len(employees)}):")
            for emp in employees[:5]:  # Показываем первых 5
                logger.info(f"   - {emp.full_name} ({emp.department_name})")
            
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка работы с отделами/сотрудниками: {e}")
            return False
    
    async def test_reports_functionality(self):
        """Тест функций отчетов"""
        try:
            # Проверяем возможность получения отчетов за неделю
            from datetime import date
            week_reports = await self.db_manager.get_reports_by_week(
                date.today(), date.today()
            )
            logger.info(f"✅ Отчеты за неделю: {len(week_reports)}")
            
            # Проверяем получение отчетов пользователя (если есть сотрудники)
            employees = await self.db_manager.get_employees()
            if employees:
                user_reports = await self.db_manager.get_user_reports(employees[0].user_id, limit=5)
                logger.info(f"✅ Отчеты пользователя: {len(user_reports)}")
            
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка работы с отчетами: {e}")
            return False
    
    async def run_all_tests(self):
        """Запуск всех тестов"""
        logger.info("🧪 Начало тестирования функций бота")
        logger.info("=" * 50)
        
        tests = [
            ("Информация о боте", self.test_bot_info),
            ("Подключение к базе данных", self.test_database_connection),
            ("Настройки конфигурации", self.test_config_settings),
            ("Права администратора", self.test_admin_permissions),
            ("Отделы и сотрудники", self.test_departments_and_employees),
            ("Функции отчетов", self.test_reports_functionality),
            ("Отправка сообщений", self.test_send_message),
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            logger.info(f"\n🔍 Тестирование: {test_name}")
            try:
                result = await test_func()
                if result:
                    passed += 1
                    logger.success(f"✅ {test_name}: ПРОЙДЕН")
                else:
                    failed += 1
                    logger.error(f"❌ {test_name}: ПРОВАЛЕН")
            except Exception as e:
                failed += 1
                logger.error(f"❌ {test_name}: ОШИБКА - {e}")
        
        logger.info("\n" + "=" * 50)
        logger.info(f"📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
        logger.info(f"✅ Пройдено: {passed}")
        logger.info(f"❌ Провалено: {failed}")
        logger.info(f"📈 Процент успеха: {(passed / (passed + failed) * 100):.1f}%")
        
        if failed == 0:
            logger.success("🎉 Все тесты пройдены успешно!")
        else:
            logger.warning(f"⚠️ Обнаружено {failed} проблем")
        
        return passed, failed

async def main():
    """Главная функция"""
    tester = BotFunctionTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())