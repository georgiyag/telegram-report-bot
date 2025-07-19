@echo off
chcp 65001 >nul
echo ========================================
echo   Диагностика системы
echo ========================================
echo.

echo 🔍 Проверка системных требований...
echo.

REM Проверка Python
echo [1/8] Python:
python --version 2>nul
if errorlevel 1 (
    echo ❌ Python не найден
    echo Установите Python 3.8+ с https://python.org
) else (
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
    echo ✅ Python %PYTHON_VERSION%
)

REM Проверка pip
echo.
echo [2/8] pip:
pip --version 2>nul
if errorlevel 1 (
    echo ❌ pip не найден
) else (
    echo ✅ pip доступен
)

REM Проверка структуры проекта
echo.
echo [3/8] Структура проекта:
if exist "src\main.py" (
    echo ✅ src\main.py найден
) else (
    echo ❌ src\main.py не найден
)

if exist "requirements.txt" (
    echo ✅ requirements.txt найден
) else (
    echo ❌ requirements.txt не найден
)

if exist ".env.example" (
    echo ✅ .env.example найден
) else (
    echo ❌ .env.example не найден
)

REM Проверка виртуального окружения
echo.
echo [4/8] Виртуальное окружение:
if exist "venv\Scripts\activate.bat" (
    echo ✅ Виртуальное окружение создано
) else (
    echo ❌ Виртуальное окружение не найдено
)

REM Проверка .env файла
echo.
echo [5/8] Конфигурация:
if exist ".env" (
    echo ✅ Файл .env существует
    
    findstr /C:"TELEGRAM_BOT_TOKEN=your_bot_token_here" .env >nul
    if not errorlevel 1 (
        echo ⚠️  TELEGRAM_BOT_TOKEN не настроен
    ) else (
        echo ✅ TELEGRAM_BOT_TOKEN настроен
    )
    
    findstr /C:"GROUP_CHAT_ID=your_group_chat_id" .env >nul
    if not errorlevel 1 (
        echo ⚠️  GROUP_CHAT_ID не настроен
    ) else (
        echo ✅ GROUP_CHAT_ID настроен
    )
) else (
    echo ❌ Файл .env не найден
)

REM Проверка зависимостей
echo.
echo [6/8] Зависимости Python:
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    
    python -c "import telegram" 2>nul
    if errorlevel 1 (
        echo ❌ python-telegram-bot не установлен
    ) else (
        echo ✅ python-telegram-bot установлен
    )
    
    python -c "import aiosqlite" 2>nul
    if errorlevel 1 (
        echo ❌ aiosqlite не установлен
    ) else (
        echo ✅ aiosqlite установлен
    )
    
    python -c "import aiofiles" 2>nul
    if errorlevel 1 (
        echo ❌ aiofiles не установлен
    ) else (
        echo ✅ aiofiles установлен
    )
) else (
    echo ⚠️  Виртуальное окружение не найдено, пропускаем проверку
)

REM Проверка папок
echo.
echo [7/8] Папки проекта:
if exist "data" (
    echo ✅ Папка data существует
) else (
    echo ⚠️  Папка data не найдена (будет создана автоматически)
)

if exist "logs" (
    echo ✅ Папка logs существует
) else (
    echo ⚠️  Папка logs не найдена (будет создана автоматически)
)

REM Проверка прав доступа
echo.
echo [8/8] Права доступа:
echo test > test_write.tmp 2>nul
if exist "test_write.tmp" (
    del test_write.tmp
    echo ✅ Права на запись есть
) else (
    echo ❌ Нет прав на запись в текущую папку
)

echo.
echo ========================================
echo   Рекомендации:
echo ========================================

if not exist "venv\Scripts\activate.bat" (
    echo 🔧 Запустите: scripts\setup_enhanced.bat
)

if not exist ".env" (
    echo 🔧 Создайте файл .env из .env.example
)

findstr /C:"TELEGRAM_BOT_TOKEN=your_bot_token_here" .env >nul 2>nul
if not errorlevel 1 (
    echo 🔧 Настройте TELEGRAM_BOT_TOKEN в .env
)

echo.
echo 📖 Подробная инструкция: DEPLOYMENT_GUIDE.md
echo.
pause