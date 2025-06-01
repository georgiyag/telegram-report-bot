"""Модели для отделов и сотрудников"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class Department(BaseModel):
    """Модель отдела"""
    id: Optional[int] = Field(None, description="ID отдела в базе данных")
    name: str = Field(..., description="Название отдела")
    code: str = Field(..., description="Код отдела")
    description: Optional[str] = Field(None, description="Описание отдела")
    head_name: Optional[str] = Field(None, description="ФИО руководителя")
    report_required: bool = Field(True, description="Требуется ли отчет от отдела")
    report_deadline_day: int = Field(5, description="День недели дедлайна (0-6, где 0=понедельник)")
    report_deadline_hour: int = Field(18, description="Час дедлайна (0-23)")
    created_at: Optional[datetime] = Field(None, description="Дата создания")
    updated_at: Optional[datetime] = Field(None, description="Дата обновления")
    employees: List['Employee'] = Field(default_factory=list, description="Список сотрудников")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "IT отдел",
                "code": "IT",
                "description": "Отдел информационных технологий",
                "head_name": "Петров Петр Петрович",
                "report_required": True,
                "report_deadline_day": 5,
                "report_deadline_hour": 18,
                "employees": []
            }
        }

class Employee(BaseModel):
    """Модель сотрудника"""
    id: Optional[int] = Field(None, description="ID сотрудника в базе данных")
    user_id: int = Field(..., description="ID пользователя в Telegram")
    username: Optional[str] = Field(None, description="Username в Telegram")
    full_name: str = Field(..., description="Полное имя сотрудника")
    department_code: str = Field(..., description="Код отдела")
    department_name: Optional[str] = Field(None, description="Название отдела")
    position: Optional[str] = Field(None, description="Должность")
    employee_id: Optional[str] = Field(None, description="Табельный номер")
    email: Optional[str] = Field(None, description="Email сотрудника")
    phone: Optional[str] = Field(None, description="Телефон сотрудника")
    is_active: bool = Field(True, description="Активен ли сотрудник")
    is_blocked: bool = Field(False, description="Заблокирован ли сотрудник")
    created_at: Optional[datetime] = Field(None, description="Дата создания")
    updated_at: Optional[datetime] = Field(None, description="Дата обновления")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 123456789,
                "username": "john_doe",
                "full_name": "Иванов Иван Иванович",
                "department_code": "IT",
                "department_name": "IT отдел",
                "position": "Программист",
                "employee_id": "EMP001",
                "email": "ivanov@company.com",
                "phone": "+7-900-123-45-67",
                "is_active": True,
                "is_blocked": False
            }
        }