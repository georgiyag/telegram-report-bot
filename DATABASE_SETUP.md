# База данных для Telegram бота управления отчетами

## Обзор

Бот использует SQLite базу данных для хранения информации о:
- 📁 **Отделах** (departments)
- 👤 **Сотрудниках** (employees) 
- 📊 **Еженедельных отчетах** (reports)

## Структура базы данных

### Таблица `departments`
```sql
CREATE TABLE departments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    code TEXT NOT NULL UNIQUE,
    description TEXT,
    head_name TEXT,
    report_required BOOLEAN DEFAULT TRUE,
    report_deadline_day INTEGER DEFAULT 5,
    report_deadline_hour INTEGER DEFAULT 18,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Таблица `employees`
```sql
CREATE TABLE employees (
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
);
```

### Таблица `reports`
```sql
CREATE TABLE reports (
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
);
```

## Текущее состояние базы данных

### ✅ База данных создана и инициализирована
- 📍 Расположение: `src/data/bot_database.db`
- 🔧 Автоматическая инициализация при первом запуске
- 📊 Тестовые данные добавлены

### 📁 Отделы (4 шт.)
1. **IT отдел** (`IT`) - Руководитель: Петров Петр Петрович
2. **Бухгалтерия** (`ACCOUNTING`) - Руководитель: Сидорова Анна Ивановна
3. **Производство** (`PRODUCTION`) - Руководитель: Козлов Сергей Александрович
4. **Управление** (`MANAGEMENT`) - Руководитель: Директор Иван Иванович

### 👤 Сотрудники (4 чел.)
1. **Петрова Мария Сергеевна** - Разработчик (IT отдел)
   - Telegram ID: 111222333
   - Email: maria.petrova@company.com

2. **Сидоров Иван Петрович** - Бухгалтер (Бухгалтерия)
   - Telegram ID: 444555666
   - Email: ivan.sidorov@company.com

3. **Козлова Анна Александровна** - Инженер (Производство)
   - Telegram ID: 777888999
   - Email: anna.kozlova@company.com

4. **Козлов Сергей Александрович** - Менеджер (Управление)
   - Telegram ID: 555666777
   - Email: sergey.kozlov@company.com

### 📊 Отчеты (4 шт.)
- Все сотрудники имеют отчеты за неделю 26.05 - 01.06.2025
- 1 отчет помечен как опоздавший (Сидоров И.П.)
- Дополнительный тестовый отчет для Петровой М.С.

## Основные методы DatabaseManager

### Работа с отделами
```python
# Получить все отделы
departments = await db_manager.get_departments()

# Получить отдел по коду
dept = await db_manager.get_department_by_code("IT")
```

### Работа с сотрудниками
```python
# Получить всех сотрудников
employees = await db_manager.get_employees()

# Получить сотрудника по Telegram ID
employee = await db_manager.get_employee_by_user_id(111222333)

# Добавить нового сотрудника
success = await db_manager.add_employee(employee_obj)
```

### Работа с отчетами
```python
# Сохранить отчет
success = await db_manager.save_report(report_obj)

# Получить отчеты пользователя
reports = await db_manager.get_user_reports(user_id, limit=10)

# Получить отчет за конкретную неделю
report = await db_manager.get_user_report(user_id, week_start)

# Получить отчеты за неделю
week_reports = await db_manager.get_reports_by_week(week_start, week_end)
```

## Тестирование

### Доступные скрипты

1. **`check_db.py`** - Проверка содержимого базы данных
   ```bash
   python check_db.py
   ```

2. **`add_test_employees_sync.py`** - Добавление тестовых сотрудников
   ```bash
   python add_test_employees_sync.py
   ```

3. **`add_test_reports_sync.py`** - Добавление тестовых отчетов
   ```bash
   python add_test_reports_sync.py
   ```

4. **`test_bot_functionality.py`** - Полное тестирование функционала
   ```bash
   python test_bot_functionality.py
   ```

## Следующие шаги

### ✅ Выполнено
- [x] Создание структуры базы данных
- [x] Инициализация с тестовыми данными
- [x] Реализация основных CRUD операций
- [x] Тестирование функционала

### 🔄 Готово к использованию
- [x] База данных полностью настроена
- [x] Тестовые данные добавлены
- [x] Все методы работают корректно
- [x] Бот готов к запуску с базой данных

### 🚀 Рекомендации для продакшена
1. **Бэкапы**: Настроить регулярное резервное копирование
2. **Мониторинг**: Добавить логирование операций с БД
3. **Оптимизация**: При росте данных рассмотреть PostgreSQL
4. **Безопасность**: Добавить валидацию входных данных

## Заключение

🎉 **База данных полностью готова к работе!**

Все необходимые таблицы созданы, тестовые данные добавлены, и функционал протестирован. Бот может начать работу с пользователями и обрабатывать их отчеты.