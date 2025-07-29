from telegram import Update
from telegram.ext import ContextTypes
from loguru import logger

import logging
from config import MESSAGES
from database import DatabaseManager, Employee
from utils.navigation import get_breadcrumb_path, create_keyboard


class UserHandler:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработка команды /start"""
        user = update.effective_user
        
        # Проверяем, есть ли пользователь в базе данных
        try:
            employee = await self.db_manager.get_employee_by_user_id(user.id)
            if not employee:
                # Регистрируем нового пользователя
                new_employee = Employee(
                    user_id=user.id,
                    username=user.username,
                    full_name=f"{user.first_name} {user.last_name or ''}".strip(),
                    email=None,
                    department_code=None,
                    position=None,
                    is_active=True
                )
                await self.db_manager.add_employee(new_employee)
                self.logger.info(f"Зарегистрирован новый пользователь: {user.id}")
        except Exception as e:
            self.logger.error(f"Ошибка при регистрации пользователя: {e}")
        
        welcome_text = (
            f"👋 Добро пожаловать, <b>{user.first_name}</b>!\n\n"
            f"🏢 <b>Система отправки резюме за неделю</b>\n"
            f"<i>АО ЭМЗ ФИРМА СЭЛМА</i>\n\n"
            f"🤖 Я помогу вам легко и быстро отправить еженедельный отчет.\n\n"
            f"✨ <b>Что я умею:</b>\n"
            f"📝 Создание еженедельных отчетов\n"
            f"📊 Проверка статуса отчетов\n"
            f"🔔 Напоминания о сроках\n"
            f"❓ Помощь и поддержка\n\n"
            f"🎯 Используйте кнопки ниже для навигации!"
        )
        
        await update.message.reply_text(welcome_text, parse_mode='HTML')
        
        # Показываем главное меню после приветствия
        from .states import MainMenuStates, get_main_menu_keyboard
        
        # Отправляем главное меню с кнопками
        from config import settings
        keyboard = get_main_menu_keyboard(user.id in settings.get_admin_ids())
        await update.message.reply_text(
            "Выберите действие:",
            reply_markup=keyboard
        )
        return MainMenuStates.MAIN_MENU

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Показать справку"""
        breadcrumb = get_breadcrumb_path("help")
        
        help_text = (
            f"{breadcrumb}\n\n"
            f"📚 <b>Справка по использованию бота</b>\n\n"
            f"🚀 <b>Основные команды:</b>\n"
            f"• <code>/start</code> - запуск бота и регистрация\n"
            f"• <code>/report</code> - создание нового отчета\n"
            f"• <code>/status</code> - проверка статуса отчетов\n"
            f"• <code>/menu</code> - главное меню\n\n"
            f"📝 <b>Как создать отчет:</b>\n"
            f"1️⃣ Нажмите кнопку 'Создать отчет'\n"
            f"2️⃣ Опишите выполненные задачи\n"
            f"3️⃣ Укажите планы на следующую неделю\n"
            f"4️⃣ Отправьте отчет на проверку\n\n"
            f"⏰ <b>Сроки подачи:</b>\n"
            f"Отчеты принимаются до пятницы 18:00\n\n"
            f"🔔 <b>Уведомления:</b>\n"
            f"Бот напомнит о необходимости подачи отчета\n\n"
            f"❓ <b>Нужна помощь?</b>\n"
            f"Обратитесь к администратору или HR-отделу"
        )
        
        keyboard = create_keyboard("help")
        await update.message.reply_text(help_text, parse_mode='HTML', reply_markup=keyboard)

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработка команды /status"""
        user = update.effective_user
        breadcrumb = get_breadcrumb_path("status")
        
        try:
            # Получаем статистику отчетов пользователя
            reports = await self.db_manager.get_user_reports(user.id)
            
            if not reports:
                status_text = (
                    f"{breadcrumb}\n\n"
                    f"📊 <b>Статус ваших отчетов</b>\n\n"
                    f"📝 <i>У вас пока нет отчетов</i>\n\n"
                    f"🚀 <b>Начните прямо сейчас!</b>\n"
                    f"Создайте свой первый отчет, нажав кнопку ниже\n\n"
                    f"💡 <b>Совет:</b> Регулярная подача отчетов\n"
                    f"поможет отслеживать ваш прогресс"
                )
            else:
                # Подсчет статистики
                approved_count = len([r for r in reports if r.status == "approved"])
                pending_count = len([r for r in reports if r.status == "pending"])
                rejected_count = len([r for r in reports if r.status == "rejected"])
                
                status_text = (
                    f"{breadcrumb}\n\n"
                    f"📊 <b>Статус ваших отчетов</b>\n\n"
                    f"📈 <b>Общая статистика:</b>\n"
                    f"✅ Одобрено: <b>{approved_count}</b>\n"
                    f"⏳ На рассмотрении: <b>{pending_count}</b>\n"
                    f"❌ Отклонено: <b>{rejected_count}</b>\n"
                    f"📝 Всего отчетов: <b>{len(reports)}</b>\n\n"
                    f"📋 <b>Последние отчеты:</b>\n"
                )
                
                for report in reports[-5:]:  # Показываем последние 5 отчетов
                    status_emoji = "✅" if report.status == "approved" else "⏳" if report.status == "pending" else "❌"
                    status_name = "Одобрен" if report.status == "approved" else "На рассмотрении" if report.status == "pending" else "Отклонен"
                    status_text += f"{status_emoji} <code>{report.week_start.strftime('%d.%m.%Y')}</code> - {status_name}\n"
                
                if len(reports) > 5:
                    status_text += f"\n<i>... и еще {len(reports) - 5} отчетов</i>"
            
            keyboard = create_keyboard("status")
            await update.message.reply_text(status_text, parse_mode='HTML', reply_markup=keyboard)
            
        except Exception as e:
            logger.error(f"Ошибка при получении статуса отчетов: {e}")
            error_text = (
                f"{breadcrumb}\n\n"
                f"❌ <b>Ошибка</b>\n\n"
                f"Не удалось загрузить статус отчетов.\n"
                f"Попробуйте позже или обратитесь к администратору."
            )
            keyboard = create_keyboard("status")
            await update.message.reply_text(error_text, parse_mode='HTML', reply_markup=keyboard)