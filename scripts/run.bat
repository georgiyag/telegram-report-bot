@echo off
chcp 65001 >nul
echo ========================================
echo   Запуск Telegram Report Bot
echo ========================================
echo.

REM Проверка виртуального окружения
if not exist "venv\Scripts\activate.bat" (
    echo ❌ Виртуальное окружение не найдено
    echo Запустите сначала scripts\setup_enhanced.bat
    pause
    exit /b 1
)

REM Активация виртуального окружения
echo [1/4] Активация виртуального окружения...
call venv\Scripts\activate.bat
echo ✅ Виртуальное окружение активировано

REM Проверка .env файла
echo.
echo [2/4] Проверка конфигурации...
if not exist ".env" (
    echo ❌ Файл .env не найден
    echo Создайте файл .env и заполните необходимые переменные
    pause
    exit /b 1
)

REM Проверка основных переменных
findstr /C:"TELEGRAM_BOT_TOKEN=your_bot_token_here" .env >nul
if not errorlevel 1 (
    echo ❌ Не настроен TELEGRAM_BOT_TOKEN в файле .env
    echo Получите токен у @BotFather и обновите .env
    pause
    exit /b 1
)

findstr /C:"GROUP_CHAT_ID=your_group_chat_id" .env >nul
if not errorlevel 1 (
    echo ❌ Не настроен GROUP_CHAT_ID в файле .env
    echo Укажите ID вашей группы в .env
    pause
    exit /b 1
)

echo ✅ Конфигурация проверена

REM Проверка зависимостей
echo.
echo [3/4] Проверка зависимостей...
python -c "import telegram, asyncio, aiofiles, aiosqlite" 2>nul
if errorlevel 1 (
    echo ❌ Не все зависимости установлены
    echo Запустите scripts\setup_enhanced.bat для установки
    pause
    exit /b 1
)
echo ✅ Зависимости проверены

REM Создание папки для данных
if not exist "data" (
    mkdir data
    echo ✅ Создана папка data
)

REM Запуск бота
echo.
echo [4/4] Запуск бота...
echo ========================================
echo   🤖 Бот запускается...
echo   Нажмите Ctrl+C для остановки
echo ========================================
echo.

python src\main.py

echo.
echo ========================================
echo   Бот остановлен
echo ========================================
pause