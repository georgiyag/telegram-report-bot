# Telegram Report Bot

**Автоматизированная система обработки еженедельных отчетов сотрудников**  
*АО ЭМЗ "ФИРМА СЭЛМА"*

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Telegram Bot API](https://img.shields.io/badge/Telegram%20Bot%20API-21.3-blue.svg)](https://python-telegram-bot.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## 📋 Описание

Telegram Report Bot - это полнофункциональный бот для автоматизации процесса сбора, обработки и анализа еженедельных отчетов сотрудников предприятия. Бот интегрируется с ИИ-сервисом Ollama для интеллектуального анализа отчетов и предоставляет удобный интерфейс для администраторов.

## ✨ Основные возможности

### Для сотрудников:
- 📝 Создание еженедельных отчетов через интуитивный диалоговый интерфейс
- ✅ Валидация данных отчета в реальном времени
- 📊 Просмотр статуса своих отчетов
- 🔔 Автоматические напоминания о необходимости подачи отчета
- 📱 Удобная мобильная клавиатура для быстрого ввода

### Для администраторов:
- 👥 Управление пользователями и отделами
- 📈 Детальная статистика по отчетам
- 🤖 ИИ-анализ отчетов с помощью Ollama
- 📤 Экспорт данных в различных форматах
- 🔔 Массовая рассылка напоминаний
- 📋 Еженедельные сводки по всем отделам

### Технические особенности:
- 🔄 Асинхронная обработка запросов
- 🛡️ Валидация и санитизация пользовательского ввода
- 📝 Подробное логирование всех операций
- 🔧 Гибкая система конфигурации
- 🧪 Полное покрытие тестами
- 🐳 Готовность к контейнеризации

## 🚀 Быстрый старт

### Предварительные требования

- Python 3.8 или выше
- Telegram Bot Token (получить у [@BotFather](https://t.me/botfather))
- Ollama (опционально, для ИИ-анализа)

### Автоматическая установка

#### Windows
```batch
# Клонируйте репозиторий
git clone <repository-url>
cd telegram_report_bot

# Запустите скрипт установки
scripts\setup.bat
```

#### Linux/Mac
```bash
# Клонируйте репозиторий
git clone <repository-url>
cd telegram_report_bot

# Сделайте скрипт исполняемым и запустите
chmod +x scripts/setup.sh
./scripts/setup.sh
```

### Ручная установка

1. **Создание виртуального окружения:**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

2. **Установка зависимостей:**
```bash
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt  # для разработки
```

3. **Настройка окружения:**
```bash
cp .env.example .env
# Отредактируйте .env файл, заполнив необходимые переменные
```

## ⚙️ Конфигурация

### Обязательные переменные окружения

Создайте файл `.env` на основе `.env.example` и заполните следующие переменные:

```env
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here
GROUP_CHAT_ID=your_group_chat_id
THREAD_ID=your_thread_id  # опционально

# Admin Settings
ADMIN_USER_IDS=123456789,987654321

# Ollama Configuration (опционально)
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1

# Application Settings
DEBUG=False
LOG_LEVEL=INFO
TIMEZONE=Europe/Moscow
```

### Получение необходимых ID

1. **Bot Token**: Создайте бота у [@BotFather](https://t.me/botfather)
2. **Group Chat ID**: Добавьте бота в группу и используйте [@userinfobot](https://t.me/userinfobot)
3. **User ID**: Отправьте сообщение [@userinfobot](https://t.me/userinfobot)

## 🏃‍♂️ Запуск

### Простой запуск
```bash
# Windows
scripts\run.bat

# Linux/Mac
./scripts/run.sh

# Или напрямую
python src/main.py
```

### Запуск в режиме разработки
```bash
# Активируйте виртуальное окружение
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Установите переменную DEBUG
export DEBUG=True  # Linux/Mac
set DEBUG=True     # Windows

# Запустите бота
python src/main.py
```

## 📖 Использование

### Команды для пользователей

- `/start` - Начать работу с ботом
- `/help` - Показать справку
- `/report` - Создать новый отчет
- `/status` - Проверить статус отчетов

### Команды для администраторов

- `/admin` - Открыть панель администратора
- `/stats` - Показать статистику

### Процесс создания отчета

1. Отправьте команду `/report`
2. Следуйте инструкциям бота:
   - Опишите выполненные задачи
   - Укажите достижения
   - Опишите проблемы (опционально)
   - Составьте планы на следующую неделю
3. Подтвердите отчет
4. Получите уведомление об успешной отправке

## 🏗️ Архитектура проекта

```
src/
├── main.py              # Точка входа приложения
├── config.py            # Конфигурация
├── handlers/            # Обработчики команд
│   ├── report_handler.py
│   ├── admin_handler.py
│   └── states.py
├── services/            # Бизнес-логика
│   ├── ollama_service.py
│   ├── telegram_service.py
│   └── report_processor.py
├── models/              # Модели данных
│   ├── report.py
│   └── department.py
└── utils/               # Вспомогательные функции
    ├── date_utils.py
    ├── text_utils.py
    └── validators.py
```

### Основные компоненты

- **ReportHandler**: Обработка создания отчетов
- **AdminHandler**: Административные функции
- **ReportProcessor**: Бизнес-логика обработки отчетов
- **OllamaService**: Интеграция с ИИ для анализа
- **TelegramService**: Взаимодействие с Telegram API

## 🧪 Тестирование

### Запуск тестов
```bash
# Все тесты
pytest

# С покрытием
pytest --cov=src

# Конкретный файл
pytest tests/test_handlers.py

# С подробным выводом
pytest -v
```

### Структура тестов
- `tests/test_handlers.py` - Тесты обработчиков
- `tests/test_services.py` - Тесты сервисов
- `tests/test_models.py` - Тесты моделей (планируется)

## 🔧 Разработка

### Настройка среды разработки

1. Установите зависимости для разработки:
```bash
pip install -r requirements-dev.txt
```

2. Настройте pre-commit хуки:
```bash
pre-commit install
```

3. Запустите линтеры:
```bash
# Форматирование кода
black src/

# Проверка стиля
flake8 src/

# Проверка типов
mypy src/
```

### Добавление новых функций

1. Создайте ветку для новой функции
2. Добавьте тесты для новой функциональности
3. Реализуйте функцию
4. Убедитесь, что все тесты проходят
5. Создайте Pull Request

## 📊 Мониторинг и логирование

### Логи

Бот создает подробные логи всех операций:
- Консольный вывод с цветовой индикацией
- Файловые логи с ротацией (в продакшене)
- Различные уровни логирования (DEBUG, INFO, WARNING, ERROR)

### Метрики

- Количество обработанных отчетов
- Статистика по пользователям
- Время обработки запросов
- Ошибки и исключения

## 🔒 Безопасность

- Валидация всех пользовательских данных
- Санитизация HTML и Markdown
- Ограничение доступа к административным функциям
- Безопасное хранение токенов и ключей
- Логирование всех административных действий

## 🚀 Развертывание

### Локальное развертывание

Используйте предоставленные скрипты `setup.bat` (Windows) или `setup.sh` (Linux/Mac).

### Docker (планируется)

```dockerfile
# Dockerfile будет добавлен в следующих версиях
```

### Systemd сервис (Linux)

```ini
[Unit]
Description=Telegram Report Bot
After=network.target

[Service]
Type=simple
User=telegram-bot
WorkingDirectory=/path/to/telegram_report_bot
Environment=PATH=/path/to/telegram_report_bot/venv/bin
ExecStart=/path/to/telegram_report_bot/venv/bin/python src/main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

## 🤝 Участие в разработке

Мы приветствуем участие в развитии проекта!

1. Форкните репозиторий
2. Создайте ветку для новой функции (`git checkout -b feature/amazing-feature`)
3. Зафиксируйте изменения (`git commit -m 'Add amazing feature'`)
4. Отправьте в ветку (`git push origin feature/amazing-feature`)
5. Создайте Pull Request

### Правила участия

- Следуйте стилю кода проекта
- Добавляйте тесты для новой функциональности
- Обновляйте документацию при необходимости
- Используйте осмысленные сообщения коммитов

## 📝 Changelog

### v1.0.0 (2024-01-XX)
- ✨ Первый релиз
- 📝 Система создания отчетов
- 👥 Административная панель
- 🤖 Интеграция с Ollama
- 🧪 Полное покрытие тестами

## 🐛 Известные проблемы

- Ollama интеграция требует локальной установки сервиса
- Большие отчеты могут превышать лимиты Telegram API

## 📞 Поддержка

Если у вас возникли вопросы или проблемы:

1. Проверьте [документацию](docs/)
2. Посмотрите [известные проблемы](#-известные-проблемы)
3. Создайте [Issue](../../issues) в репозитории
4. Обратитесь к администраторам системы

## 📄 Лицензия

Этот проект распространяется под лицензией MIT. См. файл [LICENSE](LICENSE) для подробностей.

## 🙏 Благодарности

- [python-telegram-bot](https://python-telegram-bot.org/) - отличная библиотека для работы с Telegram Bot API
- [Ollama](https://ollama.ai/) - локальные языковые модели
- [Pydantic](https://pydantic-docs.helpmanual.io/) - валидация данных
- [Loguru](https://loguru.readthedocs.io/) - удобное логирование

---

**АО ЭМЗ "ФИРМА СЭЛМА"** © 2024

*Сделано с ❤️ для автоматизации рабочих процессов*