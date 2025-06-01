#!/bin/bash

# Проверка существования виртуального окружения
if [ ! -d "venv" ]; then
    echo "Виртуальное окружение не найдено. Запустите setup.sh сначала."
    exit 1
fi

# Активация виртуального окружения
echo "Активация виртуального окружения..."
source venv/bin/activate

# Проверка существования .env файла
if [ ! -f ".env" ]; then
    echo "Файл .env не найден. Скопируйте .env.example в .env и заполните необходимые переменные."
    exit 1
fi

# Запуск бота
echo "Запуск Telegram Report Bot..."
python src/main.py