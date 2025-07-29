import sqlite3
import sys
from pathlib import Path

# Добавляем путь к src для импорта
sys.path.append('src')

from database import DatabaseManager

def check_departments():
    """Проверка отделов в базе данных"""
    try:
        # Создаем менеджер базы данных
        db = DatabaseManager()
        
        # Подключаемся к базе напрямую для проверки
        with sqlite3.connect(db.db_path) as conn:
            cursor = conn.cursor()
            
            # Проверяем количество отделов
            cursor.execute("SELECT COUNT(*) FROM departments")
            total_count = cursor.fetchone()[0]
            print(f"Всего отделов в базе: {total_count}")
            
            # Проверяем активные отделы
            cursor.execute("SELECT COUNT(*) FROM departments WHERE is_active = 1")
            active_count = cursor.fetchone()[0]
            print(f"Активных отделов: {active_count}")
            
            # Показываем все отделы
            cursor.execute("SELECT name, code, is_active FROM departments ORDER BY name")
            departments = cursor.fetchall()
            
            print("\nСписок отделов:")
            for name, code, is_active in departments:
                status = "Активен" if is_active else "Неактивен"
                print(f"  {name} ({code}) - {status}")
                
    except Exception as e:
        print(f"Ошибка при проверке базы данных: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_departments()