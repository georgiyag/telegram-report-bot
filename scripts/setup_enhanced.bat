@echo off
chcp 65001 >nul
echo ========================================
echo   Установка Telegram Report Bot
echo ========================================
echo.

REM Проверка версии Python
echo [1/7] Проверка Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Ошибка: Python 3.8+ не найден
    echo Пожалуйста, установите Python с https://python.org
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✅ Python %PYTHON_VERSION% найден

REM Проверка существования requirements.txt
echo.
echo [2/7] Проверка файлов проекта...
if not exist "requirements.txt" (
    echo ❌ Файл requirements.txt не найден
    echo Убедитесь, что вы находитесь в корневой папке проекта
    pause
    exit /b 1
)
echo ✅ Файлы проекта найдены

REM Создание виртуального окружения
echo.
echo [3/7] Создание виртуального окружения...
if exist "venv" (
    echo ⚠️  Виртуальное окружение уже существует
    set /p RECREATE="Пересоздать? (y/N): "
    if /i "%RECREATE%"=="y" (
        rmdir /s /q venv
        python -m venv venv
        echo ✅ Виртуальное окружение пересоздано
    ) else (
        echo ✅ Используем существующее окружение
    )
) else (
    python -m venv venv
    echo ✅ Виртуальное окружение создано
)

REM Активация виртуального окружения
echo.
echo [4/7] Активация виртуального окружения...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ❌ Не удалось активировать виртуальное окружение
    pause
    exit /b 1
)
echo ✅ Виртуальное окружение активировано

REM Обновление pip
echo.
echo [5/7] Обновление pip...
python -m pip install --upgrade pip --quiet
echo ✅ pip обновлен

REM Установка зависимостей
echo.
echo [6/7] Установка зависимостей...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo ❌ Ошибка при установке зависимостей
    pause
    exit /b 1
)
echo ✅ Основные зависимости установлены

if exist "requirements-dev.txt" (
    pip install -r requirements-dev.txt --quiet
    echo ✅ Зависимости для разработки установлены
)

REM Создание .env файла
echo.
echo [7/7] Настройка конфигурации...
if not exist ".env" (
    if exist ".env.example" (
        copy .env.example .env >nul
        echo ✅ Создан файл .env из шаблона
    ) else (
        echo # Telegram Bot Configuration > .env
        echo TELEGRAM_BOT_TOKEN=your_bot_token_here >> .env
        echo GROUP_CHAT_ID=your_group_chat_id >> .env
        echo ADMIN_USER_IDS=your_telegram_id >> .env
        echo. >> .env
        echo # Application Settings >> .env
        echo DEBUG=False >> .env
        echo LOG_LEVEL=INFO >> .env
        echo TIMEZONE=Europe/Moscow >> .env
        echo ✅ Создан базовый файл .env
    )
) else (
    echo ✅ Файл .env уже существует
)

REM Создание папки для данных
if not exist "data" (
    mkdir data
    echo ✅ Создана папка data
)

echo.
echo ========================================
echo   Установка завершена успешно! 🎉
echo ========================================
echo.
echo 📝 ВАЖНО: Отредактируйте файл .env и заполните:
echo    - TELEGRAM_BOT_TOKEN (получите у @BotFather)
echo    - GROUP_CHAT_ID (ID вашей группы)
echo    - ADMIN_USER_IDS (ваш Telegram ID)
echo.
echo 🚀 Для запуска бота:
echo    1. Активируйте окружение: venv\Scripts\activate.bat
echo    2. Запустите бота: python src\main.py
echo    3. Или используйте: scripts\run.bat
echo.
echo 📖 Подробная инструкция: DEPLOYMENT_GUIDE.md
echo.
pause