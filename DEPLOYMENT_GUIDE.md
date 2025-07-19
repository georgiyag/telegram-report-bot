# 🚀 Руководство по развертыванию на новой машине

## Предварительные требования

- Python 3.8 или выше
- Git (для клонирования репозитория)
- Telegram Bot Token
- Доступ к интернету

## 📋 Пошаговая инструкция

### Шаг 1: Подготовка проекта

1. **Скопируйте проект на новую машину:**
   ```bash
   # Вариант 1: Через Git (если проект в репозитории)
   git clone <your-repository-url>
   cd rezume_selma_bot
   
   # Вариант 2: Скопируйте папку проекта напрямую
   # Убедитесь, что скопировали ВСЕ файлы, включая скрытые (.env.example, .gitignore)
   ```

2. **Перейдите в папку проекта:**
   ```bash
   cd rezume_selma_bot
   ```

### Шаг 2: Настройка Python окружения

1. **Проверьте версию Python:**
   ```bash
   python --version
   # Должно быть 3.8 или выше
   ```

2. **Создайте виртуальное окружение:**
   ```bash
   python -m venv venv
   ```

3. **Активируйте виртуальное окружение:**
   ```bash
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

4. **Обновите pip:**
   ```bash
   python -m pip install --upgrade pip
   ```

5. **Установите зависимости:**
   ```bash
   pip install -r requirements.txt
   ```

### Шаг 3: Настройка конфигурации

1. **Создайте файл .env:**
   ```bash
   # Windows
   copy .env.example .env
   
   # Linux/Mac
   cp .env.example .env
   ```

2. **Отредактируйте файл .env:**
   Откройте файл `.env` в любом текстовом редакторе и заполните:
   
   ```env
   # ОБЯЗАТЕЛЬНО ЗАПОЛНИТЬ:
   TELEGRAM_BOT_TOKEN=ваш_токен_бота_здесь
   GROUP_CHAT_ID=ваш_id_группы
   ADMIN_USER_IDS=ваш_telegram_id
   
   # ОПЦИОНАЛЬНО (можно оставить как есть):
   OLLAMA_URL=http://localhost:11434
   OLLAMA_MODEL=gemma3:4b
   DEBUG=False
   LOG_LEVEL=INFO
   TIMEZONE=Europe/Moscow
   DATABASE_URL=sqlite:///reports.db
   ```

### Шаг 4: Получение необходимых ID

1. **Bot Token:**
   - Перейдите к [@BotFather](https://t.me/botfather)
   - Создайте нового бота командой `/newbot`
   - Скопируйте полученный токен

2. **Group Chat ID:**
   - Добавьте бота в вашу группу
   - Отправьте сообщение в группу
   - Перейдите к `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
   - Найдите `chat.id` в ответе

3. **Your User ID:**
   - Напишите [@userinfobot](https://t.me/userinfobot)
   - Скопируйте ваш ID

### Шаг 5: Создание структуры данных

1. **Создайте папку для данных:**
   ```bash
   mkdir data
   ```

2. **Проверьте структуру проекта:**
   ```
   rezume_selma_bot/
   ├── .env                 # ✅ Должен существовать
   ├── requirements.txt     # ✅ Должен существовать
   ├── src/                 # ✅ Должна существовать
   ├── data/                # ✅ Создали на предыдущем шаге
   └── venv/                # ✅ Создали ранее
   ```

### Шаг 6: Запуск проекта

1. **Убедитесь, что виртуальное окружение активно:**
   ```bash
   # Должно показать путь к venv
   which python  # Linux/Mac
   where python  # Windows
   ```

2. **Запустите бота:**
   ```bash
   python src/main.py
   ```

3. **Проверьте логи:**
   Если все настроено правильно, вы увидите:
   ```
   INFO - Инициализация сервисов...
   INFO - База данных инициализирована
   SUCCESS - Все сервисы успешно инициализированы
   INFO - Бот запущен и готов к работе
   ```

## 🔧 Автоматическая установка

Для упрощения процесса используйте готовые скрипты:

### Windows:
```batch
scripts\setup.bat
scripts\run.bat
```

### Linux/Mac:
```bash
chmod +x scripts/setup.sh scripts/run.sh
./scripts/setup.sh
./scripts/run.sh
```

## ❌ Частые проблемы и решения

### Проблема: "ModuleNotFoundError"
**Решение:** Убедитесь, что виртуальное окружение активировано и зависимости установлены:
```bash
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### Проблема: "Unauthorized" при запуске бота
**Решение:** Проверьте правильность `TELEGRAM_BOT_TOKEN` в файле `.env`

### Проблема: База данных не создается
**Решение:** Убедитесь, что папка `data/` существует и у приложения есть права на запись

### Проблема: "Permission denied" на Linux/Mac
**Решение:** Дайте права на выполнение скриптам:
```bash
chmod +x scripts/*.sh
```

## 🧪 Проверка работоспособности

1. **Отправьте команду `/start` боту в Telegram**
2. **Проверьте, что бот отвечает**
3. **Попробуйте команду `/admin` (если вы администратор)**

## 📞 Поддержка

Если возникли проблемы:
1. Проверьте логи в консоли
2. Убедитесь, что все переменные в `.env` заполнены правильно
3. Проверьте, что бот добавлен в группу и имеет права администратора