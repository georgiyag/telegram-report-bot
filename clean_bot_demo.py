#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Демонстрация функций Telegram бота для еженедельных отчетов
"""

import sqlite3
import logging
from datetime import datetime, timedelta
import json

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BotDemo:
    def __init__(self):
        self.db_path = 'demo_bot.db'
        self.init_database()
        
    def init_database(self):
        """Инициализация базы данных"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Создание таблиц
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS departments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                department_id INTEGER,
                is_admin BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (department_id) REFERENCES departments (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                week_start DATE NOT NULL,
                week_end DATE NOT NULL,
                completed_tasks TEXT,
                planned_tasks TEXT,
                obstacles TEXT,
                additional_info TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (employee_id) REFERENCES employees (id)
            )
        ''')
        
        # Добавление тестовых данных
        cursor.execute("INSERT OR IGNORE INTO departments (name, description) VALUES (?, ?)",
                      ("IT отдел", "Информационные технологии"))
        cursor.execute("INSERT OR IGNORE INTO departments (name, description) VALUES (?, ?)",
                      ("Маркетинг", "Отдел маркетинга и рекламы"))
        
        conn.commit()
        conn.close()
        logger.info("База данных инициализирована")
    
    def simulate_start_command(self, user_id=12345, username="test_user", first_name="Тест"):
        """Симуляция команды /start"""
        print("\n" + "="*50)
        print("🚀 КОМАНДА /start")
        print("="*50)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Проверка существования пользователя
        cursor.execute("SELECT * FROM employees WHERE telegram_id = ?", (user_id,))
        user = cursor.fetchone()
        
        if user:
            print(f"👋 Добро пожаловать обратно, {first_name}!")
            print("Вы уже зарегистрированы в системе.")
        else:
            # Регистрация нового пользователя
            cursor.execute(
                "INSERT INTO employees (telegram_id, username, first_name, department_id) VALUES (?, ?, ?, ?)",
                (user_id, username, first_name, 1)  # По умолчанию IT отдел
            )
            conn.commit()
            print(f"✅ Пользователь {first_name} успешно зарегистрирован!")
            print("Отдел: IT отдел")
        
        print("\n📋 Доступные команды:")
        print("• /help - Помощь")
        print("• /create_report - Создать отчет")
        print("• /my_reports - Мои отчеты")
        print("• /admin - Админ панель (для администраторов)")
        
        conn.close()
    
    def simulate_report_creation(self, user_id=12345):
        """Симуляция создания отчета"""
        print("\n" + "="*50)
        print("📝 СОЗДАНИЕ ЕЖЕНЕДЕЛЬНОГО ОТЧЕТА")
        print("="*50)
        
        # Получение текущей недели
        today = datetime.now()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        
        print(f"📅 Период: {week_start.strftime('%d.%m.%Y')} - {week_end.strftime('%d.%m.%Y')}")
        print("\n🔄 Процесс создания отчета:")
        
        # Симуляция ввода данных
        completed_tasks = "1. Разработка новой функции авторизации\n2. Исправление багов в модуле отчетов\n3. Код-ревью для коллег"
        planned_tasks = "1. Оптимизация базы данных\n2. Внедрение системы кэширования\n3. Подготовка документации"
        obstacles = "Задержка с получением требований от заказчика"
        additional_info = "Требуется дополнительное время на тестирование"
        
        print("\n✅ Выполненные задачи:")
        print(completed_tasks)
        
        print("\n📋 Планы на следующую неделю:")
        print(planned_tasks)
        
        print("\n⚠️ Препятствия:")
        print(obstacles)
        
        print("\n💡 Дополнительная информация:")
        print(additional_info)
        
        # Сохранение в базу данных
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO reports (employee_id, week_start, week_end, completed_tasks, planned_tasks, obstacles, additional_info) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (1, week_start.date(), week_end.date(), completed_tasks, planned_tasks, obstacles, additional_info)
        )
        conn.commit()
        conn.close()
        
        print("\n✅ Отчет успешно сохранен!")
        print("📧 Уведомление отправлено руководству")
    
    def simulate_admin_panel(self):
        """Симуляция админ панели"""
        print("\n" + "="*50)
        print("👑 АДМИН ПАНЕЛЬ")
        print("="*50)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Статистика пользователей
        cursor.execute("SELECT COUNT(*) FROM employees")
        users_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM reports")
        reports_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM departments")
        departments_count = cursor.fetchone()[0]
        
        print(f"📊 СТАТИСТИКА:")
        print(f"👥 Пользователей: {users_count}")
        print(f"📋 Отчетов: {reports_count}")
        print(f"🏢 Отделов: {departments_count}")
        
        # Последние отчеты
        print("\n📋 ПОСЛЕДНИЕ ОТЧЕТЫ:")
        cursor.execute("""
            SELECT e.first_name, e.username, r.week_start, r.week_end, r.created_at
            FROM reports r
            JOIN employees e ON r.employee_id = e.id
            ORDER BY r.created_at DESC
            LIMIT 5
        """)
        
        reports = cursor.fetchall()
        for i, report in enumerate(reports, 1):
            first_name, username, week_start, week_end, created_at = report
            print(f"{i}. {first_name} (@{username}) - {week_start} до {week_end}")
            print(f"   Создан: {created_at}")
        
        # Отделы
        print("\n🏢 ОТДЕЛЫ:")
        cursor.execute("SELECT name, description FROM departments")
        departments = cursor.fetchall()
        for dept in departments:
            name, description = dept
            print(f"• {name}: {description}")
        
        conn.close()
    
    def simulate_help_system(self):
        """Симуляция системы помощи"""
        print("\n" + "="*50)
        print("❓ СИСТЕМА ПОМОЩИ")
        print("="*50)
        
        help_text = """
🤖 TELEGRAM БОТ ДЛЯ ЕЖЕНЕДЕЛЬНЫХ ОТЧЕТОВ

📋 ОСНОВНЫЕ КОМАНДЫ:
• /start - Регистрация в системе
• /help - Показать эту справку
• /create_report - Создать новый отчет
• /my_reports - Просмотр моих отчетов
• /settings - Настройки профиля

👑 КОМАНДЫ АДМИНИСТРАТОРА:
• /admin - Админ панель
• /stats - Статистика системы
• /export - Экспорт данных
• /broadcast - Рассылка сообщений

📝 КАК СОЗДАТЬ ОТЧЕТ:
1. Используйте команду /create_report
2. Заполните выполненные задачи
3. Укажите планы на следующую неделю
4. Опишите препятствия (если есть)
5. Добавьте дополнительную информацию

⏰ НАПОМИНАНИЯ:
Бот автоматически напоминает о создании отчетов каждую пятницу в 16:00

🔧 ПОДДЕРЖКА:
По вопросам обращайтесь к администратору системы
        """
        
        print(help_text)
    
    def simulate_reminders(self):
        """Симуляция системы напоминаний"""
        print("\n" + "="*50)
        print("⏰ СИСТЕМА НАПОМИНАНИЙ")
        print("="*50)
        
        print("📅 Настройки напоминаний:")
        print("• День недели: Пятница")
        print("• Время: 16:00")
        print("• Часовой пояс: UTC+3")
        
        print("\n📨 Пример напоминания:")
        print("─" * 30)
        print("⏰ Напоминание о отчете")
        print("")
        print("Привет! 👋")
        print("Не забудь создать еженедельный отчет.")
        print("")
        print("📋 Используй команду /create_report")
        print("⏱️ Дедлайн: воскресенье, 23:59")
        print("─" * 30)
        
        print("\n✅ Статус напоминаний: Активны")
        print("📊 Отправлено напоминаний: 15")
        print("📈 Процент ответов: 87%")
    
    def run_full_demo(self):
        """Запуск полной демонстрации"""
        print("🎭 ДЕМОНСТРАЦИЯ TELEGRAM БОТА")
        print("📋 Сценарии демонстрации:")
        print("   1. Команда /start - регистрация пользователя")
        print("   2. Создание еженедельного отчета")
        print("   3. Работа с админ-панелью")
        print("   4. Система помощи")
        print("   5. Система напоминаний")
        
        # Запуск всех демонстраций
        self.simulate_start_command()
        self.simulate_report_creation()
        self.simulate_admin_panel()
        self.simulate_help_system()
        self.simulate_reminders()
        
        print("\n" + "="*50)
        print("🎉 ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА")
        print("="*50)
        print("✅ Все функции бота продемонстрированы")
        print("🚀 Бот готов к работе в реальном Telegram")
        print("📱 Токен бота: 8174058049:AAE8yOlAhKJhJGJHGJHGJHGJHGJHGJHGJHG")
        print("🔗 Ссылка: @your_bot_username")

if __name__ == "__main__":
    demo = BotDemo()
    demo.run_full_demo()