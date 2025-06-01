#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Главный модуль Telegram-бота для обработки еженедельных отчетов сотрудников.
АО ЭМЗ "ФИРМА СЭЛМА"

Автор: Telegram Report Bot
Версия: 1.0.0
"""

import asyncio
import sys
import signal
from pathlib import Path
from typing import Optional
from warnings import filterwarnings

from loguru import logger
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters
)
from telegram.warnings import PTBUserWarning

# Подавляем предупреждения о CallbackQueryHandler в ConversationHandler
filterwarnings(action="ignore", message=r".*CallbackQueryHandler", category=PTBUserWarning)

# Добавляем путь к исходному коду в PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent))

from config import settings, COMPANY_NAME, MESSAGES
from handlers import (
    ReportHandler,
    AdminHandler,
    MenuHandler,
    UserHandler,
    ReportStates,
    AdminStates,
    UserStates,
    MainMenuStates
)
from services import (
    OllamaService,
    TelegramService,
    ReportProcessor,
    TaskManager
)
from database import DatabaseManager
from utils import get_timezone

class TelegramReportBot:
    """Основной класс Telegram-бота для обработки отчетов"""
    
    def __init__(self):
        self.application: Optional[Application] = None
        self.ollama_service: Optional[OllamaService] = None
        self.telegram_service: Optional[TelegramService] = None
        self.report_processor: Optional[ReportProcessor] = None
        self.task_manager: Optional[TaskManager] = None
        self.report_handler: Optional[ReportHandler] = None
        self.admin_handler: Optional[AdminHandler] = None
        self.menu_handler: Optional[MenuHandler] = None
        self._shutdown_event = asyncio.Event()
    
    async def initialize_services(self) -> bool:
        """Инициализация всех сервисов"""
        try:
            logger.info("Инициализация сервисов...")
            
            # Инициализация базы данных
            db_manager = DatabaseManager()
            await db_manager.initialize()
            logger.info("База данных инициализирована")
            
            # Инициализация Ollama сервиса
            self.ollama_service = OllamaService()
            
            # Проверка подключения к Ollama
            if not await self.ollama_service.check_connection():
                logger.warning("Не удалось подключиться к Ollama. Функции ИИ будут недоступны.")
            else:
                logger.success("Подключение к Ollama установлено")
            
            # Инициализация Telegram сервиса
            from telegram import Bot
            bot = Bot(token=settings.telegram_bot_token)
            self.telegram_service = TelegramService(bot=bot)
            
            # Инициализация менеджера задач
            self.task_manager = TaskManager()
            
            # Инициализация процессора отчетов
            self.report_processor = ReportProcessor(
                ollama_service=self.ollama_service,
                telegram_service=self.telegram_service
            )
            
            # Инициализация обработчиков
            self.report_handler = ReportHandler(
                report_processor=self.report_processor,
                ollama_service=self.ollama_service,
                telegram_service=self.telegram_service,
                task_manager=self.task_manager,
                db_manager=db_manager
            )
            
            self.admin_handler = AdminHandler(
                report_processor=self.report_processor,
                db_manager=db_manager
            )
            
            self.user_handler = UserHandler(db_manager)
            
            # Инициализация обработчика меню
            self.menu_handler = MenuHandler(
                report_handler=self.report_handler,
                admin_handler=self.admin_handler
            )
            
            logger.success("Все сервисы успешно инициализированы")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при инициализации сервисов: {e}")
            return False
    
    def setup_handlers(self):
        """Настройка обработчиков команд и сообщений"""
        logger.info("Настройка обработчиков...")
        
        # Обработчик главного меню (ConversationHandler)
        menu_conv_handler = ConversationHandler(
            entry_points=[
                CommandHandler('start', self.menu_handler.show_main_menu),
                CallbackQueryHandler(self.menu_handler.show_main_menu, pattern='^back_to_main$')
            ],
            states={
                MainMenuStates.MAIN_MENU: [
                    CallbackQueryHandler(self._handle_menu_admin, pattern='^menu_admin$'),
                    CallbackQueryHandler(self.menu_handler.handle_menu_callback, pattern='^menu_(?!report$|admin$)'),
                    CallbackQueryHandler(self.menu_handler.handle_menu_callback, pattern='^back_to_main$')
                ]
            },
            fallbacks=[
                CommandHandler('cancel', self.menu_handler.cancel_menu)
            ],
            name="menu_conversation",
            persistent=False,
            per_message=False
        )
        
        # Обработчик отчетов (ConversationHandler)
        report_conv_handler = ConversationHandler(
            entry_points=[
                CommandHandler('report', self.report_handler.report_command),
                CallbackQueryHandler(self.report_handler.report_command, pattern='^menu_report$')
            ],
            states={
                ReportStates.WAITING_DEPARTMENT: [
                    CallbackQueryHandler(self.report_handler.receive_department, pattern='^dept_')
                ],
                ReportStates.WAITING_TASKS: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.report_handler.receive_tasks)
                ],
                ReportStates.WAITING_ACHIEVEMENTS: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.report_handler.receive_achievements)
                ],
                ReportStates.WAITING_PROBLEMS: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.report_handler.receive_problems)
                ],
                ReportStates.WAITING_PLANS: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.report_handler.receive_plans)
                ],
                ReportStates.WAITING_CONFIRMATION: [
                    CallbackQueryHandler(self.report_handler.confirm_report)
                ]
            },
            fallbacks=[
                CommandHandler('cancel', self.report_handler.cancel_report),
                CallbackQueryHandler(self.report_handler.cancel_report, pattern='^cancel$')
            ],
            name="report_conversation",
            persistent=False,
            per_message=False
        )
        
        # Обработчик админ-панели (ConversationHandler)
        admin_conv_handler = ConversationHandler(
            entry_points=[
                CommandHandler('admin', self.admin_handler.admin_command),
                CallbackQueryHandler(self.admin_handler.admin_command, pattern='^menu_admin$'),
                CallbackQueryHandler(self.admin_handler.handle_admin_callback, pattern='^admin_')
            ],
            states={
                AdminStates.MAIN_MENU: [
                    CallbackQueryHandler(self.admin_handler.handle_admin_callback, pattern='^admin_')
                ],
                AdminStates.VIEW_REPORTS: [
                    CallbackQueryHandler(self.admin_handler.handle_reports_callback, pattern='^reports_'),
                    CallbackQueryHandler(self.admin_handler.handle_admin_callback, pattern='^admin_')
                ],
                AdminStates.MANAGE_USERS: [
                    CallbackQueryHandler(self.admin_handler.handle_users_callback, pattern='^(users_|departments_)'),
                    CallbackQueryHandler(self.admin_handler.handle_admin_callback, pattern='^admin_')
                ],
                AdminStates.SEND_REMINDER: [
                    CallbackQueryHandler(self.admin_handler.handle_reminder_callback, pattern='^reminder_'),
                    CallbackQueryHandler(self.admin_handler.handle_admin_callback, pattern='^admin_')
                ],
                AdminStates.EXPORT_DATA: [
                    CallbackQueryHandler(self.admin_handler.handle_export_callback, pattern='^export_'),
                    CallbackQueryHandler(self.admin_handler.handle_admin_callback, pattern='^admin_')
                ]
            },
            fallbacks=[
                CommandHandler('cancel', self.admin_handler._cancel_admin),
                CallbackQueryHandler(self.admin_handler._cancel_admin, pattern='^admin_cancel$')
            ],
            name="admin_conversation",
            persistent=False,
            per_message=False
        )
        
        # Добавляем обработчики в приложение (порядок важен!)
        self.application.add_handler(menu_conv_handler)  # Главное меню - первый приоритет
        self.application.add_handler(report_conv_handler)
        self.application.add_handler(admin_conv_handler)
        
        # Отдельный обработчик menu_admin уже добавлен в menu_conv_handler
        
        # Простые команды
        self.application.add_handler(CommandHandler('help', self.user_handler.help_command))
        self.application.add_handler(CommandHandler('status', self.user_handler.status_command))
        self.application.add_handler(CommandHandler('task_status', self.report_handler.task_status_command))
        self.application.add_handler(CommandHandler('stats', self.admin_handler.stats_command))
        
        # Обработчик отмены задач
        self.application.add_handler(CallbackQueryHandler(
            self.report_handler.cancel_task_callback, 
            pattern='^cancel_task_'
        ))
        
        # Обработчик неизвестных команд
        self.application.add_handler(MessageHandler(
            filters.COMMAND, 
            self.handle_unknown_command
        ))
        
        # Обработчик ошибок
        self.application.add_error_handler(self.error_handler)
        
        logger.success("Обработчики настроены")
    
    async def _handle_menu_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка нажатия кнопки 'Панель администратора' из меню"""
        user = update.effective_user
        is_admin = user.id in settings.get_admin_ids()
        
        if not is_admin:
            from handlers.states import get_back_to_main_keyboard
            await update.callback_query.edit_message_text(
                text="❌ У вас нет прав для выполнения этой команды.",
                reply_markup=get_back_to_main_keyboard()
            )
            return ConversationHandler.END
        
        # Переходим к админ-панели через команду
        await self.admin_handler.admin_command(update, context)
        # Завершаем menu_conversation, чтобы admin_conversation мог начаться
        return ConversationHandler.END
    
    async def handle_unknown_command(self, update: Update, context) -> None:
        """Обработка неизвестных команд"""
        from handlers.states import get_main_menu_keyboard
        
        if not update.message:
            return
            
        user = update.effective_user
        is_admin = user.id in settings.get_admin_ids()
        
        await update.message.reply_text(
            MESSAGES['unknown_command'],
            reply_markup=get_main_menu_keyboard(is_admin)
        )
    
    async def error_handler(self, update: Update, context) -> None:
        """Обработка ошибок"""
        logger.error(f"Ошибка при обработке обновления {update}: {context.error}")
        
        if update and update.effective_message:
            try:
                await update.effective_message.reply_text(
                    "😔 Произошла ошибка при обработке вашего запроса. "
                    "Пожалуйста, попробуйте позже или обратитесь к администратору."
                )
            except Exception as e:
                logger.error(f"Не удалось отправить сообщение об ошибке: {e}")
        elif update and update.callback_query:
            try:
                await update.callback_query.answer(
                    "😔 Произошла ошибка при обработке запроса.",
                    show_alert=True
                )
            except Exception as e:
                logger.error(f"Не удалось отправить callback ответ об ошибке: {e}")
    
    async def setup_application(self) -> bool:
        """Настройка Telegram приложения"""
        try:
            logger.info("Настройка Telegram приложения...")
            
            # Создаем приложение
            self.application = (
                Application.builder()
                .token(settings.telegram_bot_token)
                .build()
            )
            
            # Настраиваем обработчики
            self.setup_handlers()
            
            logger.success("Telegram приложение настроено")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при настройке приложения: {e}")
            return False
    
    def setup_signal_handlers(self):
        """Настройка обработчиков сигналов для graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info(f"Получен сигнал {signum}, начинаем graceful shutdown...")
            self._shutdown_event.set()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def start(self) -> None:
        """Запуск бота"""
        try:
            logger.info("🚀 Запуск Telegram Report Bot...")
            logger.info(f"Версия Python: {sys.version}")
            logger.info(f"Часовой пояс: {get_timezone()}")
            logger.info(f"Режим отладки: {settings.debug}")
            
            # Инициализация сервисов
            if not await self.initialize_services():
                logger.error("Не удалось инициализировать сервисы")
                return
            
            # Настройка приложения
            if not await self.setup_application():
                logger.error("Не удалось настроить приложение")
                return
            
            # Настройка обработчиков сигналов
            self.setup_signal_handlers()
            
            # Запуск бота
            logger.success("✅ Бот успешно запущен и готов к работе!")
            logger.info(f"Компания: {COMPANY_NAME}")
            logger.info(f"Администраторы: {settings.admin_user_ids}")
            
            # Уведомляем администраторов о запуске
            if self.telegram_service:
                await self.telegram_service.send_admin_notification(
                    settings.get_admin_ids(),
                    "🚀 Бот запущен и готов к работе!"
                )
            
            # Запускаем polling
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True
            )
            
            # Запускаем периодическую очистку задач
            cleanup_task = asyncio.create_task(self._periodic_cleanup())
            
            # Ждем сигнала завершения
            await self._shutdown_event.wait()
            
            # Отменяем задачу очистки
            cleanup_task.cancel()
            try:
                await cleanup_task
            except asyncio.CancelledError:
                pass
            
        except Exception as e:
            logger.error(f"Критическая ошибка при запуске бота: {e}")
            raise
        finally:
            await self.shutdown()
    
    async def shutdown(self) -> None:
        """Graceful shutdown бота"""
        logger.info("🛑 Завершение работы бота...")
        
        try:
            # Уведомляем администраторов о завершении работы
            if self.telegram_service:
                await self.telegram_service.send_admin_notification(
                    admin_ids=settings.get_admin_ids(),
                    message="🛑 Бот завершает работу"
                )
            
            # Останавливаем приложение
            if self.application:
                await self.application.updater.stop()
                await self.application.stop()
                await self.application.shutdown()
            
            # Закрываем сервисы
            if self.ollama_service:
                await self.ollama_service.close()
            
            logger.success("✅ Бот успешно завершил работу")
            
        except Exception as e:
            logger.error(f"Ошибка при завершении работы: {e}")
    
    async def _periodic_cleanup(self):
        """Периодическая очистка завершенных задач"""
        while True:
            try:
                await asyncio.sleep(3600)  # Очистка каждый час
                if self.task_manager:
                    self.task_manager.cleanup_completed_tasks(max_age_hours=24)
                    stats = self.task_manager.get_stats()
                    logger.info(f"Статистика задач: {stats}")
            except asyncio.CancelledError:
                logger.info("Периодическая очистка задач остановлена")
                break
            except Exception as e:
                logger.error(f"Ошибка при очистке задач: {e}")

def setup_logging():
    """Настройка логирования"""
    # Удаляем стандартный обработчик
    logger.remove()
    
    # Настраиваем формат логов
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )
    
    # Добавляем обработчик для консоли
    logger.add(
        sys.stderr,
        format=log_format,
        level=settings.log_level,
        colorize=True
    )
    
    # Добавляем обработчик для файла (если не в режиме отладки)
    if not settings.debug:
        logger.add(
            "logs/bot_{time:YYYY-MM-DD}.log",
            format=log_format,
            level=settings.log_level,
            rotation="1 day",
            retention="30 days",
            compression="zip"
        )
    
    # Настраиваем уровни для внешних библиотек
    import logging
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("telegram").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

async def main():
    """Главная функция"""
    # Настройка логирования
    setup_logging()
    
    # Проверяем настройки
    logger.info("Проверка конфигурации...")
    
    if not settings.telegram_bot_token:
        logger.error("TELEGRAM_BOT_TOKEN не установлен")
        sys.exit(1)
    
    if not settings.admin_user_ids:
        logger.error("ADMIN_USER_IDS не установлен")
        sys.exit(1)
    
    logger.success("Конфигурация проверена")
    
    # Создаем и запускаем бота
    bot = TelegramReportBot()
    
    try:
        await bot.start()
    except KeyboardInterrupt:
        logger.info("Получен сигнал прерывания")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Проверяем версию Python
    if sys.version_info < (3, 8):
        print("Ошибка: Требуется Python 3.8 или выше")
        sys.exit(1)
    
    # Запускаем бота
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 До свидания!")
    except Exception as e:
        print(f"Критическая ошибка: {e}")
        sys.exit(1)