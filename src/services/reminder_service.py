# -*- coding: utf-8 -*-
"""
Сервис автоматических напоминаний о еженедельных отчетах.
АО ЭМЗ "ФИРМА СЭЛМА"

Автор: Telegram Report Bot
Версия: 1.0.0
"""

import asyncio
from datetime import datetime, date, time, timedelta
from typing import List, Optional

from loguru import logger

from database import DatabaseManager
from services.telegram_service import TelegramService
from models.department import Employee
from config import settings


class ReminderService:
    """Сервис для автоматических напоминаний"""
    
    def __init__(self, db_manager: DatabaseManager, telegram_service: TelegramService):
        self.db_manager = db_manager
        self.telegram_service = telegram_service
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Запуск сервиса напоминаний"""
        if self.is_running:
            logger.warning("Сервис напоминаний уже запущен")
            return
        
        self.is_running = True
        self._task = asyncio.create_task(self._reminder_loop())
        logger.info("Сервис автоматических напоминаний запущен")
    
    async def stop(self):
        """Остановка сервиса напоминаний"""
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Сервис автоматических напоминаний остановлен")
    
    async def _reminder_loop(self):
        """Основной цикл проверки напоминаний"""
        while self.is_running:
            try:
                await self._check_and_send_reminders()
                # Проверяем каждые 30 минут
                await asyncio.sleep(1800)
            except asyncio.CancelledError:
                logger.info("Цикл напоминаний остановлен")
                break
            except Exception as e:
                logger.error(f"Ошибка в цикле напоминаний: {e}")
                await asyncio.sleep(300)  # Ждем 5 минут при ошибке
    
    async def _check_and_send_reminders(self):
        """Проверка и отправка напоминаний"""
        now = datetime.now()
        current_date = now.date()
        current_time = now.time()
        
        # Получаем начало текущей недели (понедельник)
        week_start = current_date - timedelta(days=current_date.weekday())
        
        # Проверяем, нужно ли отправлять напоминания
        should_send = await self._should_send_reminders(current_date, current_time)
        
        if should_send:
            logger.info("Отправка автоматических напоминаний")
            await self._send_automatic_reminders(week_start)
    
    async def _should_send_reminders(self, current_date: date, current_time: time) -> bool:
        """Определяет, нужно ли отправлять напоминания сейчас"""
        # Отправляем напоминания в среду в 14:00
        wednesday_reminder = (
            current_date.weekday() == 2 and  # Среда
            current_time.hour == 14 and
            current_time.minute < 30
        )
        
        # Отправляем напоминания в пятницу в 16:00 (за 2 часа до дедлайна)
        friday_reminder = (
            current_date.weekday() == 4 and  # Пятница
            current_time.hour == 16 and
            current_time.minute < 30
        )
        
        return wednesday_reminder or friday_reminder
    
    async def _send_automatic_reminders(self, week_start: date):
        """Отправка автоматических напоминаний"""
        try:
            # Получаем список сотрудников без отчетов
            missing_users = await self.db_manager.get_missing_reports_users(week_start)
            
            if not missing_users:
                logger.info("Все сотрудники уже сдали отчеты")
                return
            
            # Отправляем напоминания
            results = await self.telegram_service.send_bulk_reminders(missing_users)
            sent_count = results.get('sent', 0)
            failed_count = results.get('failed', 0)
            
            logger.info(f"Автоматические напоминания отправлены: {sent_count} успешно, {failed_count} ошибок")
            
            # Уведомляем администраторов
            admin_message = (
                f"🤖 <b>Автоматические напоминания отправлены</b>\n\n"
                f"📊 Статистика:\n"
                f"• Всего без отчетов: {len(missing_users)}\n"
                f"• Напоминания отправлены: {sent_count}\n"
                f"• Ошибки отправки: {failed_count}\n\n"
                f"📅 Неделя: {week_start.strftime('%d.%m.%Y')}"
            )
            
            # Получаем список администраторов
            admin_ids = await self._get_admin_ids()
            if admin_ids:
                await self.telegram_service.send_admin_notification(admin_ids, admin_message)
            
        except Exception as e:
            logger.error(f"Ошибка отправки автоматических напоминаний: {e}")
            
            # Уведомляем администраторов об ошибке
            error_message = (
                f"❌ <b>Ошибка автоматических напоминаний</b>\n\n"
                f"Произошла ошибка при отправке автоматических напоминаний:\n"
                f"<code>{str(e)}</code>\n\n"
                f"Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
            )
            
            admin_ids = await self._get_admin_ids()
            if admin_ids:
                await self.telegram_service.send_admin_notification(admin_ids, error_message)
    
    async def _get_admin_ids(self) -> List[int]:
        """Получение списка ID администраторов"""
        try:
            employees = await self.db_manager.get_employees()
            admin_ids = [emp.user_id for emp in employees if emp.is_admin and emp.is_active]
            return admin_ids
        except Exception as e:
            logger.error(f"Ошибка получения списка администраторов: {e}")
            return []
    
    async def send_manual_reminder(self, target_type: str, target_value: str = None) -> dict:
        """Отправка ручного напоминания"""
        try:
            week_start = date.today() - timedelta(days=date.today().weekday())
            
            if target_type == "all":
                # Всем активным сотрудникам
                employees = await self.db_manager.get_employees()
                target_users = [emp for emp in employees if emp.is_active and not emp.is_blocked]
                
            elif target_type == "missing":
                # Только тем, кто не сдал отчет
                target_users = await self.db_manager.get_missing_reports_users(week_start)
                
            elif target_type == "department":
                # Конкретному отделу
                if not target_value:
                    return {"success": False, "error": "Не указан код отдела"}
                target_users = await self.db_manager.get_employees_by_department(target_value)
                target_users = [emp for emp in target_users if emp.is_active and not emp.is_blocked]
                
            else:
                return {"success": False, "error": "Неизвестный тип цели"}
            
            if not target_users:
                return {"success": True, "sent": 0, "failed": 0, "message": "Нет пользователей для отправки"}
            
            # Отправляем напоминания
            results = await self.telegram_service.send_bulk_reminders(target_users)
            
            return {
                "success": True,
                "sent": results.get('sent', 0),
                "failed": results.get('failed', 0),
                "total": len(target_users)
            }
            
        except Exception as e:
            logger.error(f"Ошибка отправки ручного напоминания: {e}")
            return {"success": False, "error": str(e)}