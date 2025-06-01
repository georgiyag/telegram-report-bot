# Установка и настройка

Подробное руководство по установке и настройке Telegram Report Bot.

## Системные требования

### Минимальные требования
- **Операционная система**: Windows 10+, Ubuntu 18.04+, macOS 10.14+
- **Python**: 3.8 или выше
- **RAM**: 512 MB
- **Дисковое пространство**: 100 MB
- **Интернет**: Стабильное подключение для работы с Telegram API

### Рекомендуемые требования
- **Python**: 3.11+
- **RAM**: 1 GB
- **Дисковое пространство**: 500 MB
- **Ollama**: Для ИИ-анализа отчетов (опционально)

## Автоматическая установка

### Windows

1. Откройте PowerShell или Command Prompt
2. Перейдите в директорию проекта:
   ```cmd
   cd path\to\telegram_report_bot
   ```
3. Запустите скрипт установки:
   ```cmd
   scripts\setup.bat
   ```

### Linux/macOS

1. Откройте терминал
2. Перейдите в директорию проекта:
   ```bash
   cd /path/to/telegram_report_bot
   ```
3. Сделайте скрипт исполняемым и запустите:
   ```bash
   chmod +x scripts/setup.sh
   ./scripts/setup.sh
   ```

## Ручная установка

### Шаг 1: Проверка Python

Убедитесь, что у вас установлен Python 3.8 или выше:

```bash
python --version
# или
python3 --version
```

Если Python не установлен, скачайте его с [официального сайта](https://www.python.org/downloads/).

### Шаг 2: Создание виртуального окружения

```bash
# Создание виртуального окружения
python -m venv venv

# Активация (Windows)
venv\Scripts\activate

# Активация (Linux/macOS)
source venv/bin/activate
```

### Шаг 3: Установка зависимостей

```bash
# Обновление pip
pip install --upgrade pip

# Установка основных зависимостей
pip install -r requirements.txt

# Установка зависимостей для разработки (опционально)
pip install -r requirements-dev.txt
```

### Шаг 4: Настройка конфигурации

1. Скопируйте файл примера конфигурации:
   ```bash
   cp .env.example .env
   ```

2. Отредактируйте файл `.env` и заполните необходимые переменные:
   ```env
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   GROUP_CHAT_ID=your_group_chat_id
   ADMIN_USER_IDS=123456789,987654321
   ```

## Получение необходимых данных

### Telegram Bot Token

1. Найдите [@BotFather](https://t.me/botfather) в Telegram
2. Отправьте команду `/newbot`
3. Следуйте инструкциям для создания бота
4. Скопируйте полученный токен

### Group Chat ID

1. Добавьте вашего бота в группу
2. Найдите [@userinfobot](https://t.me/userinfobot) в Telegram
3. Добавьте его в ту же группу
4. Отправьте любое сообщение в группу
5. Бот покажет ID группы

### User ID администраторов

1. Найдите [@userinfobot](https://t.me/userinfobot) в Telegram
2. Отправьте ему любое сообщение
3. Скопируйте ваш User ID
4. Повторите для всех администраторов

## Настройка Ollama (опционально)

Для использования ИИ-анализа отчетов:

### Установка Ollama

1. Скачайте Ollama с [официального сайта](https://ollama.ai/)
2. Установите согласно инструкциям для вашей ОС
3. Запустите Ollama:
   ```bash
   ollama serve
   ```

### Загрузка модели

```bash
# Загрузка рекомендуемой модели
ollama pull llama3.1

# Или другой модели по выбору
ollama pull mistral
```

### Настройка в .env

```env
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1
```

## Проверка установки

### Тест конфигурации

```bash
# Активируйте виртуальное окружение
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Проверьте конфигурацию
python -c "from src.config import settings; print('✅ Конфигурация загружена успешно')"
```

### Тест подключения к Telegram

```bash
# Запустите бота в тестовом режиме
python src/main.py --test
```

### Запуск тестов

```bash
# Запуск всех тестов
pytest

# Запуск с покрытием
pytest --cov=src
```

## Устранение проблем

### Проблемы с Python

**Ошибка**: `python: command not found`

**Решение**: 
- Windows: Переустановите Python с галочкой "Add to PATH"
- Linux: `sudo apt install python3 python3-pip`
- macOS: `brew install python3`

### Проблемы с зависимостями

**Ошибка**: `pip install failed`

**Решение**:
```bash
# Обновите pip
python -m pip install --upgrade pip

# Очистите кэш
pip cache purge

# Переустановите зависимости
pip install -r requirements.txt --force-reinstall
```

### Проблемы с виртуальным окружением

**Ошибка**: `venv activation failed`

**Решение**:
```bash
# Удалите старое окружение
rm -rf venv  # Linux/macOS
rmdir /s venv  # Windows

# Создайте новое
python -m venv venv
```

### Проблемы с Telegram API

**Ошибка**: `Unauthorized`

**Решение**:
- Проверьте правильность Bot Token
- Убедитесь, что бот не заблокирован
- Проверьте права бота в группе

**Ошибка**: `Chat not found`

**Решение**:
- Проверьте правильность Group Chat ID
- Убедитесь, что бот добавлен в группу
- Проверьте права бота на отправку сообщений

### Проблемы с Ollama

**Ошибка**: `Connection refused`

**Решение**:
- Убедитесь, что Ollama запущен: `ollama serve`
- Проверьте URL в конфигурации
- Проверьте доступность порта 11434

## Обновление

### Обновление зависимостей

```bash
# Активируйте виртуальное окружение
source venv/bin/activate

# Обновите зависимости
pip install -r requirements.txt --upgrade
```

### Обновление кода

```bash
# Получите последние изменения
git pull origin main

# Обновите зависимости
pip install -r requirements.txt --upgrade

# Перезапустите бота
```

## Следующие шаги

После успешной установки:

1. Прочитайте [руководство пользователя](USER_GUIDE.md)
2. Ознакомьтесь с [API документацией](API.md)
3. Изучите [примеры использования](EXAMPLES.md)
4. Настройте [мониторинг и логирование](MONITORING.md)