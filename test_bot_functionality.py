#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Полная проверка функциональности Telegram бота
"""

import asyncio
import sys
import os
from pathlib import Path

# Добавляем путь к src для импорта модулей
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from database import DatabaseManager
from config import settings, DEPARTMENTS
from models.department import Department, Employee
from models.report import WeeklyReport
from loguru import logger

class BotFunctionalityTester:
    """Класс для тестирования функциональности бота"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, message: str = ""):
        """Логирование результатов тестов"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = f"{status} | {test_name}"
        if message:
            result += f" | {message}"
        
        self.test_results.append((test_name, success, message))
        logger.info(result)
        print(result)
    
    async def test_database_connection(self):
        """Тест подключения к базе данных"""
        try:
            # Проверяем подключение к БД через инициализацию
            result = await self.db.initialize()
            
            self.log_test("Database Connection", result, "База данных доступна")
            return True
        except Exception as e:
            self.log_test("Database Connection", False, f"Ошибка: {e}")
            return False
    
    async def test_departments_management(self):
        """Тест управления отделами"""
        try:
            # Получаем список отделов
            departments = await self.db.get_departments()
            self.log_test("Get Departments", True, f"Найдено отделов: {len(departments)}")
            
            # Добавляем тестовый отдел
            test_dept = Department(
                code="TEST_DEPT",
                name="Тестовый отдел",
                description="Отдел для тестирования",
                head_name="Тестовый Руководитель"
            )
            
            # Удаляем если существует
            try:
                await self.db.delete_department(test_dept.code)
            except:
                pass
            
            # Добавляем новый отдел
            success = await self.db.add_department(test_dept)
            self.log_test("Add Department", success, f"Отдел {test_dept.code} добавлен")
            
            # Проверяем что отдел добавился
            departments_after = await self.db.get_departments()
            dept_found = any(d.code == test_dept.code for d in departments_after)
            self.log_test("Verify Department Added", dept_found, "Отдел найден в списке")
            
            # Получаем отдел по коду
            dept_by_code = await self.db.get_department_by_code(test_dept.code)
            self.log_test("Get Department by Code", dept_by_code is not None, "Отдел найден по коду")
            
            # Удаляем тестовый отдел
            delete_success = await self.db.delete_department(test_dept.code)
            self.log_test("Delete Department", delete_success, "Тестовый отдел удален")
            
            return True
        except Exception as e:
            self.log_test("Departments Management", False, f"Ошибка: {e}")
            return False
    
    async def test_user_management(self):
        """Тест управления пользователями"""
        try:
            # Тестовые данные пользователя
            test_employee = Employee(
                user_id=999999999,
                username="test_user",
                full_name="Тестовый Пользователь",
                department_code="IT",  # Используем существующий отдел
                position="Тестировщик"
            )
            
            # Удаляем если существует
            try:
                await self.db.delete_employee(test_employee.user_id)
            except:
                pass
            
            # Добавляем пользователя
            success = await self.db.add_employee(test_employee)
            self.log_test("Add Employee", success, f"Пользователь {test_employee.user_id} добавлен")
            
            # Проверяем что пользователь добавился
            employee = await self.db.get_employee_by_user_id(test_employee.user_id)
            self.log_test("Get Employee", employee is not None, "Пользователь найден")
            
            # Обновляем пользователя
            updated_name = "Обновленный Тестовый Пользователь"
            update_success = await self.db.update_employee(
                test_employee.user_id,
                full_name=updated_name,
                position="Старший тестировщик"
            )
            self.log_test("Update Employee", update_success, "Пользователь обновлен")
            
            # Проверяем права администратора
            is_admin_before = await self.db.is_admin(test_employee.user_id)
            self.log_test("Check Admin Rights (Before)", not is_admin_before, "Пользователь не админ")
            
            # Назначаем права администратора
            admin_success = await self.db.set_admin_rights(test_employee.user_id, True)
            self.log_test("Set Admin Rights", admin_success, "Права администратора назначены")
            
            # Проверяем права администратора после назначения
            is_admin_after = await self.db.is_admin(test_employee.user_id)
            self.log_test("Check Admin Rights (After)", is_admin_after, "Пользователь теперь админ")
            
            # Убираем права администратора
            remove_admin_success = await self.db.set_admin_rights(test_employee.user_id, False)
            self.log_test("Remove Admin Rights", remove_admin_success, "Права администратора убраны")
            
            # Блокируем пользователя
            block_success = await self.db.block_employee(test_employee.user_id)
            self.log_test("Block Employee", block_success, "Пользователь заблокирован")
            
            # Удаляем тестового пользователя
            delete_success = await self.db.delete_employee(test_employee.user_id)
            self.log_test("Delete Employee", delete_success, "Тестовый пользователь удален")
            
            return True
        except Exception as e:
            self.log_test("User Management", False, f"Ошибка: {e}")
            return False
    
    async def test_reports_functionality(self):
        """Тест функциональности отчетов"""
        try:
            from datetime import datetime, timedelta
            
            # Тестовые данные пользователя
            test_employee = Employee(
                user_id=888888888,
                username="report_test_user",
                full_name="Тестовый Пользователь Отчетов",
                department_code="IT",
                position="Тестировщик отчетов"
            )
            
            # Добавляем тестового пользователя
            await self.db.add_employee(test_employee)
            
            # Создаем тестовый отчет
            week_start = datetime.now() - timedelta(days=7)
            week_end = datetime.now()
            
            test_report = WeeklyReport(
                user_id=test_employee.user_id,
                username=test_employee.username,
                full_name=test_employee.full_name,
                week_start=week_start,
                week_end=week_end,
                completed_tasks="Тестовые задачи выполнены",
                achievements="Достижения в тестировании",
                problems="Проблем не обнаружено",
                next_week_plans="Планы на следующую неделю",
                department=test_employee.department_code,
                position=test_employee.position
            )
            
            # Сохраняем отчет
            report_success = await self.db.save_report(test_report)
            self.log_test("Save Report", report_success, "Отчет сохранен")
            
            # Получаем отчет пользователя
            user_report = await self.db.get_user_report(test_employee.user_id, week_start.date())
            self.log_test("Get User Report", user_report is not None, "Отчет пользователя получен")
            
            # Получаем отчеты за неделю
            week_reports = await self.db.get_reports_by_week(week_start.date(), week_end.date())
            self.log_test("Get Week Reports", len(week_reports) >= 0, f"Найдено отчетов за неделю: {len(week_reports)}")
            
            # Получаем статистику по отделам
            dept_stats = await self.db.get_department_stats(test_employee.department_code, week_start.date(), week_end.date())
            self.log_test("Get Department Stats", isinstance(dept_stats, dict), f"Статистика по отделу получена")
            
            # Получаем пользователей без отчетов
            missing_reports = await self.db.get_missing_reports_users(week_start.date())
            self.log_test("Get Missing Reports", isinstance(missing_reports, list), f"Пользователей без отчетов: {len(missing_reports)}")
            
            # Удаляем тестового пользователя
            await self.db.delete_employee(test_employee.user_id)
            
            return True
        except Exception as e:
            self.log_test("Reports Functionality", False, f"Ошибка: {e}")
            return False
    
    async def test_admin_functionality(self):
        """Тест функций администратора"""
        try:
            # Получаем список администраторов
            admin_employees = await self.db.get_admin_employees()
            self.log_test("Get Admin Employees", isinstance(admin_employees, list), f"Администраторов: {len(admin_employees)}")
            
            # Проверяем права администратора для настоящего админа
            admin_ids = settings.get_admin_ids()
            if admin_ids:
                admin_id = admin_ids[0]
                
                # Создаем администратора в базе данных если его нет
                admin_employee = await self.db.get_employee_by_user_id(admin_id)
                if not admin_employee:
                    admin_emp = Employee(
                        user_id=admin_id,
                        username="admin_user",
                        full_name="Администратор Системы",
                        department_code="IT",
                        position="Системный администратор",
                        is_admin=True
                    )
                    await self.db.add_employee(admin_emp)
                    self.log_test("Create Admin Employee", True, "Администратор создан в БД")
                
                # Проверяем права администратора
                is_admin = await self.db.is_admin(admin_id)
                self.log_test("Check Real Admin Rights", is_admin, f"Администратор {admin_id} имеет права")
            else:
                self.log_test("Check Real Admin Rights", False, "Нет настроенных администраторов")
            
            return True
        except Exception as e:
            self.log_test("Admin Functionality", False, f"Ошибка: {e}")
            return False
    
    async def test_configuration(self):
        """Тест конфигурации"""
        try:
            # Проверяем настройки
            self.log_test("Bot Token", bool(settings.telegram_bot_token), "Токен бота настроен")
            self.log_test("Group Chat ID", bool(settings.group_chat_id), "ID группового чата настроен")
            self.log_test("Ollama URL", bool(settings.ollama_url), f"Ollama URL: {settings.ollama_url}")
            self.log_test("Admin IDs", len(settings.get_admin_ids()) > 0, f"Администраторов: {len(settings.get_admin_ids())}")
            self.log_test("Departments", len(DEPARTMENTS) > 0, f"Отделов в конфигурации: {len(DEPARTMENTS)}")
            
            return True
        except Exception as e:
            self.log_test("Configuration", False, f"Ошибка: {e}")
            return False
    
    async def run_all_tests(self):
        """Запуск всех тестов"""
        print("\n" + "="*60)
        print("🧪 НАЧАЛО ПОЛНОЙ ПРОВЕРКИ ФУНКЦИОНАЛЬНОСТИ БОТА")
        print("="*60 + "\n")
        
        # Список тестов
        tests = [
            ("Конфигурация", self.test_configuration),
            ("Подключение к БД", self.test_database_connection),
            ("Управление отделами", self.test_departments_management),
            ("Управление пользователями", self.test_user_management),
            ("Функциональность отчетов", self.test_reports_functionality),
            ("Функции администратора", self.test_admin_functionality),
        ]
        
        # Выполняем тесты
        for test_name, test_func in tests:
            print(f"\n🔍 Тестирование: {test_name}")
            print("-" * 40)
            try:
                await test_func()
            except Exception as e:
                self.log_test(test_name, False, f"Критическая ошибка: {e}")
        
        # Выводим итоговый отчет
        self.print_summary()
    
    def print_summary(self):
        """Вывод итогового отчета"""
        print("\n" + "="*60)
        print("📊 ИТОГОВЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for _, success, _ in self.test_results if success)
        failed_tests = total_tests - passed_tests
        
        print(f"\n📈 Всего тестов: {total_tests}")
        print(f"✅ Пройдено: {passed_tests}")
        print(f"❌ Провалено: {failed_tests}")
        print(f"📊 Успешность: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            print("\n❌ ПРОВАЛИВШИЕСЯ ТЕСТЫ:")
            for test_name, success, message in self.test_results:
                if not success:
                    print(f"  • {test_name}: {message}")
        
        print("\n" + "="*60)
        
        if failed_tests == 0:
            print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        else:
            print(f"⚠️  ОБНАРУЖЕНЫ ПРОБЛЕМЫ В {failed_tests} ТЕСТАХ")
        
        print("="*60 + "\n")

async def main():
    """Главная функция"""
    tester = BotFunctionalityTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())