from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, Field

class WeeklyReport(BaseModel):
    """Модель еженедельного отчета"""
    id: Optional[int] = Field(None, description="ID отчета в базе данных")
    user_id: int = Field(..., description="ID пользователя в Telegram")
    username: Optional[str] = Field(None, description="Username пользователя")
    full_name: str = Field(..., description="Полное имя сотрудника")
    week_start: datetime = Field(..., description="Начало недели")
    week_end: datetime = Field(..., description="Конец недели")
    
    # Основные поля отчета
    completed_tasks: str = Field(..., description="Выполненные задачи")
    achievements: Optional[str] = Field(None, description="Достижения")
    problems: Optional[str] = Field(None, description="Проблемы и трудности")
    next_week_plans: Optional[str] = Field(None, description="Планы на следующую неделю")
    
    # Дополнительная информация
    department: Optional[str] = Field(None, description="Отдел")
    position: Optional[str] = Field(None, description="Должность")
    submitted_at: Optional[datetime] = Field(None, description="Время подачи отчета")
    is_late: bool = Field(False, description="Опоздал ли с подачей отчета")
    

    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        json_schema_extra = {
            "example": {
                "user_id": 123456789,
                "username": "john_doe",
                "full_name": "Иванов Иван Иванович",
                "week_start": "2024-01-15T00:00:00",
                "week_end": "2024-01-21T23:59:59",
                "completed_tasks": "1. Выполнил задачу A\n2. Завершил проект B",
                "achievements": "Превысил план на 15%",
                "problems": "Задержка поставки материалов",
                "next_week_plans": "1. Начать новый проект\n2. Провести встречу с клиентом",
                "department": "IT отдел",
                "position": "Разработчик"
            }
        }