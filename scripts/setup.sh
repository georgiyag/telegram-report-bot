#!/bin/bash
echo "Настройка проекта Telegram Report Bot..."

# Проверка версии Python
python3 --version
if [ $? -ne 0 ]; then
    echo "Ошибка: Python 3.8+ не найден"
    exit 1
fi

# Создание виртуального окружения
echo "Создание виртуального окружения..."
python3 -m venv venv

# Активация виртуального окружения
echo "Активация виртуального окружения..."
source venv/bin/activate

# Обновление pip
echo "Обновление pip..."
pip install --upgrade pip

# Установка зависимостей
echo "Установка зависимостей..."
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Создание .env файла из примера
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Создан файл .env. Пожалуйста, заполните необходимые переменные."
fi

echo "Установка завершена успешно!"
echo "Для активации окружения используйте: source venv/bin/activate"
echo "Для запуска бота: python src/main.py"