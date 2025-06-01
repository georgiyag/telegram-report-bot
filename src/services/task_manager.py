# -*- coding: utf-8 -*-
"""
Сервис для управления фоновыми задачами обработки отчетов.
Обеспечивает асинхронную обработку без блокировки основного потока бота.

Автор: Telegram Report Bot
Версия: 1.0.0
"""

import asyncio
import uuid
from datetime import datetime
from enum import Enum
from typing import Dict, Optional, Callable, Any
from dataclasses import dataclass

from loguru import logger


class TaskStatus(Enum):
    """Статусы задач"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TaskInfo:
    """Информация о задаче"""
    task_id: str
    user_id: int
    status: TaskStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    progress_message: Optional[str] = None


class TaskManager:
    """Менеджер фоновых задач"""
    
    def __init__(self):
        self.tasks: Dict[str, TaskInfo] = {}
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.user_tasks: Dict[int, str] = {}  # user_id -> task_id
        self.progress_callbacks: Dict[str, Callable] = {}
        
    def create_task(self, user_id: int, coro, progress_callback: Optional[Callable] = None) -> str:
        """Создание новой задачи"""
        task_id = str(uuid.uuid4())
        
        # Отменяем предыдущую задачу пользователя, если есть
        if user_id in self.user_tasks:
            old_task_id = self.user_tasks[user_id]
            self.cancel_task(old_task_id)
        
        # Создаем информацию о задаче
        task_info = TaskInfo(
            task_id=task_id,
            user_id=user_id,
            status=TaskStatus.PENDING,
            created_at=datetime.now()
        )
        
        self.tasks[task_id] = task_info
        self.user_tasks[user_id] = task_id
        
        if progress_callback:
            self.progress_callbacks[task_id] = progress_callback
        
        # Создаем и запускаем asyncio задачу
        async_task = asyncio.create_task(self._run_task(task_id, coro))
        self.running_tasks[task_id] = async_task
        
        logger.info(f"Создана задача {task_id} для пользователя {user_id}")
        return task_id
    
    async def _run_task(self, task_id: str, coro) -> Any:
        """Выполнение задачи"""
        task_info = self.tasks[task_id]
        
        try:
            # Обновляем статус на "выполняется"
            task_info.status = TaskStatus.RUNNING
            task_info.started_at = datetime.now()
            
            logger.info(f"Запуск задачи {task_id}")
            
            # Выполняем задачу
            result = await coro
            
            # Обновляем статус на "завершена"
            task_info.status = TaskStatus.COMPLETED
            task_info.completed_at = datetime.now()
            task_info.result = result
            
            logger.success(f"Задача {task_id} успешно завершена")
            return result
            
        except asyncio.CancelledError:
            task_info.status = TaskStatus.CANCELLED
            task_info.completed_at = datetime.now()
            logger.warning(f"Задача {task_id} была отменена")
            raise
            
        except Exception as e:
            task_info.status = TaskStatus.FAILED
            task_info.completed_at = datetime.now()
            task_info.error = str(e)
            logger.error(f"Ошибка в задаче {task_id}: {e}")
            raise
            
        finally:
            # Очищаем ссылки
            if task_id in self.running_tasks:
                del self.running_tasks[task_id]
            
            # Вызываем callback прогресса с финальным статусом
            if task_id in self.progress_callbacks:
                try:
                    await self.progress_callbacks[task_id](task_info)
                except Exception as e:
                    logger.error(f"Ошибка в progress_callback для задачи {task_id}: {e}")
                del self.progress_callbacks[task_id]
    
    def get_task_info(self, task_id: str) -> Optional[TaskInfo]:
        """Получение информации о задаче"""
        return self.tasks.get(task_id)
    
    def get_user_task(self, user_id: int) -> Optional[TaskInfo]:
        """Получение текущей задачи пользователя"""
        if user_id in self.user_tasks:
            task_id = self.user_tasks[user_id]
            return self.tasks.get(task_id)
        return None
    
    def cancel_task(self, task_id: str) -> bool:
        """Отмена задачи"""
        if task_id in self.running_tasks:
            async_task = self.running_tasks[task_id]
            async_task.cancel()
            logger.info(f"Задача {task_id} отменена")
            return True
        return False
    
    def cancel_user_task(self, user_id: int) -> bool:
        """Отмена текущей задачи пользователя"""
        if user_id in self.user_tasks:
            task_id = self.user_tasks[user_id]
            return self.cancel_task(task_id)
        return False
    
    async def update_progress(self, task_id: str, message: str):
        """Обновление прогресса задачи"""
        if task_id in self.tasks:
            self.tasks[task_id].progress_message = message
            
            # Вызываем callback прогресса
            if task_id in self.progress_callbacks:
                try:
                    await self.progress_callbacks[task_id](self.tasks[task_id])
                except Exception as e:
                    logger.error(f"Ошибка в progress_callback для задачи {task_id}: {e}")
    
    def cleanup_completed_tasks(self, max_age_hours: int = 24):
        """Очистка завершенных задач старше указанного времени"""
        current_time = datetime.now()
        tasks_to_remove = []
        
        for task_id, task_info in self.tasks.items():
            if (task_info.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED] and
                task_info.completed_at and
                (current_time - task_info.completed_at).total_seconds() > max_age_hours * 3600):
                tasks_to_remove.append(task_id)
        
        for task_id in tasks_to_remove:
            del self.tasks[task_id]
            # Удаляем из user_tasks если это текущая задача пользователя
            user_id = None
            for uid, tid in self.user_tasks.items():
                if tid == task_id:
                    user_id = uid
                    break
            if user_id:
                del self.user_tasks[user_id]
        
        if tasks_to_remove:
            logger.info(f"Очищено {len(tasks_to_remove)} завершенных задач")
    
    def get_stats(self) -> Dict[str, int]:
        """Получение статистики задач"""
        stats = {
            "total": len(self.tasks),
            "pending": 0,
            "running": 0,
            "completed": 0,
            "failed": 0,
            "cancelled": 0
        }
        
        for task_info in self.tasks.values():
            stats[task_info.status.value] += 1
        
        return stats