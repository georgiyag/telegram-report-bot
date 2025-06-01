@echo off
echo Запуск Telegram Report Bot...

REM Проверка существования виртуального окружения
if not exist "venv\Scripts\activate.bat" (
    echo Ошибка: Виртуальное окружение не найдено!
    echo Пожалуйста, сначала запустите setup.bat
    pause
    exit /b 1
)

REM Активация виртуального окружения
echo Активация виртуального окружения...
call venv\Scripts\activate.bat

REM Проверка существования .env файла
if not exist ".env" (
    echo Ошибка: Файл .env не найден!
    echo Пожалуйста, создайте .env файл на основе .env.example
    echo и заполните необходимые переменные.
    pause
    exit /b 1
)

REM Создание директории для логов
if not exist "logs" (
    mkdir logs
)

REM Запуск бота
echo Запуск бота...
python src\main.py

REM Если бот завершился с ошибкой
if errorlevel 1 (
    echo.
    echo Бот завершился с ошибкой!
    echo Проверьте логи для получения подробной информации.
    pause
)

echo.
echo Бот завершил работу.
pause