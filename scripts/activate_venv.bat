@echo off
echo ========================================
echo   Активация виртуального окружения
echo ========================================
echo.

REM Проверка существования venv
if not exist "venv\Scripts\activate.bat" (
    echo ❌ Виртуальное окружение не найдено
    echo Запустите scripts\setup_enhanced.bat для создания
    pause
    exit /b 1
)

REM Активация venv
echo ✅ Активация виртуального окружения...
call venv\Scripts\activate.bat

REM Проверка активации
echo ✅ Виртуальное окружение активировано
echo.
echo 📍 Текущий Python: 
python --version
echo.
echo 📦 Установленные пакеты:
pip list --format=columns
echo.
echo 🚀 Готово к работе!
echo.
echo Команды для запуска:
echo   python src\main.py     - Запуск бота
echo   scripts\run.bat        - Запуск с проверками
echo   scripts\check_system.bat - Диагностика
echo.
cmd /k