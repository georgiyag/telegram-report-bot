import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from handlers.report_handler import ReportHandler
from handlers.admin_handler import AdminHandler
from handlers.states import ReportStates, AdminStates
from models.report import WeeklyReport
from services.report_processor import ReportProcessor
from services.telegram_service import TelegramService

class TestReportHandler:
    """Тесты для ReportHandler"""
    
    @pytest.fixture
    def mock_report_processor(self):
        """Мок для ReportProcessor"""
        processor = Mock(spec=ReportProcessor)
        processor.save_report = AsyncMock()
        processor.get_user_reports = AsyncMock(return_value=[])
        processor.get_current_week_report = AsyncMock(return_value=None)
        return processor
    
    @pytest.fixture
    def mock_telegram_service(self):
        """Мок для TelegramService"""
        service = Mock(spec=TelegramService)
        service.send_message = AsyncMock()
        service.send_typing_action = AsyncMock()
        service.create_report_keyboard = Mock()
        return service
    
    @pytest.fixture
    def report_handler(self, mock_report_processor, mock_telegram_service):
        """Создание экземпляра ReportHandler с моками"""
        return ReportHandler(
            report_processor=mock_report_processor,
            telegram_service=mock_telegram_service
        )
    
    @pytest.fixture
    def mock_update(self):
        """Мок для Update"""
        update = Mock()
        update.effective_user.id = 123456789
        update.effective_user.username = "testuser"
        update.effective_user.full_name = "Test User"
        update.message.text = "Test message"
        update.message.reply_text = AsyncMock()
        update.callback_query = None
        return update
    
    @pytest.fixture
    def mock_context(self):
        """Мок для CallbackContext"""
        context = Mock()
        context.user_data = {}
        return context
    
    @pytest.mark.asyncio
    async def test_start_command(self, report_handler, mock_update, mock_context):
        """Тест команды /start"""
        result = await report_handler.start_command(mock_update, mock_context)
        
        # Проверяем, что отправлено приветственное сообщение
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args[0][0]
        assert "Добро пожаловать" in call_args
        assert "АО ЭМЗ \"ФИРМА СЭЛМА\"" in call_args
    
    @pytest.mark.asyncio
    async def test_help_command(self, report_handler, mock_update, mock_context):
        """Тест команды /help"""
        await report_handler.help_command(mock_update, mock_context)
        
        # Проверяем, что отправлено сообщение с помощью
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args[0][0]
        assert "Справка" in call_args
        assert "/report" in call_args
    
    @pytest.mark.asyncio
    async def test_start_report_new_user(self, report_handler, mock_update, mock_context, mock_report_processor):
        """Тест начала создания отчета для нового пользователя"""
        # Настраиваем мок - пользователь не найден
        mock_report_processor.get_current_week_report.return_value = None
        
        result = await report_handler.start_report(mock_update, mock_context)
        
        # Проверяем, что состояние изменилось
        assert result == ReportStates.WAITING_TASKS
        
        # Проверяем, что в user_data сохранены данные пользователя
        assert 'report_data' in mock_context.user_data
        assert mock_context.user_data['report_data']['user_id'] == 123456789
        assert mock_context.user_data['report_data']['username'] == "testuser"
        assert mock_context.user_data['report_data']['full_name'] == "Test User"
    
    @pytest.mark.asyncio
    async def test_start_report_existing_report(self, report_handler, mock_update, mock_context, mock_report_processor):
        """Тест начала создания отчета при наличии существующего отчета"""
        # Создаем существующий отчет
        existing_report = WeeklyReport(
            user_id=123456789,
            username="testuser",
            full_name="Test User",
            week_start=datetime.now(),
            week_end=datetime.now() + timedelta(days=6),
            completed_tasks="Existing tasks",
            achievements="Existing achievements",
            next_week_plans="Existing plans"
        )
        
        mock_report_processor.get_current_week_report.return_value = existing_report
        
        await report_handler.start_report(mock_update, mock_context)
        
        # Проверяем, что отправлено сообщение о существующем отчете
        mock_update.message.reply_text.assert_called()
        call_args = mock_update.message.reply_text.call_args[0][0]
        assert "уже создан отчет" in call_args.lower()
    
    @pytest.mark.asyncio
    async def test_handle_tasks_valid(self, report_handler, mock_update, mock_context):
        """Тест обработки валидных задач"""
        # Подготавливаем контекст
        mock_context.user_data = {
            'report_data': {
                'user_id': 123456789,
                'username': 'testuser',
                'full_name': 'Test User'
            }
        }
        
        mock_update.message.text = "Выполнил важные задачи по разработке и тестированию системы"
        
        result = await report_handler.handle_tasks(mock_update, mock_context)
        
        # Проверяем, что задачи сохранены и состояние изменилось
        assert result == ReportStates.WAITING_ACHIEVEMENTS
        assert mock_context.user_data['report_data']['completed_tasks'] == mock_update.message.text
    
    @pytest.mark.asyncio
    async def test_handle_tasks_invalid(self, report_handler, mock_update, mock_context):
        """Тест обработки невалидных задач"""
        # Подготавливаем контекст
        mock_context.user_data = {
            'report_data': {
                'user_id': 123456789,
                'username': 'testuser',
                'full_name': 'Test User'
            }
        }
        
        mock_update.message.text = "Короткий текст"  # Слишком короткий
        
        result = await report_handler.handle_tasks(mock_update, mock_context)
        
        # Проверяем, что состояние не изменилось
        assert result == ReportStates.WAITING_TASKS
        
        # Проверяем, что отправлено сообщение об ошибке
        mock_update.message.reply_text.assert_called()
        call_args = mock_update.message.reply_text.call_args[0][0]
        assert "ошибка" in call_args.lower() or "неверно" in call_args.lower()
    
    @pytest.mark.asyncio
    async def test_confirm_report(self, report_handler, mock_update, mock_context, mock_report_processor):
        """Тест подтверждения отчета"""
        # Подготавливаем контекст с полным отчетом
        mock_context.user_data = {
            'report_data': {
                'user_id': 123456789,
                'username': 'testuser',
                'full_name': 'Test User',
                'completed_tasks': 'Выполненные задачи',
                'achievements': 'Достижения',
                'problems': 'Проблемы',
                'next_week_plans': 'Планы на следующую неделю'
            }
        }
        
        # Мокаем callback_query
        mock_update.callback_query = Mock()
        mock_update.callback_query.answer = AsyncMock()
        mock_update.callback_query.edit_message_text = AsyncMock()
        
        result = await report_handler.confirm_report(mock_update, mock_context)
        
        # Проверяем, что отчет сохранен
        mock_report_processor.save_report.assert_called_once()
        
        # Проверяем, что состояние завершено
        from telegram.ext import ConversationHandler
        assert result == ConversationHandler.END

class TestAdminHandler:
    """Тесты для AdminHandler"""
    
    @pytest.fixture
    def mock_report_processor(self):
        """Мок для ReportProcessor"""
        processor = Mock(spec=ReportProcessor)
        processor.get_statistics = AsyncMock(return_value={
            'total_reports': 10,
            'this_week_reports': 5,
            'total_users': 3
        })
        processor.get_all_reports = AsyncMock(return_value=[])
        processor.send_reminder_to_all = AsyncMock()
        return processor
    
    @pytest.fixture
    def mock_telegram_service(self):
        """Мок для TelegramService"""
        service = Mock(spec=TelegramService)
        service.send_message = AsyncMock()
        service.create_admin_keyboard = Mock()
        return service
    
    @pytest.fixture
    def admin_handler(self, mock_report_processor, mock_telegram_service):
        """Создание экземпляра AdminHandler с моками"""
        return AdminHandler(
            report_processor=mock_report_processor,
            telegram_service=mock_telegram_service
        )
    
    @pytest.fixture
    def mock_admin_update(self):
        """Мок для Update от администратора"""
        update = Mock()
        update.effective_user.id = 123456789  # ID должен быть в ADMIN_USER_IDS
        update.message.reply_text = AsyncMock()
        return update
    
    @pytest.fixture
    def mock_context(self):
        """Мок для CallbackContext"""
        context = Mock()
        context.user_data = {}
        return context
    
    @pytest.mark.asyncio
    @patch('handlers.admin_handler.settings.ADMIN_USER_IDS', [123456789])
    async def test_admin_panel_authorized(self, admin_handler, mock_admin_update, mock_context):
        """Тест доступа к админ-панели для авторизованного пользователя"""
        result = await admin_handler.admin_panel(mock_admin_update, mock_context)
        
        # Проверяем, что состояние изменилось на главное меню админки
        assert result == AdminStates.MAIN_MENU
        
        # Проверяем, что отправлено сообщение с админ-панелью
        mock_admin_update.message.reply_text.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('handlers.admin_handler.settings.ADMIN_USER_IDS', [987654321])  # Другой ID
    async def test_admin_panel_unauthorized(self, admin_handler, mock_admin_update, mock_context):
        """Тест отказа в доступе к админ-панели для неавторизованного пользователя"""
        from telegram.ext import ConversationHandler
        
        result = await admin_handler.admin_panel(mock_admin_update, mock_context)
        
        # Проверяем, что разговор завершен
        assert result == ConversationHandler.END
        
        # Проверяем, что отправлено сообщение об отказе в доступе
        mock_admin_update.message.reply_text.assert_called_once()
        call_args = mock_admin_update.message.reply_text.call_args[0][0]
        assert "доступ запрещен" in call_args.lower() or "не авторизован" in call_args.lower()
    
    @pytest.mark.asyncio
    @patch('handlers.admin_handler.settings.ADMIN_USER_IDS', [123456789])
    async def test_show_statistics(self, admin_handler, mock_admin_update, mock_context, mock_report_processor):
        """Тест показа статистики"""
        await admin_handler.show_statistics(mock_admin_update, mock_context)
        
        # Проверяем, что запрошена статистика
        mock_report_processor.get_statistics.assert_called_once()
        
        # Проверяем, что отправлено сообщение со статистикой
        mock_admin_update.message.reply_text.assert_called_once()
        call_args = mock_admin_update.message.reply_text.call_args[0][0]
        assert "статистика" in call_args.lower()

class TestIntegration:
    """Интеграционные тесты"""
    
    @pytest.mark.asyncio
    async def test_full_report_flow(self):
        """Тест полного потока создания отчета"""
        # Этот тест требует более сложной настройки с реальными сервисами
        # Пока оставляем как заглушку для будущей реализации
        pass
    
    @pytest.mark.asyncio
    async def test_admin_workflow(self):
        """Тест полного административного workflow"""
        # Этот тест требует более сложной настройки с реальными сервисами
        # Пока оставляем как заглушку для будущей реализации
        pass

if __name__ == "__main__":
    pytest.main([__file__])