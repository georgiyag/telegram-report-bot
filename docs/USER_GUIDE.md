# Руководство пользователя

Полное руководство по использованию Telegram Report Bot для сотрудников и администраторов.

## Содержание

- [Для сотрудников](#для-сотрудников)
- [Для администраторов](#для-администраторов)
- [Часто задаваемые вопросы](#часто-задаваемые-вопросы)
- [Устранение проблем](#устранение-проблем)

## Для сотрудников

### Начало работы

1. **Найдите бота**: Найдите бота по имени или получите ссылку от администратора
2. **Запустите бота**: Нажмите кнопку "Start" или отправьте команду `/start`
3. **Получите приветствие**: Бот отправит приветственное сообщение с инструкциями

### Основные команды

#### `/start`
Запускает бота и показывает приветственное сообщение.

**Пример использования:**
```
/start
```

**Ответ бота:**
```
👋 Добро пожаловать в систему отчетов АО ЭМЗ "ФИРМА СЭЛМА"!

📋 Доступные команды:
/report - Создать новый отчет
/status - Проверить статус отчетов
/help - Показать справку
```

#### `/help`
Показывает справочную информацию и список доступных команд.

#### `/report`
Запускает процесс создания нового еженедельного отчета.

#### `/status`
Показывает статус ваших отчетов за текущую и предыдущие недели.

### Создание отчета

#### Шаг 1: Запуск процесса

Отправьте команду `/report`. Бот проверит:
- Не создан ли уже отчет за текущую неделю
- Зарегистрированы ли вы в системе

#### Шаг 2: Описание выполненных задач

**Вопрос бота:**
```
📝 Опишите задачи, которые вы выполнили на этой неделе:

💡 Советы:
• Будьте конкретны и детальны
• Укажите результаты работы
• Используйте маркированные списки для удобства

⏰ У вас есть 10 минут на ввод.
```

**Пример ответа:**
```
• Разработал модуль авторизации пользователей
• Исправил 5 критических багов в системе отчетности
• Провел код-ревью для 3 pull request'ов
• Обновил документацию API
• Настроил CI/CD pipeline для тестового окружения
```

#### Шаг 3: Достижения

**Вопрос бота:**
```
🏆 Какие достижения или успехи вы хотите отметить?

💡 Например:
• Завершенные проекты
• Улучшения процессов
• Изученные технологии
• Помощь коллегам
```

**Пример ответа:**
```
• Успешно запустил новую систему мониторинга
• Сократил время сборки проекта на 40%
• Изучил новый фреймворк FastAPI
• Помог новому сотруднику освоиться в команде
```

#### Шаг 4: Проблемы (опционально)

**Вопрос бота:**
```
⚠️ Возникли ли какие-то проблемы или препятствия?

💡 Это поможет руководству:
• Понять текущие сложности
• Предоставить необходимую поддержку
• Улучшить рабочие процессы

🔄 Нажмите "Пропустить", если проблем не было.
```

**Пример ответа:**
```
• Задержка в получении доступа к тестовому серверу
• Нехватка документации по legacy коду
• Конфликт версий библиотек в проекте
```

#### Шаг 5: Планы на следующую неделю

**Вопрос бота:**
```
📅 Какие задачи планируете выполнить на следующей неделе?

💡 Укажите:
• Основные задачи и цели
• Ожидаемые результаты
• Необходимые ресурсы
```

**Пример ответа:**
```
• Завершить интеграцию с платежной системой
• Написать unit-тесты для нового модуля
• Провести презентацию результатов для заказчика
• Начать работу над мобильным приложением
```

#### Шаг 6: Подтверждение

**Предварительный просмотр:**
```
📋 Ваш отчет за неделю 15-21 января 2024:

👤 Сотрудник: Иван Иванов
🏢 Отдел: Разработка
📅 Период: 15.01.2024 - 21.01.2024

📝 Выполненные задачи:
• Разработал модуль авторизации пользователей
• Исправил 5 критических багов в системе отчетности
...

🏆 Достижения:
• Успешно запустил новую систему мониторинга
...

⚠️ Проблемы:
• Задержка в получении доступа к тестовому серверу
...

📅 Планы на следующую неделю:
• Завершить интеграцию с платежной системой
...

✅ Подтвердить отправку?
```

**Действия:**
- ✅ **Отправить** - отправить отчет
- ✏️ **Редактировать** - изменить отчет
- ❌ **Отменить** - отменить создание

### Проверка статуса отчетов

Команда `/status` показывает информацию о ваших отчетах:

```
📊 Статус ваших отчетов:

📅 Текущая неделя (15-21 января):
✅ Отчет отправлен 19.01.2024 в 14:30
📝 Статус: Обработан
🤖 ИИ-анализ: Выполнен

📅 Предыдущая неделя (8-14 января):
✅ Отчет отправлен 12.01.2024 в 16:45
📝 Статус: Архивирован

📅 Неделя (1-7 января):
❌ Отчет не отправлен
⚠️ Просрочен

📈 Статистика:
• Отправлено отчетов: 15/17
• Процент выполнения: 88%
• Средняя оценка: 4.2/5
```

### Уведомления и напоминания

#### Автоматические напоминания

Бот отправляет напоминания:
- **Понедельник 9:00** - напоминание о необходимости отчета
- **Среда 15:00** - если отчет еще не отправлен
- **Пятница 17:00** - последнее напоминание

#### Типы уведомлений

**Напоминание о создании отчета:**
```
⏰ Напоминание!

Пора создать отчет за текущую неделю (15-21 января).

📝 Отправьте команду /report для начала.

⏳ Дедлайн: Пятница, 21 января, 18:00
```

**Подтверждение отправки:**
```
✅ Отчет успешно отправлен!

📋 Ваш отчет за неделю 15-21 января принят и будет обработан.

🤖 ИИ-анализ будет выполнен в течение нескольких минут.
📧 Уведомление о результатах придет в группу.
```

**Уведомление об ошибке:**
```
❌ Ошибка при отправке отчета!

🔧 Попробуйте еще раз через несколько минут.
Если проблема повторится, обратитесь к администратору.

📞 Техподдержка: @admin_username
```

## Для администраторов

### Доступ к административной панели

Для доступа к административным функциям ваш User ID должен быть добавлен в список администраторов в конфигурации бота.

#### Команда `/admin`

Открывает главное меню административной панели:

```
🔧 Административная панель

📊 Статистика
👥 Управление пользователями
📋 Просмотр отчетов
🔔 Отправка напоминаний
📤 Экспорт данных
⚙️ Настройки
```

### Просмотр статистики

#### Общая статистика

```
📊 Статистика системы отчетов

📅 Текущая неделя (15-21 января 2024):
• Всего сотрудников: 25
• Отправили отчеты: 18 (72%)
• Ожидают отправки: 7 (28%)
• Средняя длина отчета: 245 слов

📈 За последний месяц:
• Всего отчетов: 98
• Процент выполнения: 85%
• Средняя оценка ИИ: 4.1/5

🏆 Топ отделы по активности:
1. Разработка - 95%
2. Тестирование - 90%
3. Аналитика - 87%
4. Дизайн - 82%
```

#### Детальная статистика по отделам

```
🏢 Отдел: Разработка

👥 Сотрудники: 8
📋 Отчеты за неделю: 7/8 (87.5%)

✅ Отправили отчеты:
• Иван Иванов - 19.01 14:30
• Петр Петров - 19.01 15:45
• Анна Сидорова - 20.01 09:15
...

❌ Не отправили:
• Сергей Козлов

📊 Средние показатели:
• Длина отчета: 280 слов
• Оценка ИИ: 4.3/5
• Время отправки: 15:30
```

### Управление пользователями

#### Просмотр списка пользователей

```
👥 Управление пользователями

🔍 Поиск по имени или ID
➕ Добавить нового сотрудника
📝 Редактировать информацию
🗑️ Удалить сотрудника
📊 Статистика по сотруднику
```

#### Добавление нового сотрудника

1. Выберите "➕ Добавить нового сотрудника"
2. Введите Telegram User ID
3. Укажите ФИО
4. Выберите отдел
5. Укажите должность
6. Подтвердите добавление

#### Редактирование информации сотрудника

```
📝 Редактирование: Иван Иванов

👤 ФИО: Иван Иванович Иванов
🆔 User ID: 123456789
🏢 Отдел: Разработка
💼 Должность: Senior Developer
📅 Дата добавления: 15.01.2024
📊 Статистика: 15/17 отчетов (88%)

✏️ Изменить ФИО
🏢 Изменить отдел
💼 Изменить должность
🗑️ Удалить сотрудника
```

### Просмотр отчетов

#### Фильтры для просмотра

```
📋 Просмотр отчетов

📅 По периоду:
• Текущая неделя
• Предыдущая неделя
• Выбрать период

🏢 По отделу:
• Все отделы
• Разработка
• Тестирование
• Аналитика
• Дизайн

👤 По сотруднику:
• Все сотрудники
• Поиск по имени
```

#### Детальный просмотр отчета

```
📋 Отчет: Иван Иванов
📅 Период: 15-21 января 2024
⏰ Отправлен: 19.01.2024 в 14:30

📝 Выполненные задачи:
• Разработал модуль авторизации пользователей
• Исправил 5 критических багов в системе отчетности
• Провел код-ревью для 3 pull request'ов
• Обновил документацию API
• Настроил CI/CD pipeline для тестового окружения

🏆 Достижения:
• Успешно запустил новую систему мониторинга
• Сократил время сборки проекта на 40%
• Изучил новый фреймворк FastAPI
• Помог новому сотруднику освоиться в команде

⚠️ Проблемы:
• Задержка в получении доступа к тестовому серверу
• Нехватка документации по legacy коду
• Конфликт версий библиотек в проекте

📅 Планы на следующую неделю:
• Завершить интеграцию с платежной системой
• Написать unit-тесты для нового модуля
• Провести презентацию результатов для заказчика
• Начать работу над мобильным приложением

🤖 ИИ-анализ:
📊 Оценка продуктивности: 4.5/5
💡 Рекомендации: Рассмотреть возможность автоматизации тестирования
🎯 Фокус: Высокая техническая экспертиза, хорошее планирование

📤 Действия:
• 📧 Переслать в группу
• 📊 Экспортировать
• 🗑️ Удалить
```

### Отправка напоминаний

#### Массовая рассылка

```
🔔 Отправка напоминаний

📋 Кому отправить:
• Всем сотрудникам без отчета (7 человек)
• Конкретному отделу
• Выбранным сотрудникам

📝 Тип напоминания:
• Стандартное напоминание
• Срочное напоминание
• Персональное сообщение

⏰ Время отправки:
• Сейчас
• Запланировать
```

#### Персональные напоминания

```
📝 Персональное напоминание для: Сергей Козлов

💬 Текст сообщения:
"Сергей, напоминаю о необходимости отправить отчет за текущую неделю. Дедлайн - завтра в 18:00. Если есть вопросы, обращайтесь!"

📤 Отправить сейчас
⏰ Запланировать на завтра 9:00
```

### Экспорт данных

#### Доступные форматы

```
📤 Экспорт данных

📊 Что экспортировать:
• Все отчеты за период
• Статистику по отделам
• Список сотрудников
• ИИ-анализ отчетов

📅 Период:
• Текущая неделя
• Текущий месяц
• Выбрать период

📄 Формат:
• Excel (.xlsx)
• CSV (.csv)
• PDF отчет
• JSON данные
```

#### Пример экспорта

```
📤 Экспорт завершен!

📊 Отчеты за январь 2024
📁 Файл: reports_january_2024.xlsx
📏 Размер: 2.3 MB
📋 Содержимое: 98 отчетов, 25 сотрудников

⬇️ Скачать файл
📧 Отправить на email
☁️ Сохранить в облако
```

### Настройки системы

#### Общие настройки

```
⚙️ Настройки системы

⏰ Время напоминаний:
• Первое: Понедельник 9:00
• Второе: Среда 15:00
• Последнее: Пятница 17:00

📅 Дедлайн отчетов:
• Пятница 18:00

🤖 ИИ-анализ:
• Включен ✅
• Модель: llama3.1
• Автоматический анализ: Да

📧 Уведомления:
• В группу: Включены ✅
• Администраторам: Включены ✅
• Email: Отключены ❌
```

#### Управление отделами

```
🏢 Управление отделами

📋 Текущие отделы:
• Разработка (8 сотрудников)
• Тестирование (5 сотрудников)
• Аналитика (6 сотрудников)
• Дизайн (4 сотрудников)
• Управление (2 сотрудника)

➕ Добавить отдел
✏️ Редактировать отдел
🗑️ Удалить отдел
```

## Часто задаваемые вопросы

### Для сотрудников

**Q: Можно ли изменить отчет после отправки?**
A: Нет, после подтверждения отправки отчет изменить нельзя. Если нужны исправления, обратитесь к администратору.

**Q: Что делать, если забыл отправить отчет?**
A: Отправьте отчет как можно скорее. Система отметит его как просроченный, но он все равно будет учтен.

**Q: Можно ли отправить отчет заранее?**
A: Да, отчет можно отправить в любой день текущей недели.

**Q: Что означают оценки ИИ-анализа?**
A: ИИ анализирует ваш отчет по критериям: детальность, конкретность, планирование, проблемы. Оценка от 1 до 5.

**Q: Почему бот не отвечает?**
A: Проверьте:
- Не заблокирован ли бот
- Есть ли интернет-соединение
- Не ведется ли техническое обслуживание

### Для администраторов

**Q: Как добавить нового администратора?**
A: Добавьте User ID в переменную ADMIN_USER_IDS в файле .env и перезапустите бота.

**Q: Можно ли восстановить удаленный отчет?**
A: Если есть резервная копия базы данных, то да. Обратитесь к системному администратору.

**Q: Как настроить интеграцию с Ollama?**
A: Установите Ollama, загрузите модель и укажите URL в конфигурации. Подробности в документации по установке.

**Q: Можно ли изменить формат отчетов?**
A: Да, но это требует изменения кода. Обратитесь к разработчикам.

## Устранение проблем

### Проблемы с отправкой отчетов

**Проблема**: Бот не принимает отчет
**Решение**:
1. Проверьте, не превышает ли текст лимиты Telegram (4096 символов)
2. Убедитесь, что не используете запрещенные символы
3. Попробуйте разбить длинный текст на части

**Проблема**: Отчет отправляется, но не появляется в статистике
**Решение**:
1. Подождите несколько минут
2. Проверьте команду /status
3. Обратитесь к администратору

### Проблемы с уведомлениями

**Проблема**: Не приходят напоминания
**Решение**:
1. Проверьте, не заблокирован ли бот
2. Убедитесь, что вы в списке сотрудников
3. Проверьте настройки уведомлений в Telegram

### Проблемы администраторов

**Проблема**: Нет доступа к админ-панели
**Решение**:
1. Проверьте, что ваш User ID в списке администраторов
2. Перезапустите бота после изменения конфигурации
3. Проверьте правильность User ID

**Проблема**: ИИ-анализ не работает
**Решение**:
1. Проверьте, запущен ли Ollama
2. Убедитесь, что модель загружена
3. Проверьте URL подключения в конфигурации

## Контакты и поддержка

**Техническая поддержка**: @admin_username  
**Email**: support@selma.ru  
**Телефон**: +7 (XXX) XXX-XX-XX  

**Часы работы поддержки**: Пн-Пт 9:00-18:00 (МСК)

---

*Документация обновлена: январь 2024*  
*Версия бота: 1.0.0*