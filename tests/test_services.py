import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
import json

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from services.ollama_service import OllamaService
from services.telegram_service import TelegramService
from services.report_processor import ReportProcessor
from models.report import WeeklyReport
from models.department import Employee

class TestOllamaService:
    """Тесты для OllamaService"""
    
    @pytest.fixture
    def ollama_service(self):
        """Создание экземпляра OllamaService"""
        return OllamaService(
            base_url="http://localhost:11434",
            model="llama3.1"
        )
    
    @pytest.mark.asyncio
    async def test_check_connection_success(self, ollama_service):
        """Тест успешного подключения к Ollama"""
        with patch('aiohttp.ClientSession.get') as mock_get:
            # Мокаем успешный ответ
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {"status": "ok"}
            mock_get.return_value.__aenter__.return_value = mock_response
            
            result = await ollama_service.check_connection()
            assert result is True
    
    @pytest.mark.asyncio
    async def test_check_connection_failure(self, ollama_service):
        """Тест неудачного подключения к Ollama"""
        with patch('aiohttp.ClientSession.get') as mock_get:
            # Мокаем ошибку подключения
            mock_get.side_effect = Exception("Connection failed")
            
            result = await ollama_service.check_connection()
            assert result is False
    
    @pytest.mark.asyncio
    async def test_make_request_success(self, ollama_service):
        """Тест успешного запроса к Ollama"""
        with patch('aiohttp.ClientSession.post') as mock_post:
            # Мокаем успешный ответ
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {
                "response": "Test response from Ollama"
            }
            mock_post.return_value.__aenter__.return_value = mock_response
            
            result = await ollama_service._make_request("Test prompt")
            assert result == "Test response from Ollama"
    
    @pytest.mark.asyncio
    async def test_process_weekly_report(self, ollama_service):
        """Тест обработки еженедельного отчета"""
        # Создаем тестовый отчет
        report = WeeklyReport(
            user_id=123456789,
            username="testuser",
            full_name="Test User",
            week_start=datetime.now(),
            week_end=datetime.now() + timedelta(days=6),
            completed_tasks="Выполнил важные задачи",
            achievements="Достиг поставленных целей",
            next_week_plans="Планирую новые задачи"
        )
        
        with patch.object(ollama_service, '_make_request') as mock_request:
            mock_request.return_value = "Анализ отчета: отличная работа!"
            
            result = await ollama_service.process_weekly_report(report)
            
            assert result is not None
            assert "анализ" in result.lower()
            mock_request.assert_called_once()

class TestTelegramService:
    """Тесты для TelegramService"""
    
    @pytest.fixture
    def telegram_service(self):
        """Создание экземпляра TelegramService"""
        return TelegramService(
            bot_token="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11",
            group_chat_id=-1001234567890,
            thread_id=123
        )
    
    @pytest.fixture
    def mock_bot(self):
        """Мок для Telegram Bot"""
        bot = Mock()
        bot.send_message = AsyncMock()
        bot.send_chat_action = AsyncMock()
        bot.get_chat_member = AsyncMock()
        bot.get_chat_members_count = AsyncMock(return_value=10)
        return bot
    
    @pytest.mark.asyncio
    async def test_send_message_success(self, telegram_service, mock_bot):
        """Тест успешной отправки сообщения"""
        with patch.object(telegram_service, 'bot', mock_bot):
            result = await telegram_service.send_message(
                chat_id=123456789,
                text="Test message"
            )
            
            assert result is True
            mock_bot.send_message.assert_called_once_with(
                chat_id=123456789,
                text="Test message",
                parse_mode=None,
                reply_markup=None
            )
    
    @pytest.mark.asyncio
    async def test_send_message_failure(self, telegram_service, mock_bot):
        """Тест неудачной отправки сообщения"""
        with patch.object(telegram_service, 'bot', mock_bot):
            # Мокаем ошибку отправки
            mock_bot.send_message.side_effect = Exception("Send failed")
            
            result = await telegram_service.send_message(
                chat_id=123456789,
                text="Test message"
            )
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_send_weekly_report(self, telegram_service, mock_bot):
        """Тест отправки еженедельного отчета"""
        # Создаем тестовый отчет
        report = WeeklyReport(
            user_id=123456789,
            username="testuser",
            full_name="Test User",
            week_start=datetime.now(),
            week_end=datetime.now() + timedelta(days=6),
            completed_tasks="Выполнил важные задачи",
            achievements="Достиг поставленных целей",
            next_week_plans="Планирую новые задачи"
        )
        
        with patch.object(telegram_service, 'bot', mock_bot):
            result = await telegram_service.send_weekly_report(report)
            
            assert result is True
            mock_bot.send_message.assert_called_once()
            
            # Проверяем, что сообщение содержит информацию из отчета
            call_args = mock_bot.send_message.call_args
            message_text = call_args[1]['text']
            assert "Test User" in message_text
            assert "Выполнил важные задачи" in message_text
    
    @pytest.mark.asyncio
    async def test_send_reminder(self, telegram_service, mock_bot):
        """Тест отправки напоминания"""
        with patch.object(telegram_service, 'bot', mock_bot):
            result = await telegram_service.send_reminder(
                user_id=123456789,
                username="testuser"
            )
            
            assert result is True
            mock_bot.send_message.assert_called_once()
            
            # Проверяем, что сообщение содержит напоминание
            call_args = mock_bot.send_message.call_args
            message_text = call_args[1]['text']
            assert "напоминание" in message_text.lower() or "отчет" in message_text.lower()
    
    def test_create_report_keyboard(self, telegram_service):
        """Тест создания клавиатуры для отчета"""
        keyboard = telegram_service.create_report_keyboard()
        
        assert keyboard is not None
        # Проверяем, что клавиатура содержит ожидаемые кнопки
        # (детальная проверка зависит от реализации)
    
    def test_create_admin_keyboard(self, telegram_service):
        """Тест создания админской клавиатуры"""
        keyboard = telegram_service.create_admin_keyboard()
        
        assert keyboard is not None
        # Проверяем, что клавиатура содержит ожидаемые кнопки
        # (детальная проверка зависит от реализации)

class TestReportProcessor:
    """Тесты для ReportProcessor"""
    
    @pytest.fixture
    def mock_ollama_service(self):
        """Мок для OllamaService"""
        service = Mock(spec=OllamaService)
        service.process_weekly_report = AsyncMock(return_value="AI analysis")
        service.generate_weekly_summary = AsyncMock(return_value="Weekly summary")
        return service
    
    @pytest.fixture
    def mock_telegram_service(self):
        """Мок для TelegramService"""
        service = Mock(spec=TelegramService)
        service.send_weekly_report = AsyncMock(return_value=True)
        service.send_reminder = AsyncMock(return_value=True)
        service.send_admin_notification = AsyncMock(return_value=True)
        return service
    
    @pytest.fixture
    def report_processor(self, mock_ollama_service, mock_telegram_service):
        """Создание экземпляра ReportProcessor с моками"""
        return ReportProcessor(
            ollama_service=mock_ollama_service,
            telegram_service=mock_telegram_service
        )
    
    @pytest.mark.asyncio
    async def test_save_report(self, report_processor):
        """Тест сохранения отчета"""
        # Создаем тестовый отчет
        report = WeeklyReport(
            user_id=123456789,
            username="testuser",
            full_name="Test User",
            week_start=datetime.now(),
            week_end=datetime.now() + timedelta(days=6),
            completed_tasks="Выполнил важные задачи",
            achievements="Достиг поставленных целей",
            next_week_plans="Планирую новые задачи"
        )
        
        result = await report_processor.save_report(report)
        
        # Проверяем, что отчет сохранен
        assert result is True
        
        # Проверяем, что отчет добавлен в хранилище
        assert len(report_processor.reports) > 0
        saved_report = report_processor.reports[0]
        assert saved_report.user_id == 123456789
        assert saved_report.status == "submitted"
    
    @pytest.mark.asyncio
    async def test_get_current_week_report(self, report_processor):
        """Тест получения отчета за текущую неделю"""
        # Создаем и сохраняем тестовый отчет
        report = WeeklyReport(
            user_id=123456789,
            username="testuser",
            full_name="Test User",
            week_start=datetime.now(),
            week_end=datetime.now() + timedelta(days=6),
            completed_tasks="Выполнил важные задачи",
            achievements="Достиг поставленных целей",
            next_week_plans="Планирую новые задачи"
        )
        
        await report_processor.save_report(report)
        
        # Получаем отчет за текущую неделю
        found_report = await report_processor.get_current_week_report(123456789)
        
        assert found_report is not None
        assert found_report.user_id == 123456789
    
    @pytest.mark.asyncio
    async def test_get_statistics(self, report_processor):
        """Тест получения статистики"""
        # Создаем несколько тестовых отчетов
        for i in range(3):
            report = WeeklyReport(
                user_id=123456789 + i,
                username=f"testuser{i}",
                full_name=f"Test User {i}",
                week_start=datetime.now(),
                week_end=datetime.now() + timedelta(days=6),
                completed_tasks="Выполнил важные задачи",
                achievements="Достиг поставленных целей",
                next_week_plans="Планирую новые задачи"
            )
            await report_processor.save_report(report)
        
        stats = await report_processor.get_statistics()
        
        assert stats is not None
        assert 'total_reports' in stats
        assert 'total_users' in stats
        assert stats['total_reports'] >= 3
    
    @pytest.mark.asyncio
    async def test_send_reminders(self, report_processor, mock_telegram_service):
        """Тест отправки напоминаний"""
        # Добавляем тестового сотрудника
        employee = Employee(
            user_id=123456789,
            username="testuser",
            full_name="Test User",
            department="IT",
            position="Developer"
        )
        report_processor.employees.append(employee)
        
        result = await report_processor.send_reminder_to_all()
        
        assert result is True
        # Проверяем, что напоминание отправлено
        mock_telegram_service.send_reminder.assert_called()
    
    @pytest.mark.asyncio
    async def test_add_employee(self, report_processor):
        """Тест добавления сотрудника"""
        employee_data = {
            'user_id': 123456789,
            'username': 'testuser',
            'full_name': 'Test User',
            'department': 'IT',
            'position': 'Developer'
        }
        
        result = await report_processor.add_employee(employee_data)
        
        assert result is True
        assert len(report_processor.employees) > 0
        
        added_employee = report_processor.employees[0]
        assert added_employee.user_id == 123456789
        assert added_employee.full_name == "Test User"
    
    @pytest.mark.asyncio
    async def test_export_reports(self, report_processor):
        """Тест экспорта отчетов"""
        # Создаем тестовый отчет
        report = WeeklyReport(
            user_id=123456789,
            username="testuser",
            full_name="Test User",
            week_start=datetime.now(),
            week_end=datetime.now() + timedelta(days=6),
            completed_tasks="Выполнил важные задачи",
            achievements="Достиг поставленных целей",
            next_week_plans="Планирую новые задачи"
        )
        
        await report_processor.save_report(report)
        
        # Экспортируем отчеты
        exported_data = await report_processor.export_reports()
        
        assert exported_data is not None
        assert len(exported_data) > 0
        
        # Проверяем формат экспортированных данных
        first_report = exported_data[0]
        assert 'user_id' in first_report
        assert 'full_name' in first_report
        assert 'completed_tasks' in first_report

class TestIntegrationServices:
    """Интеграционные тесты для сервисов"""
    
    @pytest.mark.asyncio
    async def test_full_report_processing_flow(self):
        """Тест полного потока обработки отчета"""
        # Создаем реальные сервисы (с моками для внешних зависимостей)
        ollama_service = Mock(spec=OllamaService)
        ollama_service.process_weekly_report = AsyncMock(return_value="AI analysis")
        
        telegram_service = Mock(spec=TelegramService)
        telegram_service.send_weekly_report = AsyncMock(return_value=True)
        telegram_service.send_admin_notification = AsyncMock(return_value=True)
        
        report_processor = ReportProcessor(
            ollama_service=ollama_service,
            telegram_service=telegram_service
        )
        
        # Создаем отчет
        report = WeeklyReport(
            user_id=123456789,
            username="testuser",
            full_name="Test User",
            week_start=datetime.now(),
            week_end=datetime.now() + timedelta(days=6),
            completed_tasks="Выполнил важные задачи по разработке системы",
            achievements="Успешно завершил проект и получил положительные отзывы",
            next_week_plans="Планирую начать работу над новым модулем системы"
        )
        
        # Сохраняем отчет
        save_result = await report_processor.save_report(report)
        assert save_result is True
        
        # Проверяем, что отчет обработан ИИ
        ollama_service.process_weekly_report.assert_called_once()
        
        # Проверяем, что отчет отправлен в группу
        telegram_service.send_weekly_report.assert_called_once()
        
        # Проверяем, что администраторы уведомлены
        telegram_service.send_admin_notification.assert_called()
    
    @pytest.mark.asyncio
    async def test_reminder_system(self):
        """Тест системы напоминаний"""
        telegram_service = Mock(spec=TelegramService)
        telegram_service.send_reminder = AsyncMock(return_value=True)
        
        report_processor = ReportProcessor(
            ollama_service=Mock(),
            telegram_service=telegram_service
        )
        
        # Добавляем сотрудников
        employees_data = [
            {
                'user_id': 123456789,
                'username': 'user1',
                'full_name': 'User One',
                'department': 'IT'
            },
            {
                'user_id': 987654321,
                'username': 'user2',
                'full_name': 'User Two',
                'department': 'HR'
            }
        ]
        
        for emp_data in employees_data:
            await report_processor.add_employee(emp_data)
        
        # Отправляем напоминания
        result = await report_processor.send_reminder_to_all()
        
        assert result is True
        # Проверяем, что напоминания отправлены всем сотрудникам
        assert telegram_service.send_reminder.call_count == len(employees_data)

if __name__ == "__main__":
    pytest.main([__file__])