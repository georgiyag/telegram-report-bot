@echo off
echo Настройка проекта Telegram Report Bot...

REM Проверка версии Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Ошибка: Python 3.8+ не найден
    pause
    exit /b 1
)

REM Создание виртуального окружения
echo Создание виртуального окружения...
python -m venv venv

REM Активация виртуального окружения
echo Активация виртуального окружения...
call venv\Scripts\activate.bat

REM Обновление pip
echo Обновление pip...
python -m pip install --upgrade pip

REM Установка зависимостей
echo Установка зависимостей...
pip install -r requirements.txt
pip install -r requirements-dev.txt

REM Создание .env файла из примера
if not exist .env (
    copy .env.example .env
    echo Создан файл .env. Пожалуйста, заполните необходимые переменные.
)

echo Установка завершена успешно!
echo Для активации окружения используйте: venv\Scripts\activate.bat
echo Для запуска бота: python src\main.py
pause