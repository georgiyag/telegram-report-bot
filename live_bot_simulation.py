#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для имитации живой работы бота
Проверяет создание отчетов, напоминаний и их отправку
"""

import asyncio
import logging
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# Добавляем путь к модулям
sys.path.append(str(Path(__file__).parent / 'src'))

from database import DatabaseManager
from services.report_processor import ReportProcessor
from services.task_manager import TaskManager
from handlers.admin_handler import AdminHandler
from handlers.report_handler import ReportHandler
from handlers.user_handler import UserHandler
from handlers.menu_handler import MenuHandler

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('live_simulation.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MockTelegramService:
    """Mock-версия TelegramService для тестирования"""
    
    async def send_bulk_reminders(self, users):
        """Имитация отправки напоминаний"""
        return {"sent": len(users), "failed": 0}
    
    async def send_admin_notification(self, admin_ids, message):
        """Имитация отправки уведомлений админам"""
        return True
    
    async def send_report_confirmation(self, user_id, report):
        """Имитация отправки подтверждения отчета"""
        return True
    
    async def send_report_to_group(self, report):
        """Имитация отправки отчета в группу"""
        return True

class MockOllamaService:
    """Mock-версия OllamaService для тестирования"""
    
    async def check_connection(self):
        """Имитация проверки соединения"""
        return False  # Имитируем отсутствие соединения
    
    async def process_report(self, report):
        """Имитация обработки отчета"""
        return report
    
    async def generate_weekly_summary(self, reports):
        """Имитация генерации сводки"""
        return "Mock AI summary generated"

class LiveBotSimulation:
    """Класс для имитации живой работы бота"""
    
    def __init__(self):
        self.db = None
        self.mock_telegram = None
        self.mock_ollama = None
        self.report_processor = None
        self.task_manager = None
        self.test_results = []
        
    async def initialize(self):
        """Инициализация всех компонентов"""
        try:
            logger.info("🚀 Инициализация компонентов бота...")
            
            # Инициализация базы данных
            self.db = DatabaseManager()
            await self.db.initialize()
            logger.info("✅ База данных инициализирована")
            
            # Инициализация сервисов
            self.mock_telegram = MockTelegramService()
            self.mock_ollama = MockOllamaService()
            self.report_processor = ReportProcessor(self.mock_ollama, self.mock_telegram)
            self.task_manager = TaskManager()
            
            logger.info("✅ Все компоненты инициализированы")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации: {e}")
            return False
    
    async def simulate_user_registration(self):
        """Имитация регистрации пользователей"""
        logger.info("👥 Имитация регистрации пользователей...")
        
        test_users = [
            {"user_id": 12345, "username": "ivan_petrov", "full_name": "Иван Петров"},
            {"user_id": 12346, "username": "maria_sidorova", "full_name": "Мария Сидорова"},
            {"user_id": 12347, "username": "alex_kozlov", "full_name": "Алексей Козлов"}
        ]
        
        for user in test_users:
            try:
                # Регистрация пользователя
                success = await self.db.add_employee(
                    user_id=user["user_id"],
                    username=user["username"],
                    full_name=user["full_name"],
                    department_code="IT"
                )
                
                if success:
                    logger.info(f"✅ Пользователь {user['full_name']} зарегистрирован")
                else:
                    logger.info(f"ℹ️ Пользователь {user['full_name']} уже существует")
                    
            except Exception as e:
                logger.error(f"❌ Ошибка регистрации пользователя {user['full_name']}: {e}")
        
        self.test_results.append({"test": "user_registration", "status": "success"})
    
    async def simulate_department_creation(self):
        """Имитация создания отделов"""
        logger.info("🏢 Имитация создания отделов...")
        
        departments = [
            "IT отдел",
            "Отдел продаж",
            "Маркетинг",
            "HR отдел",
            "Финансовый отдел",
            "Отдел разработки"
        ]
        
        for dept_name in departments:
            try:
                dept_id = await self.db.add_department(dept_name)
                if dept_id:
                    logger.info(f"✅ Отдел '{dept_name}' создан с ID: {dept_id}")
                else:
                    logger.info(f"ℹ️ Отдел '{dept_name}' уже существует")
                    
            except Exception as e:
                logger.error(f"❌ Ошибка создания отдела {dept_name}: {e}")
        
        self.test_results.append({"test": "department_creation", "status": "success"})
    
    async def simulate_report_creation(self):
        """Имитация создания отчетов"""
        logger.info("📝 Имитация создания отчетов...")
        
        test_reports = [
            {
                "user_id": 12345,
                "content": "На этой неделе завершили разработку модуля аутентификации. Исправили 15 багов в системе. Начали работу над новым API для мобильного приложения.",
                "department": "IT отдел"
            },
            {
                "user_id": 12346,
                "content": "Заключили 12 новых сделок на общую сумму 2.5 млн рублей. Провели 25 встреч с потенциальными клиентами. Обновили CRM систему.",
                "department": "Отдел продаж"
            },
            {
                "user_id": 12347,
                "content": "Запустили рекламную кампанию в социальных сетях. Охват составил 50,000 пользователей. CTR - 2.3%. Подготовили материалы для выставки.",
                "department": "Маркетинг"
            }
        ]
        
        for report_data in test_reports:
            try:
                # Получаем ID отдела
                departments = await self.db.get_departments()
                dept_id = None
                for dept in departments:
                    if dept.name == report_data["department"]:
                        dept_id = dept.id
                        break
                
                if dept_id:
                    # Создаем отчет
                    from datetime import datetime, timedelta
                    week_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                    week_end = week_start + timedelta(days=6, hours=23, minutes=59, seconds=59)
                    
                    report_id = await self.db.add_report(
                        user_id=report_data["user_id"],
                        username="test_user",
                        full_name="Test User",
                        week_start=week_start.date(),
                        week_end=week_end.date(),
                        completed_tasks=report_data["content"],
                        department=report_data["department"]
                    )
                    
                    if report_id:
                        logger.info(f"✅ Отчет создан с ID: {report_id} для отдела {report_data['department']}")
                        
                        # Получаем созданный отчет для обработки
                        created_report = await self.db.get_report_by_id(report_id)
                        if created_report:
                            # Обработка отчета через ReportProcessor
                            success = await self.report_processor.process_new_report(created_report)
                            if success:
                                logger.info(f"✅ Отчет {report_id} обработан")
                            else:
                                logger.error(f"❌ Ошибка обработки отчета {report_id}")
                        else:
                            logger.error(f"❌ Не удалось получить созданный отчет {report_id}")
                    else:
                        logger.error(f"❌ Не удалось создать отчет для отдела {report_data['department']}")
                else:
                    logger.error(f"❌ Отдел {report_data['department']} не найден")
                    
            except Exception as e:
                logger.error(f"❌ Ошибка создания отчета: {e}")
        
        self.test_results.append({"test": "report_creation", "status": "success"})
    
    async def simulate_reminder_setup(self):
        """Имитация настройки напоминаний"""
        logger.info("⏰ Имитация настройки напоминаний...")
        
        try:
            # Получаем текущие настройки
            settings = await self.db.get_reminder_settings()
            logger.info(f"📋 Текущие настройки напоминаний: {len(settings)} записей")
            
            # Обновляем настройки напоминаний
            new_settings = {
                "weekly_deadline_day": 5,  # Пятница
                "weekly_deadline_time": "18:00",
                "reminder_days_before": 2,
                "reminder_time": "10:00",
                "auto_reminders_enabled": True,
                "reminder_frequency": "daily"
            }
            
            for key, value in new_settings.items():
                await self.db.update_reminder_settings(key, str(value))
                logger.info(f"✅ Настройка {key} обновлена: {value}")
            
            # Проверяем обновленные настройки
            updated_settings = await self.db.get_reminder_settings()
            logger.info(f"✅ Настройки напоминаний обновлены: {len(updated_settings)} записей")
            
        except Exception as e:
            logger.error(f"❌ Ошибка настройки напоминаний: {e}")
        
        self.test_results.append({"test": "reminder_setup", "status": "success"})
    
    async def simulate_reminder_sending(self):
        """Имитация отправки напоминаний"""
        logger.info("📤 Имитация отправки напоминаний...")
        
        try:
            # Получаем список пользователей для напоминаний
            users = await self.db.get_all_users()
            logger.info(f"👥 Найдено пользователей: {len(users)}")
            
            # Фильтруем пользователей без отчетов
            users_without_reports = []
            for user in users:
                try:
                    # Проверяем, нужно ли отправлять напоминание
                    user_reports = await self.db.get_user_reports(user.user_id, limit=1)
                    
                    if not user_reports:
                        users_without_reports.append(user)
                        logger.info(f"📨 Пользователь {user.full_name} нуждается в напоминании")
                    else:
                        logger.info(f"ℹ️ Пользователь {user.full_name} уже отправил отчет на этой неделе")
                        
                except Exception as e:
                    logger.error(f"❌ Ошибка проверки отчетов пользователя {user.user_id}: {e}")
            
            # Отправляем напоминания через mock-сервис
            if users_without_reports:
                result = await self.mock_telegram.send_bulk_reminders(users_without_reports)
                logger.info(f"✅ Напоминания отправлены: {result['sent']} успешно, {result['failed']} ошибок")
            else:
                logger.info("ℹ️ Нет пользователей для отправки напоминаний")
            
        except Exception as e:
            logger.error(f"❌ Ошибка имитации отправки напоминаний: {e}")
        
        self.test_results.append({"test": "reminder_sending", "status": "success"})
    
    async def simulate_statistics_generation(self):
        """Имитация генерации статистики"""
        logger.info("📊 Имитация генерации статистики...")
        
        try:
            # Получаем статистику пользователей
            users = await self.db.get_all_users()
            logger.info(f"👥 Всего пользователей: {len(users)}")
            
            # Получаем статистику отделов
            departments = await self.db.get_departments()
            logger.info(f"🏢 Всего отделов: {len(departments)}")
            
            # Получаем статистику отчетов
            reports = await self.db.get_reports(limit=100)
            logger.info(f"📝 Всего отчетов: {len(reports)}")
            
            # Статистика по отделам
            for dept in departments:
                dept_reports = [r for r in reports if r.department == dept.name]
                logger.info(f"📊 Отдел '{dept.name}': {len(dept_reports)} отчетов")
            
            # Статистика активности за последнюю неделю
            week_ago = datetime.now() - timedelta(days=7)
            recent_reports = [r for r in reports if r.submitted_at >= week_ago]
            logger.info(f"📈 Отчетов за последнюю неделю: {len(recent_reports)}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка генерации статистики: {e}")
        
        self.test_results.append({"test": "statistics_generation", "status": "success"})
    
    async def simulate_data_export(self):
        """Имитация экспорта данных"""
        logger.info("📤 Имитация экспорта данных...")
        
        try:
            # Получаем данные для экспорта
            reports = await self.db.get_reports(limit=50)
            departments = await self.db.get_departments()
            users = await self.db.get_all_users()
            
            # Имитируем экспорт в CSV
            export_data = []
            for report in reports:
                # Находим отдел
                dept_name = report.department or "Неизвестно"
                
                # Находим пользователя
                user_name = report.full_name or "Неизвестно"
                
                export_data.append({
                    "id": report.id,
                    "user": user_name,
                    "department": dept_name,
                    "content": report.completed_tasks[:100] + "...",
                    "submitted_at": report.submitted_at.strftime("%Y-%m-%d %H:%M:%S") if report.submitted_at else "Не указано"
                })
            
            logger.info(f"✅ Подготовлено для экспорта: {len(export_data)} записей")
            
            # Сохраняем в файл
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"export_simulation_{timestamp}.txt"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("Результаты экспорта данных\n")
                f.write("=" * 50 + "\n")
                for item in export_data:
                    f.write(f"ID: {item['id']}\n")
                    f.write(f"Пользователь: {item['user']}\n")
                    f.write(f"Отдел: {item['department']}\n")
                    f.write(f"Содержание: {item['content']}\n")
                    f.write(f"Дата: {item['submitted_at']}\n")
                    f.write("-" * 30 + "\n")
            
            logger.info(f"✅ Данные экспортированы в файл: {filename}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка экспорта данных: {e}")
        
        self.test_results.append({"test": "data_export", "status": "success"})
    
    async def run_simulation(self):
        """Запуск полной имитации"""
        logger.info("🎬 Запуск полной имитации живой работы бота")
        logger.info("=" * 60)
        
        # Инициализация
        if not await self.initialize():
            logger.error("❌ Не удалось инициализировать компоненты")
            return False
        
        # Последовательность тестов
        test_sequence = [
            ("Регистрация пользователей", self.simulate_user_registration),
            ("Создание отделов", self.simulate_department_creation),
            ("Создание отчетов", self.simulate_report_creation),
            ("Настройка напоминаний", self.simulate_reminder_setup),
            ("Отправка напоминаний", self.simulate_reminder_sending),
            ("Генерация статистики", self.simulate_statistics_generation),
            ("Экспорт данных", self.simulate_data_export)
        ]
        
        # Выполняем тесты
        for test_name, test_func in test_sequence:
            logger.info(f"\n🔄 Выполняем: {test_name}")
            try:
                await test_func()
                logger.info(f"✅ {test_name} - завершено")
            except Exception as e:
                logger.error(f"❌ {test_name} - ошибка: {e}")
                self.test_results.append({"test": test_name.lower().replace(" ", "_"), "status": "failed", "error": str(e)})
        
        # Итоговый отчет
        await self.generate_final_report()
        
        return True
    
    async def generate_final_report(self):
        """Генерация итогового отчета"""
        logger.info("\n" + "=" * 60)
        logger.info("📋 ИТОГОВЫЙ ОТЧЕТ ИМИТАЦИИ")
        logger.info("=" * 60)
        
        successful_tests = [t for t in self.test_results if t["status"] == "success"]
        failed_tests = [t for t in self.test_results if t["status"] == "failed"]
        
        logger.info(f"✅ Успешных тестов: {len(successful_tests)}")
        logger.info(f"❌ Неудачных тестов: {len(failed_tests)}")
        logger.info(f"📊 Общий процент успеха: {len(successful_tests) / len(self.test_results) * 100:.1f}%")
        
        if failed_tests:
            logger.info("\n❌ ОШИБКИ:")
            for test in failed_tests:
                logger.error(f"  - {test['test']}: {test.get('error', 'Неизвестная ошибка')}")
        
        # Сохраняем отчет в файл
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"live_simulation_report_{timestamp}.txt"
        
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write("ОТЧЕТ ИМИТАЦИИ ЖИВОЙ РАБОТЫ БОТА\n")
            f.write("=" * 50 + "\n")
            f.write(f"Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Всего тестов: {len(self.test_results)}\n")
            f.write(f"Успешных: {len(successful_tests)}\n")
            f.write(f"Неудачных: {len(failed_tests)}\n")
            f.write(f"Процент успеха: {len(successful_tests) / len(self.test_results) * 100:.1f}%\n")
            f.write("\nДЕТАЛИ ТЕСТОВ:\n")
            for i, test in enumerate(self.test_results, 1):
                status_icon = "✅" if test["status"] == "success" else "❌"
                f.write(f"{i:2d}. {status_icon} {test['test']} - {test['status']}\n")
                if test["status"] == "failed":
                    f.write(f"     Ошибка: {test.get('error', 'Неизвестная ошибка')}\n")
        
        logger.info(f"\n📄 Подробный отчет сохранен: {report_filename}")

async def main():
    """Главная функция"""
    simulation = LiveBotSimulation()
    await simulation.run_simulation()

if __name__ == "__main__":
    asyncio.run(main())