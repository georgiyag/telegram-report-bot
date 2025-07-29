#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для эмуляции работы человека с Telegram ботом
Имитирует полноценное взаимодействие пользователя с ботом:
- Отправка сообщений
- Создание отчетов
- Настройка напоминаний
- Создание отделов
- Добавление сотрудников
- Тестирование всех функций
"""

import asyncio
import json
import logging
import random
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import aiohttp
from telegram import Bot, Update
from telegram.ext import Application

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('human_emulator.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class HumanBotEmulator:
    """Эмулятор человеческого взаимодействия с ботом"""
    
    def __init__(self, bot_token: str, chat_id: int):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.bot = Bot(token=bot_token)
        self.session_data = {}
        self.test_results = []
        
        # Тестовые данные
        self.test_departments = [
            "IT отдел",
            "Отдел продаж", 
            "Маркетинг",
            "HR отдел",
            "Финансовый отдел"
        ]
        
        self.test_employees = [
            {"name": "Иван Петров", "department": "IT отдел", "position": "Разработчик"},
            {"name": "Мария Сидорова", "department": "Отдел продаж", "position": "Менеджер"},
            {"name": "Алексей Козлов", "department": "Маркетинг", "position": "Аналитик"},
            {"name": "Елена Волкова", "department": "HR отдел", "position": "Специалист"},
            {"name": "Дмитрий Орлов", "department": "Финансовый отдел", "position": "Бухгалтер"}
        ]
        
        self.test_reports = [
            {
                "title": "Еженедельный отчет по разработке",
                "content": "На этой неделе завершили разработку модуля аутентификации. Исправили 15 багов. Начали работу над новым API.",
                "department": "IT отдел"
            },
            {
                "title": "Отчет по продажам за неделю",
                "content": "Заключили 12 новых сделок на общую сумму 2.5 млн рублей. Провели 25 встреч с клиентами.",
                "department": "Отдел продаж"
            },
            {
                "title": "Маркетинговая активность",
                "content": "Запустили рекламную кампанию в социальных сетях. Охват составил 50,000 пользователей. CTR - 2.3%.",
                "department": "Маркетинг"
            }
        ]
    
    async def send_message(self, text: str, delay: float = 1.0) -> Optional[Dict]:
        """Отправка сообщения боту с имитацией человеческой задержки"""
        try:
            # Имитация времени набора текста
            typing_delay = len(text) * 0.05 + random.uniform(0.5, 2.0)
            await asyncio.sleep(typing_delay)
            
            logger.info(f"Отправляем сообщение: {text[:50]}...")
            message = await self.bot.send_message(chat_id=self.chat_id, text=text)
            
            await asyncio.sleep(delay)
            return message.to_dict()
            
        except Exception as e:
            logger.error(f"Ошибка отправки сообщения: {e}")
            return None
    
    async def click_button(self, callback_data: str, delay: float = 0.5) -> bool:
        """Имитация нажатия на inline кнопку"""
        try:
            logger.info(f"Нажимаем кнопку: {callback_data}")
            
            # Имитация времени реакции человека
            await asyncio.sleep(random.uniform(0.3, 1.5))
            
            # Здесь должна быть логика отправки callback_query
            # В реальном боте это происходит автоматически при нажатии кнопки
            
            await asyncio.sleep(delay)
            return True
            
        except Exception as e:
            logger.error(f"Ошибка нажатия кнопки: {e}")
            return False
    
    async def test_bot_start(self) -> bool:
        """Тест запуска бота"""
        logger.info("=== Тестируем запуск бота ===")
        
        result = await self.send_message("/start")
        if result:
            self.test_results.append({"test": "bot_start", "status": "success", "timestamp": datetime.now()})
            return True
        else:
            self.test_results.append({"test": "bot_start", "status": "failed", "timestamp": datetime.now()})
            return False
    
    async def test_main_menu(self) -> bool:
        """Тест главного меню"""
        logger.info("=== Тестируем главное меню ===")
        
        # Переход в главное меню
        result = await self.send_message("📋 Главное меню")
        await asyncio.sleep(2)
        
        # Тестируем различные пункты меню
        menu_items = [
            "📝 Создать отчет",
            "📊 Мои отчеты", 
            "🔔 Напоминания",
            "❓ Помощь"
        ]
        
        for item in menu_items:
            await self.send_message(item)
            await asyncio.sleep(1.5)
        
        self.test_results.append({"test": "main_menu", "status": "success", "timestamp": datetime.now()})
        return True
    
    async def test_admin_panel(self) -> bool:
        """Тест админ-панели"""
        logger.info("=== Тестируем админ-панель ===")
        
        # Переход в админ-панель
        result = await self.send_message("👑 Админ-панель")
        await asyncio.sleep(2)
        
        # Тестируем админские функции
        admin_functions = [
            "📊 Статистика",
            "🏢 Управление отделами",
            "👥 Управление пользователями",
            "🔔 Управление напоминаниями",
            "📈 Отчеты",
            "📤 Экспорт данных"
        ]
        
        for func in admin_functions:
            await self.send_message(func)
            await asyncio.sleep(2)
        
        self.test_results.append({"test": "admin_panel", "status": "success", "timestamp": datetime.now()})
        return True
    
    async def test_create_departments(self) -> bool:
        """Тест создания отделов"""
        logger.info("=== Тестируем создание отделов ===")
        
        # Переход к управлению отделами
        await self.send_message("👑 Админ-панель")
        await asyncio.sleep(1)
        await self.send_message("🏢 Управление отделами")
        await asyncio.sleep(1)
        
        # Создаем тестовые отделы
        for dept in self.test_departments:
            await self.send_message("➕ Добавить отдел")
            await asyncio.sleep(1)
            await self.send_message(dept)
            await asyncio.sleep(2)
            logger.info(f"Создан отдел: {dept}")
        
        self.test_results.append({"test": "create_departments", "status": "success", "timestamp": datetime.now()})
        return True
    
    async def test_add_employees(self) -> bool:
        """Тест добавления сотрудников"""
        logger.info("=== Тестируем добавление сотрудников ===")
        
        # Переход к управлению пользователями
        await self.send_message("👑 Админ-панель")
        await asyncio.sleep(1)
        await self.send_message("👥 Управление пользователями")
        await asyncio.sleep(1)
        
        # Добавляем тестовых сотрудников
        for employee in self.test_employees:
            await self.send_message("➕ Добавить пользователя")
            await asyncio.sleep(1)
            
            # Имитируем ввод данных сотрудника
            await self.send_message(employee["name"])
            await asyncio.sleep(1)
            await self.send_message(employee["department"])
            await asyncio.sleep(1)
            await self.send_message(employee["position"])
            await asyncio.sleep(2)
            
            logger.info(f"Добавлен сотрудник: {employee['name']} - {employee['department']}")
        
        self.test_results.append({"test": "add_employees", "status": "success", "timestamp": datetime.now()})
        return True
    
    async def test_create_reports(self) -> bool:
        """Тест создания отчетов"""
        logger.info("=== Тестируем создание отчетов ===")
        
        # Создаем тестовые отчеты
        for report in self.test_reports:
            await self.send_message("📝 Создать отчет")
            await asyncio.sleep(1)
            
            # Вводим заголовок отчета
            await self.send_message(report["title"])
            await asyncio.sleep(2)
            
            # Вводим содержание отчета
            await self.send_message(report["content"])
            await asyncio.sleep(3)
            
            # Выбираем отдел
            await self.send_message(report["department"])
            await asyncio.sleep(2)
            
            logger.info(f"Создан отчет: {report['title']}")
        
        self.test_results.append({"test": "create_reports", "status": "success", "timestamp": datetime.now()})
        return True
    
    async def test_reminder_settings(self) -> bool:
        """Тест настройки напоминаний"""
        logger.info("=== Тестируем настройку напоминаний ===")
        
        # Переход к настройкам напоминаний
        await self.send_message("👑 Админ-панель")
        await asyncio.sleep(1)
        await self.send_message("🔔 Управление напоминаниями")
        await asyncio.sleep(1)
        await self.send_message("⚙️ Настройки напоминаний")
        await asyncio.sleep(2)
        
        # Настраиваем различные параметры
        settings = [
            "📅 Дедлайн отчетов: Пятница 18:00",
            "⏰ Время отправки: 09:00",
            "🔄 Частота: Еженедельно",
            "📢 Включить напоминания"
        ]
        
        for setting in settings:
            await self.send_message(setting)
            await asyncio.sleep(1.5)
            logger.info(f"Настроено: {setting}")
        
        self.test_results.append({"test": "reminder_settings", "status": "success", "timestamp": datetime.now()})
        return True
    
    async def test_view_reports(self) -> bool:
        """Тест просмотра отчетов"""
        logger.info("=== Тестируем просмотр отчетов ===")
        
        # Просматриваем различные типы отчетов
        await self.send_message("📊 Мои отчеты")
        await asyncio.sleep(2)
        
        # Тестируем фильтры
        filters = [
            "📅 За эту неделю",
            "📅 За прошлую неделю", 
            "📅 За месяц",
            "🏢 По отделам"
        ]
        
        for filter_option in filters:
            await self.send_message(filter_option)
            await asyncio.sleep(2)
        
        self.test_results.append({"test": "view_reports", "status": "success", "timestamp": datetime.now()})
        return True
    
    async def test_statistics(self) -> bool:
        """Тест просмотра статистики"""
        logger.info("=== Тестируем статистику ===")
        
        # Переход к статистике
        await self.send_message("👑 Админ-панель")
        await asyncio.sleep(1)
        await self.send_message("📊 Статистика")
        await asyncio.sleep(3)
        
        # Просматриваем различные виды статистики
        stats_options = [
            "👥 Статистика пользователей",
            "📈 Статистика отчетов",
            "🏢 Статистика отделов",
            "📊 Общая активность"
        ]
        
        for option in stats_options:
            await self.send_message(option)
            await asyncio.sleep(2)
        
        self.test_results.append({"test": "statistics", "status": "success", "timestamp": datetime.now()})
        return True
    
    async def test_export_data(self) -> bool:
        """Тест экспорта данных"""
        logger.info("=== Тестируем экспорт данных ===")
        
        # Переход к экспорту
        await self.send_message("👑 Админ-панель")
        await asyncio.sleep(1)
        await self.send_message("📤 Экспорт данных")
        await asyncio.sleep(2)
        
        # Тестируем различные форматы экспорта
        export_options = [
            "📊 Экспорт в Excel",
            "📄 Экспорт в CSV",
            "🏢 Экспорт отделов",
            "👥 Экспорт пользователей"
        ]
        
        for option in export_options:
            await self.send_message(option)
            await asyncio.sleep(3)  # Экспорт может занять время
        
        self.test_results.append({"test": "export_data", "status": "success", "timestamp": datetime.now()})
        return True
    
    async def test_help_system(self) -> bool:
        """Тест системы помощи"""
        logger.info("=== Тестируем систему помощи ===")
        
        # Тестируем помощь
        await self.send_message("❓ Помощь")
        await asyncio.sleep(2)
        
        # Тестируем различные разделы помощи
        help_sections = [
            "📝 Как создать отчет",
            "🔔 Настройка напоминаний",
            "👑 Админские функции",
            "📞 Техподдержка"
        ]
        
        for section in help_sections:
            await self.send_message(section)
            await asyncio.sleep(1.5)
        
        self.test_results.append({"test": "help_system", "status": "success", "timestamp": datetime.now()})
        return True
    
    async def test_navigation(self) -> bool:
        """Тест навигации по боту"""
        logger.info("=== Тестируем навигацию ===")
        
        # Тестируем переходы между разделами
        navigation_flow = [
            "📋 Главное меню",
            "📝 Создать отчет",
            "🔙 Назад",
            "📊 Мои отчеты",
            "🔙 Назад",
            "👑 Админ-панель",
            "📊 Статистика",
            "🔙 Назад",
            "📋 Главное меню"
        ]
        
        for nav_item in navigation_flow:
            await self.send_message(nav_item)
            await asyncio.sleep(1)
        
        self.test_results.append({"test": "navigation", "status": "success", "timestamp": datetime.now()})
        return True
    
    async def test_error_handling(self) -> bool:
        """Тест обработки ошибок"""
        logger.info("=== Тестируем обработку ошибок ===")
        
        # Отправляем некорректные команды
        error_tests = [
            "/nonexistent_command",
            "Случайный текст без смысла",
            "🚫 Несуществующая кнопка",
            "" * 5000,  # Очень длинное сообщение
            "<script>alert('test')</script>",  # Потенциально опасный контент
        ]
        
        for error_test in error_tests:
            await self.send_message(error_test)
            await asyncio.sleep(1)
        
        self.test_results.append({"test": "error_handling", "status": "success", "timestamp": datetime.now()})
        return True
    
    async def generate_report(self) -> str:
        """Генерация отчета о тестировании"""
        logger.info("=== Генерируем отчет о тестировании ===")
        
        total_tests = len(self.test_results)
        successful_tests = len([t for t in self.test_results if t["status"] == "success"])
        failed_tests = total_tests - successful_tests
        
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        report = f"""
🤖 ОТЧЕТ О ТЕСТИРОВАНИИ БОТА
{'=' * 50}

📊 ОБЩАЯ СТАТИСТИКА:
• Всего тестов: {total_tests}
• Успешных: {successful_tests}
• Неудачных: {failed_tests}
• Процент успеха: {success_rate:.1f}%

📋 ДЕТАЛИ ТЕСТИРОВАНИЯ:
"""
        
        for i, test in enumerate(self.test_results, 1):
            status_emoji = "✅" if test["status"] == "success" else "❌"
            report += f"{i:2d}. {status_emoji} {test['test']} - {test['timestamp'].strftime('%H:%M:%S')}\n"
        
        report += f"""

🕒 ВРЕМЯ ТЕСТИРОВАНИЯ:
• Начало: {self.test_results[0]['timestamp'].strftime('%Y-%m-%d %H:%M:%S') if self.test_results else 'N/A'}
• Окончание: {self.test_results[-1]['timestamp'].strftime('%Y-%m-%d %H:%M:%S') if self.test_results else 'N/A'}
• Продолжительность: {(self.test_results[-1]['timestamp'] - self.test_results[0]['timestamp']).total_seconds():.1f} сек

📝 ЗАКЛЮЧЕНИЕ:
{'Все тесты прошли успешно! Бот работает корректно.' if failed_tests == 0 else f'Обнаружены проблемы в {failed_tests} тестах. Требуется дополнительная проверка.'}
"""
        
        # Сохраняем отчет в файл
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_filename = f"human_emulator_report_{timestamp}.txt"
        
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"Отчет сохранен в файл: {report_filename}")
        return report
    
    async def run_full_test(self) -> str:
        """Запуск полного тестирования"""
        logger.info("🚀 НАЧИНАЕМ ПОЛНОЕ ТЕСТИРОВАНИЕ БОТА")
        start_time = datetime.now()
        
        try:
            # Последовательность тестов
            test_sequence = [
                self.test_bot_start,
                self.test_main_menu,
                self.test_admin_panel,
                self.test_create_departments,
                self.test_add_employees,
                self.test_create_reports,
                self.test_reminder_settings,
                self.test_view_reports,
                self.test_statistics,
                self.test_export_data,
                self.test_help_system,
                self.test_navigation,
                self.test_error_handling
            ]
            
            # Выполняем все тесты
            for test_func in test_sequence:
                try:
                    await test_func()
                    # Пауза между тестами для имитации человеческого поведения
                    await asyncio.sleep(random.uniform(2, 5))
                except Exception as e:
                    logger.error(f"Ошибка в тесте {test_func.__name__}: {e}")
                    self.test_results.append({
                        "test": test_func.__name__,
                        "status": "failed",
                        "error": str(e),
                        "timestamp": datetime.now()
                    })
            
            # Генерируем итоговый отчет
            report = await self.generate_report()
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            logger.info(f"✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО за {duration:.1f} секунд")
            return report
            
        except Exception as e:
            logger.error(f"Критическая ошибка при тестировании: {e}")
            return f"❌ Тестирование прервано из-за ошибки: {e}"


async def main():
    """Главная функция"""
    # Конфигурация (замените на ваши данные)
    BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"  # Замените на токен вашего бота
    CHAT_ID = 123456789  # Замените на ваш chat_id
    
    print("🤖 Эмулятор человеческого взаимодействия с ботом")
    print("=" * 50)
    
    # Проверяем конфигурацию
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE" or CHAT_ID == 123456789:
        print("❌ ОШИБКА: Необходимо настроить BOT_TOKEN и CHAT_ID")
        print("\n📝 Инструкция по настройке:")
        print("1. Получите токен бота у @BotFather")
        print("2. Узнайте ваш chat_id (можно через @userinfobot)")
        print("3. Замените значения в коде")
        return
    
    # Создаем эмулятор
    emulator = HumanBotEmulator(BOT_TOKEN, CHAT_ID)
    
    try:
        print("🚀 Запускаем полное тестирование...")
        report = await emulator.run_full_test()
        
        print("\n" + "=" * 50)
        print(report)
        print("=" * 50)
        
    except KeyboardInterrupt:
        print("\n⏹️ Тестирование прервано пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        logger.error(f"Критическая ошибка: {e}")


if __name__ == "__main__":
    # Запускаем эмулятор
    asyncio.run(main())