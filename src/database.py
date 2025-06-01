"""Модуль для работы с базой данных SQLite"""

import sqlite3
import asyncio
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from loguru import logger

from models.department import Department, Employee
from models.report import WeeklyReport
from config import settings

class DatabaseManager:
    """Менеджер базы данных SQLite"""
    
    def __init__(self, db_path: str = "data/bot_database.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        self._init_database()
    
    async def initialize(self):
        """Асинхронная инициализация базы данных"""
        self._init_database()
        return True
    
    def _init_database(self):
        """Инициализация базы данных и создание таблиц"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Создание таблицы отделов
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS departments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL UNIQUE,
                        code TEXT NOT NULL UNIQUE,
                        description TEXT,
                        head_name TEXT,
                        report_required BOOLEAN DEFAULT TRUE,
                        report_deadline_day INTEGER DEFAULT 5,
                        report_deadline_hour INTEGER DEFAULT 18,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Создание таблицы сотрудников
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS employees (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL UNIQUE,
                        username TEXT,
                        full_name TEXT NOT NULL,
                        department_code TEXT NOT NULL,
                        position TEXT,
                        employee_id TEXT UNIQUE,
                        email TEXT,
                        phone TEXT,
                        is_active BOOLEAN DEFAULT TRUE,
                        is_blocked BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (department_code) REFERENCES departments (code)
                    )
                """)
                
                # Создание таблицы отчетов
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS reports (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        username TEXT,
                        full_name TEXT NOT NULL,
                        week_start DATE NOT NULL,
                        week_end DATE NOT NULL,
                        completed_tasks TEXT NOT NULL,
                        achievements TEXT,
                        problems TEXT,
                        next_week_plans TEXT,
                        department TEXT,
                        position TEXT,
                        submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_late BOOLEAN DEFAULT FALSE,
                        FOREIGN KEY (user_id) REFERENCES employees (user_id),
                        UNIQUE(user_id, week_start)
                    )
                """)
                
                # Создание индексов для оптимизации
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_reports_week ON reports (week_start, week_end)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_reports_user ON reports (user_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_employees_dept ON employees (department_code)")
                
                conn.commit()
                logger.info("База данных успешно инициализирована")
                
                # Добавляем тестовые данные если база пустая
                self._add_initial_data(cursor, conn)
                
        except Exception as e:
            logger.error(f"Ошибка инициализации базы данных: {e}")
            raise
    
    def _add_initial_data(self, cursor, conn):
        """Добавление начальных данных"""
        # Проверяем есть ли отделы
        cursor.execute("SELECT COUNT(*) FROM departments")
        if cursor.fetchone()[0] == 0:
            # Добавляем тестовые отделы
            departments = [
                ("IT отдел", "IT", "Отдел информационных технологий", "Петров Петр Петрович", True, 5, 18),
                ("Бухгалтерия", "ACCOUNTING", "Бухгалтерский отдел", "Сидорова Анна Ивановна", True, 5, 17),
                ("Производство", "PRODUCTION", "Производственный отдел", "Козлов Сергей Александрович", True, 5, 16),
                ("Управление", "MANAGEMENT", "Отдел управления", "Директор Иван Иванович", False, 5, 18)
            ]
            
            cursor.executemany("""
                INSERT INTO departments (name, code, description, head_name, report_required, report_deadline_day, report_deadline_hour)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, departments)
            
            conn.commit()
            logger.info("Добавлены тестовые отделы")
    
    # CRUD операции для отделов
    async def get_departments(self) -> List[Department]:
        """Получение всех отделов"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM departments ORDER BY name")
                rows = cursor.fetchall()
                
                departments = []
                for row in rows:
                    dept_data = dict(row)
                    departments.append(Department(**dept_data))
                
                return departments
        except Exception as e:
            logger.error(f"Ошибка получения отделов: {e}")
            return []
    
    async def get_department_by_code(self, code: str) -> Optional[Department]:
        """Получение отдела по коду"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM departments WHERE code = ?", (code,))
                row = cursor.fetchone()
                
                if row:
                    return Department(**dict(row))
                return None
        except Exception as e:
            logger.error(f"Ошибка получения отдела {code}: {e}")
            return None
    
    # CRUD операции для сотрудников
    async def get_employees(self) -> List[Employee]:
        """Получение всех сотрудников"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT e.*, d.name as department_name 
                    FROM employees e 
                    LEFT JOIN departments d ON e.department_code = d.code 
                    WHERE e.is_active = TRUE 
                    ORDER BY e.full_name
                """)
                rows = cursor.fetchall()
                
                employees = []
                for row in rows:
                    emp_data = dict(row)
                    employees.append(Employee(**emp_data))
                
                return employees
        except Exception as e:
            logger.error(f"Ошибка получения сотрудников: {e}")
            return []
    
    async def get_employee_by_user_id(self, user_id: int) -> Optional[Employee]:
        """Получение сотрудника по Telegram user_id"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT e.*, d.name as department_name 
                    FROM employees e 
                    LEFT JOIN departments d ON e.department_code = d.code 
                    WHERE e.user_id = ? AND e.is_active = TRUE
                """, (user_id,))
                row = cursor.fetchone()
                
                if row:
                    return Employee(**dict(row))
                return None
        except Exception as e:
            logger.error(f"Ошибка получения сотрудника {user_id}: {e}")
            return None
    
    async def add_employee(self, employee: Employee) -> bool:
        """Добавление нового сотрудника"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO employees (user_id, username, full_name, department_code, position, employee_id, email, phone)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    employee.user_id, employee.username, employee.full_name,
                    employee.department_code, employee.position, employee.employee_id,
                    employee.email, employee.phone
                ))
                conn.commit()
                logger.info(f"Добавлен сотрудник: {employee.full_name}")
                return True
        except Exception as e:
            logger.error(f"Ошибка добавления сотрудника: {e}")
            return False
    
    async def update_employee(self, user_id: int, **kwargs) -> bool:
        """Обновление данных сотрудника"""
        try:
            if not kwargs:
                return False
            
            # Добавляем updated_at
            kwargs['updated_at'] = datetime.now()
            
            set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
            values = list(kwargs.values()) + [user_id]
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(f"""
                    UPDATE employees 
                    SET {set_clause}
                    WHERE user_id = ?
                """, values)
                conn.commit()
                
                if cursor.rowcount > 0:
                    logger.info(f"Обновлен сотрудник {user_id}")
                    return True
                return False
        except Exception as e:
            logger.error(f"Ошибка обновления сотрудника {user_id}: {e}")
            return False
    
    async def block_employee(self, user_id: int, blocked: bool = True) -> bool:
        """Блокировка/разблокировка сотрудника"""
        return await self.update_employee(user_id, is_blocked=blocked)
    
    # CRUD операции для отчетов
    async def save_report(self, report: WeeklyReport) -> bool:
        """Сохранение отчета"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Проверяем дедлайн для определения опоздания
                employee = await self.get_employee_by_user_id(report.user_id)
                is_late = False
                if employee:
                    dept = await self.get_department_by_code(employee.department_code)
                    if dept and dept.report_required:
                        # Логика определения опоздания (упрощенная)
                        current_time = datetime.now()
                        deadline_day = dept.report_deadline_day
                        deadline_hour = dept.report_deadline_hour
                        # Здесь можно добавить более сложную логику
                        is_late = current_time.weekday() > deadline_day or \
                                 (current_time.weekday() == deadline_day and current_time.hour > deadline_hour)
                
                cursor.execute("""
                    INSERT OR REPLACE INTO reports 
                    (user_id, username, full_name, week_start, week_end, completed_tasks, 
                     achievements, problems, next_week_plans, department, position, is_late)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    report.user_id, report.username, report.full_name,
                    report.week_start.date(), report.week_end.date(),
                    report.completed_tasks, report.achievements, report.problems,
                    report.next_week_plans, report.department, report.position, is_late
                ))
                conn.commit()
                logger.info(f"Сохранен отчет пользователя {report.user_id} за неделю {report.week_start.date()}")
                return True
        except Exception as e:
            logger.error(f"Ошибка сохранения отчета: {e}")
            return False
    
    async def get_reports_by_week(self, week_start: date, week_end: date) -> List[WeeklyReport]:
        """Получение отчетов за неделю"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM reports 
                    WHERE week_start = ? AND week_end = ?
                    ORDER BY submitted_at DESC
                """, (week_start, week_end))
                rows = cursor.fetchall()
                
                reports = []
                for row in rows:
                    report_data = dict(row)
                    # Преобразуем даты
                    report_data['week_start'] = datetime.fromisoformat(f"{report_data['week_start']}T00:00:00")
                    report_data['week_end'] = datetime.fromisoformat(f"{report_data['week_end']}T23:59:59")
                    reports.append(WeeklyReport(**report_data))
                
                return reports
        except Exception as e:
            logger.error(f"Ошибка получения отчетов за неделю: {e}")
            return []
    
    async def get_user_report(self, user_id: int, week_start: date) -> Optional[WeeklyReport]:
        """Получение отчета пользователя за конкретную неделю"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM reports 
                    WHERE user_id = ? AND week_start = ?
                """, (user_id, week_start))
                row = cursor.fetchone()
                
                if row:
                    report_data = dict(row)
                    # Преобразуем даты
                    report_data['week_start'] = datetime.fromisoformat(f"{report_data['week_start']}T00:00:00")
                    report_data['week_end'] = datetime.fromisoformat(f"{report_data['week_end']}T23:59:59")
                    return WeeklyReport(**report_data)
                return None
        except Exception as e:
            logger.error(f"Ошибка получения отчета пользователя {user_id}: {e}")
            return None
    
    # Статистические методы
    async def get_department_stats(self, department_code: str, week_start: date, week_end: date) -> Dict[str, Any]:
        """Получение статистики по отделу"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Общее количество сотрудников в отделе
                cursor.execute("""
                    SELECT COUNT(*) FROM employees 
                    WHERE department_code = ? AND is_active = TRUE
                """, (department_code,))
                total_employees = cursor.fetchone()[0]
                
                # Количество отправленных отчетов
                cursor.execute("""
                    SELECT COUNT(*) FROM reports r
                    JOIN employees e ON r.user_id = e.user_id
                    WHERE e.department_code = ? AND r.week_start = ?
                """, (department_code, week_start))
                submitted_reports = cursor.fetchone()[0]
                
                # Количество опоздавших
                cursor.execute("""
                    SELECT COUNT(*) FROM reports r
                    JOIN employees e ON r.user_id = e.user_id
                    WHERE e.department_code = ? AND r.week_start = ? AND r.is_late = TRUE
                """, (department_code, week_start))
                late_reports = cursor.fetchone()[0]
                
                return {
                    'department_code': department_code,
                    'total_employees': total_employees,
                    'submitted_reports': submitted_reports,
                    'missing_reports': total_employees - submitted_reports,
                    'late_reports': late_reports,
                    'completion_rate': (submitted_reports / total_employees * 100) if total_employees > 0 else 0
                }
        except Exception as e:
            logger.error(f"Ошибка получения статистики отдела {department_code}: {e}")
            return {}
    
    async def get_missing_reports_users(self, week_start: date) -> List[Employee]:
        """Получение списка сотрудников, не сдавших отчет"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT e.*, d.name as department_name 
                    FROM employees e
                    JOIN departments d ON e.department_code = d.code
                    LEFT JOIN reports r ON e.user_id = r.user_id AND r.week_start = ?
                    WHERE e.is_active = TRUE 
                      AND e.is_blocked = FALSE 
                      AND d.report_required = TRUE 
                      AND r.id IS NULL
                    ORDER BY e.department_code, e.full_name
                """, (week_start,))
                rows = cursor.fetchall()
                
                employees = []
                for row in rows:
                    emp_data = dict(row)
                    employees.append(Employee(**emp_data))
                
                return employees
        except Exception as e:
            logger.error(f"Ошибка получения списка не сдавших отчет: {e}")
            return []
    
    async def close(self):
        """Закрытие соединения с базой данных"""
        # SQLite автоматически закрывает соединения
        logger.info("База данных закрыта")

# Глобальный экземпляр менеджера базы данных
db_manager = DatabaseManager()