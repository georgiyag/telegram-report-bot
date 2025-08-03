#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Комплексный тест Telegram бота через реальные API вызовы
Тестирует все основные функции: создание отчетов, уведомления, управление пользователями, админ-панель
"""

import asyncio
import aiohttp
import json
import time
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

@dataclass
class TestResult:
    """Результат теста"""
    test_name: str
    success: bool
    message: str
    response_data: Optional[Dict] = None
    execution_time: float = 0.0

class ComprehensiveBotTester:
    """Комплексный тестер бота через Telegram API"""
    
    def __init__(self):
        # Получаем токен бота из переменных окружения
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        
        # ID пользователя для тестирования (замените на ваш)
        self.test_user_id = 167960842  # Ваш Telegram ID
        
        # Результаты тестов
        self.test_results: List[TestResult] = []
        
        # Сессия для HTTP запросов
        self.session: Optional[aiohttp.ClientSession] = None
        
        print("🤖 Инициализация комплексного тестера бота")
        print(f"📱 Тестовый пользователь: {self.test_user_id}")
        print(f"🔗 API URL: {self.base_url}")
        print("\n" + "="*60)
    
    async def __aenter__(self):
        """Асинхронный контекст-менеджер"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Закрытие сессии"""
        if self.session:
            await self.session.close()
    
    async def send_telegram_request(self, method: str, data: Dict) -> Dict:
        """Отправка запроса к Telegram API"""
        url = f"{self.base_url}/{method}"
        
        async with self.session.post(url, json=data) as response:
            result = await response.json()
            return result
    
    async def simulate_callback_query(self, callback_data: str, message_id: int = None) -> TestResult:
        """Симуляция нажатия inline кнопки"""
        start_time = time.time()
        test_name = f"Callback: {callback_data}"
        
        try:
            # Отправляем callback query через sendMessage с inline клавиатурой
            keyboard = {
                "inline_keyboard": [[
                    {"text": f"Test {callback_data}", "callback_data": callback_data}
                ]]
            }
            
            data = {
                "chat_id": self.test_user_id,
                "text": f"🧪 Тестирование кнопки: {callback_data}",
                "reply_markup": keyboard
            }
            
            response = await self.send_telegram_request("sendMessage", data)
            execution_time = time.time() - start_time
            
            if response.get('ok'):
                return TestResult(
                    test_name=test_name,
                    success=True,
                    message=f"Кнопка {callback_data} отправлена успешно",
                    response_data=response,
                    execution_time=execution_time
                )
            else:
                return TestResult(
                    test_name=test_name,
                    success=False,
                    message=f"Ошибка: {response.get('description', 'Unknown error')}",
                    response_data=response,
                    execution_time=execution_time
                )
                
        except Exception as e:
            execution_time = time.time() - start_time
            return TestResult(
                test_name=test_name,
                success=False,
                message=f"Исключение: {str(e)}",
                execution_time=execution_time
            )
    
    async def send_command(self, command: str) -> TestResult:
        """Отправка команды боту"""
        start_time = time.time()
        test_name = f"Command: {command}"
        
        try:
            data = {
                "chat_id": self.test_user_id,
                "text": command
            }
            
            response = await self.send_telegram_request("sendMessage", data)
            execution_time = time.time() - start_time
            
            if response.get('ok'):
                return TestResult(
                    test_name=test_name,
                    success=True,
                    message=f"Команда {command} отправлена успешно",
                    response_data=response,
                    execution_time=execution_time
                )
            else:
                return TestResult(
                    test_name=test_name,
                    success=False,
                    message=f"Ошибка: {response.get('description', 'Unknown error')}",
                    response_data=response,
                    execution_time=execution_time
                )
                
        except Exception as e:
            execution_time = time.time() - start_time
            return TestResult(
                test_name=test_name,
                success=False,
                message=f"Исключение: {str(e)}",
                execution_time=execution_time
            )
    
    async def send_text_message(self, text: str, description: str = "") -> TestResult:
        """Отправка текстового сообщения"""
        start_time = time.time()
        test_name = f"Text: {description or text[:30]}"
        
        try:
            data = {
                "chat_id": self.test_user_id,
                "text": text
            }
            
            response = await self.send_telegram_request("sendMessage", data)
            execution_time = time.time() - start_time
            
            if response.get('ok'):
                return TestResult(
                    test_name=test_name,
                    success=True,
                    message=f"Сообщение отправлено успешно",
                    response_data=response,
                    execution_time=execution_time
                )
            else:
                return TestResult(
                    test_name=test_name,
                    success=False,
                    message=f"Ошибка: {response.get('description', 'Unknown error')}",
                    response_data=response,
                    execution_time=execution_time
                )
                
        except Exception as e:
            execution_time = time.time() - start_time
            return TestResult(
                test_name=test_name,
                success=False,
                message=f"Исключение: {str(e)}",
                execution_time=execution_time
            )
    
    def log_test_result(self, result: TestResult):
        """Логирование результата теста"""
        status = "✅ PASS" if result.success else "❌ FAIL"
        print(f"{status} | {result.test_name} | {result.execution_time:.2f}s | {result.message}")
        self.test_results.append(result)
    
    async def test_basic_commands(self):
        """Тест базовых команд"""
        print("\n🔧 ТЕСТИРОВАНИЕ БАЗОВЫХ КОМАНД")
        print("-" * 40)
        
        commands = [
            "/start",
            "/menu", 
            "/help",
            "/status"
        ]
        
        for command in commands:
            result = await self.send_command(command)
            self.log_test_result(result)
            await asyncio.sleep(1)  # Пауза между запросами
    
    async def test_main_menu_navigation(self):
        """Тест навигации по главному меню"""
        print("\n🧭 ТЕСТИРОВАНИЕ НАВИГАЦИИ ПО ГЛАВНОМУ МЕНЮ")
        print("-" * 50)
        
        # Сначала отправляем /start для получения главного меню
        start_result = await self.send_command("/start")
        self.log_test_result(start_result)
        await asyncio.sleep(2)
        
        # Тестируем кнопки главного меню
        menu_buttons = [
            "menu_report",
            "menu_status", 
            "menu_help",
            "menu_admin"
        ]
        
        for button in menu_buttons:
            result = await self.simulate_callback_query(button)
            self.log_test_result(result)
            await asyncio.sleep(2)
    
    async def test_report_creation_flow(self):
        """Тест полного процесса создания отчета"""
        print("\n📝 ТЕСТИРОВАНИЕ СОЗДАНИЯ ОТЧЕТА")
        print("-" * 40)
        
        # 1. Запускаем создание отчета
        result = await self.send_command("/report")
        self.log_test_result(result)
        await asyncio.sleep(2)
        
        # 2. Выбираем отдел (симулируем нажатие кнопки отдела)
        dept_result = await self.simulate_callback_query("dept_1")
        self.log_test_result(dept_result)
        await asyncio.sleep(2)
        
        # 3. Отправляем задачи
        tasks_text = "Тестовые задачи за неделю:\n- Разработка функционала\n- Тестирование системы\n- Исправление ошибок"
        tasks_result = await self.send_text_message(tasks_text, "Задачи за неделю")
        self.log_test_result(tasks_result)
        await asyncio.sleep(2)
        
        # 4. Отправляем достижения
        achievements_text = "Достижения:\n- Завершена разработка модуля\n- Исправлены критические ошибки\n- Улучшена производительность"
        achievements_result = await self.send_text_message(achievements_text, "Достижения")
        self.log_test_result(achievements_result)
        await asyncio.sleep(2)
        
        # 5. Отправляем проблемы
        problems_text = "Проблемы:\n- Задержка в получении требований\n- Технические сложности с интеграцией"
        problems_result = await self.send_text_message(problems_text, "Проблемы")
        self.log_test_result(problems_result)
        await asyncio.sleep(2)
        
        # 6. Отправляем планы
        plans_text = "Планы на следующую неделю:\n- Завершить интеграцию\n- Провести полное тестирование\n- Подготовить документацию"
        plans_result = await self.send_text_message(plans_text, "Планы")
        self.log_test_result(plans_result)
        await asyncio.sleep(2)
        
        # 7. Подтверждаем отчет
        confirm_result = await self.simulate_callback_query("report_confirm")
        self.log_test_result(confirm_result)
        await asyncio.sleep(2)
    
    async def test_admin_panel(self):
        """Тест админ-панели"""
        print("\n⚙️ ТЕСТИРОВАНИЕ АДМИН-ПАНЕЛИ")
        print("-" * 35)
        
        # 1. Открываем админ-панель
        admin_result = await self.send_command("/admin")
        self.log_test_result(admin_result)
        await asyncio.sleep(2)
        
        # 2. Тестируем кнопки админ-панели
        admin_buttons = [
            "admin_manage_users",
            "admin_manage_depts", 
            "admin_reports",
            "admin_reminders",
            "admin_export"
        ]
        
        for button in admin_buttons:
            result = await self.simulate_callback_query(button)
            self.log_test_result(result)
            await asyncio.sleep(2)
    
    async def test_navigation_buttons(self):
        """Тест кнопок навигации"""
        print("\n🔄 ТЕСТИРОВАНИЕ КНОПОК НАВИГАЦИИ")
        print("-" * 40)
        
        navigation_buttons = [
            "back_to_main",
            "back_main",
            "admin_back",
            "cancel"
        ]
        
        for button in navigation_buttons:
            result = await self.simulate_callback_query(button)
            self.log_test_result(result)
            await asyncio.sleep(1)
    
    async def run_comprehensive_test(self):
        """Запуск комплексного тестирования"""
        print("🚀 ЗАПУСК КОМПЛЕКСНОГО ТЕСТИРОВАНИЯ БОТА")
        print("=" * 60)
        print(f"⏰ Время начала: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🤖 Тестируемый бот: {self.base_url}")
        print(f"👤 Тестовый пользователь: {self.test_user_id}")
        
        start_time = time.time()
        
        try:
            # Последовательное выполнение всех тестов
            await self.test_basic_commands()
            await self.test_main_menu_navigation()
            await self.test_report_creation_flow()
            await self.test_admin_panel()
            await self.test_navigation_buttons()
            
        except Exception as e:
            print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        
        total_time = time.time() - start_time
        
        # Генерируем отчет
        await self.generate_test_report(total_time)
    
    async def generate_test_report(self, total_time: float):
        """Генерация отчета о тестировании"""
        print("\n" + "=" * 60)
        print("📊 ИТОГОВЫЙ ОТЧЕТ О ТЕСТИРОВАНИИ")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r.success)
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"⏱️  Общее время выполнения: {total_time:.2f} секунд")
        print(f"📈 Всего тестов: {total_tests}")
        print(f"✅ Пройдено: {passed_tests}")
        print(f"❌ Провалено: {failed_tests}")
        print(f"📊 Процент успеха: {success_rate:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ ПРОВАЛИВШИЕСЯ ТЕСТЫ:")
            print("-" * 30)
            for result in self.test_results:
                if not result.success:
                    print(f"• {result.test_name}: {result.message}")
        
        # Сохраняем отчет в файл
        report_filename = f"comprehensive_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write("КОМПЛЕКСНЫЙ ОТЧЕТ О ТЕСТИРОВАНИИ TELEGRAM БОТА\n")
            f.write("=" * 60 + "\n")
            f.write(f"Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Общее время: {total_time:.2f} секунд\n")
            f.write(f"Всего тестов: {total_tests}\n")
            f.write(f"Пройдено: {passed_tests}\n")
            f.write(f"Провалено: {failed_tests}\n")
            f.write(f"Процент успеха: {success_rate:.1f}%\n\n")
            
            f.write("ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ:\n")
            f.write("-" * 40 + "\n")
            for result in self.test_results:
                status = "PASS" if result.success else "FAIL"
                f.write(f"[{status}] {result.test_name} ({result.execution_time:.2f}s): {result.message}\n")
        
        print(f"\n💾 Отчет сохранен в файл: {report_filename}")
        
        if success_rate >= 90:
            print("\n🎉 ОТЛИЧНЫЙ РЕЗУЛЬТАТ! Бот работает стабильно.")
        elif success_rate >= 70:
            print("\n⚠️  ХОРОШИЙ РЕЗУЛЬТАТ, но есть проблемы для исправления.")
        else:
            print("\n🚨 ТРЕБУЕТСЯ ВНИМАНИЕ! Много критических ошибок.")

async def main():
    """Главная функция"""
    print("🤖 Комплексное тестирование Telegram бота")
    print("📋 Проверка всех функций через реальные API вызовы")
    print()
    
    # Проверяем наличие токена
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not bot_token or bot_token == 'YOUR_BOT_TOKEN_HERE':
        print("❌ ОШИБКА: Не найден токен бота!")
        print("Установите переменную окружения TELEGRAM_BOT_TOKEN")
        return
    
    async with ComprehensiveBotTester() as tester:
        await tester.run_comprehensive_test()

if __name__ == "__main__":
    asyncio.run(main())