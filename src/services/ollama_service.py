import aiohttp
import asyncio
from typing import Optional, Dict, Any
from loguru import logger

from config import settings
from models.report import WeeklyReport

class OllamaService:
    """Сервис для работы с Ollama API"""
    
    def __init__(self):
        self.base_url = settings.ollama_url
        self.model = settings.ollama_model
        self.timeout = aiohttp.ClientTimeout(total=120)  # 2 минуты таймаут
    
    async def _make_request(self, prompt: str) -> Optional[str]:
        """Выполнение запроса к Ollama API"""
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                payload = {
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "max_tokens": 1000
                    }
                }
                
                logger.info(f"Отправка запроса к Ollama: {self.base_url}/api/generate")
                
                async with session.post(
                    f"{self.base_url}/api/generate",
                    json=payload
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get('response', '').strip()
                    else:
                        logger.error(f"Ошибка Ollama API: {response.status} - {await response.text()}")
                        return None
                        
        except asyncio.TimeoutError:
            logger.error("Таймаут при обращении к Ollama API")
            return None
        except aiohttp.ClientError as e:
            logger.error(f"Ошибка соединения с Ollama: {e}")
            return None
        except Exception as e:
            logger.error(f"Неожиданная ошибка при работе с Ollama: {e}")
            return None
    
    async def check_connection(self) -> bool:
        """Проверка доступности Ollama API"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(f"{self.base_url}/api/tags") as response:
                    if response.status == 200:
                        logger.info("Соединение с Ollama установлено")
                        return True
                    else:
                        logger.warning(f"Ollama недоступен: {response.status}")
                        return False
        except Exception as e:
            logger.warning(f"Не удалось подключиться к Ollama: {e}")
            return False
    
    async def process_report(self, report: WeeklyReport) -> WeeklyReport:
        """Обработка отчета через Ollama"""
        logger.info(f"Начало обработки отчета пользователя {report.user_id}")
        
        # Создаем промпт для анализа отчета
        analysis_prompt = self._create_analysis_prompt(report)
        
        # Получаем анализ от ИИ
        ai_analysis = await self._make_request(analysis_prompt)
        
        if ai_analysis:
            # Создаем промпт для краткой сводки
            summary_prompt = self._create_summary_prompt(report)
            ai_summary = await self._make_request(summary_prompt)
            
            # Обновляем отчет
            report.mark_as_processed(
                summary=ai_summary or "Краткая сводка недоступна",
                analysis=ai_analysis
            )
            
            logger.info(f"Отчет пользователя {report.user_id} успешно обработан")
        else:
            logger.warning(f"Не удалось обработать отчет пользователя {report.user_id}")
            # Отмечаем как обработанный даже без ИИ анализа
            report.mark_as_processed(
                summary="Автоматическая обработка недоступна",
                analysis="Анализ временно недоступен"
            )
        
        return report
    
    def _create_analysis_prompt(self, report: WeeklyReport) -> str:
        """Создание промпта для анализа отчета"""
        return f"""Проанализируй еженедельный отчет сотрудника предприятия АО ЭМЗ "ФИРМА СЭЛМА".

Информация о сотруднике:
- ФИО: {report.full_name}
- Отдел: {report.department or 'Не указан'}
- Должность: {report.position or 'Не указана'}
- Период: {report.get_week_string()}

Выполненные задачи:
{report.completed_tasks}

Достижения:
{report.achievements}

Проблемы:
{report.problems}

Планы на следующую неделю:
{report.next_week_plans}

Пожалуйста, проведи анализ отчета и предоставь:
1. Оценку продуктивности сотрудника (высокая/средняя/низкая)
2. Ключевые достижения
3. Выявленные проблемы и рекомендации по их решению
4. Оценку реалистичности планов на следующую неделю
5. Общие рекомендации для сотрудника

Ответ должен быть структурированным, профессиональным и конструктивным. Объем ответа - не более 500 слов."""
    
    def _create_summary_prompt(self, report: WeeklyReport) -> str:
        """Создание промпта для краткой сводки"""
        return f"""Создай краткую сводку еженедельного отчета сотрудника для руководства.

Отчет сотрудника {report.full_name} ({report.department or 'отдел не указан'}) за {report.get_week_string()}:

Выполненные задачи:
{report.completed_tasks}

Достижения:
{report.achievements}

Проблемы:
{report.problems}

Планы на следующую неделю:
{report.next_week_plans}

Создай краткую сводку (не более 200 слов), которая включает:
1. Основные выполненные задачи
2. Ключевые достижения
3. Критические проблемы (если есть)
4. Главные планы на следующую неделю

Сводка должна быть информативной и подходящей для руководства."""
    
    async def generate_weekly_summary(self, reports: list[WeeklyReport]) -> str:
        """Генерация общей сводки по всем отчетам за неделю"""
        if not reports:
            return "Отчеты за неделю отсутствуют."
        
        # Подготавливаем данные для анализа
        reports_data = []
        for report in reports:
            reports_data.append(f"""
Сотрудник: {report.full_name} ({report.department or 'отдел не указан'})
Задачи: {report.completed_tasks[:200]}...
Достижения: {report.achievements[:100]}...
Проблемы: {report.problems[:100]}...
""")
        
        prompt = f"""Проанализируй еженедельные отчеты сотрудников АО ЭМЗ "ФИРМА СЭЛМА" и создай общую сводку для руководства.

Отчеты ({len(reports)} шт.):
{''.join(reports_data[:10])}  # Ограничиваем количество для промпта

Создай общую сводку, включающую:
1. Общую статистику (количество отчетов, отделы)
2. Основные достижения компании за неделю
3. Выявленные проблемы и риски
4. Рекомендации для руководства
5. Прогноз на следующую неделю

Объем сводки - не более 400 слов. Стиль - деловой, структурированный."""
        
        result = await self._make_request(prompt)
        return result or "Не удалось сгенерировать общую сводку."
    
    async def analyze_employee_performance(self, reports: list[WeeklyReport], user_id: int) -> str:
        """Анализ производительности конкретного сотрудника за период"""
        user_reports = [r for r in reports if r.user_id == user_id]
        
        if not user_reports:
            return "Отчеты сотрудника не найдены."
        
        # Сортируем по дате
        user_reports.sort(key=lambda x: x.week_start)
        
        reports_summary = []
        for i, report in enumerate(user_reports[-4:], 1):  # Последние 4 недели
            reports_summary.append(f"""
Неделя {i} ({report.get_week_string()}):
Задачи: {report.completed_tasks[:150]}...
Достижения: {report.achievements[:100]}...
Проблемы: {report.problems[:100]}...
""")
        
        prompt = f"""Проанализируй динамику работы сотрудника {user_reports[0].full_name} за последние недели.

Отчеты сотрудника:
{''.join(reports_summary)}

Проведи анализ и предоставь:
1. Динамику производительности (растет/стабильна/снижается)
2. Сильные стороны сотрудника
3. Области для улучшения
4. Повторяющиеся проблемы
5. Рекомендации для развития

Объем анализа - не более 300 слов."""
        
        result = await self._make_request(prompt)
        return result or "Не удалось проанализировать производительность сотрудника."
    
    async def suggest_improvements(self, report: WeeklyReport) -> str:
        """Предложения по улучшению для сотрудника"""
        prompt = f"""На основе отчета сотрудника {report.full_name}, предложи конкретные рекомендации для повышения эффективности работы.

Текущий отчет:
Задачи: {report.completed_tasks}
Проблемы: {report.problems}
Планы: {report.next_week_plans}

Предоставь:
1. 3-5 конкретных рекомендаций для улучшения работы
2. Предложения по решению выявленных проблем
3. Советы по планированию задач
4. Рекомендации по профессиональному развитию

Ответ должен быть конструктивным и практичным. Объем - не более 250 слов."""
        
        result = await self._make_request(prompt)
        return result or "Рекомендации временно недоступны."
    
    async def close(self):
        """Метод для корректного завершения работы сервиса"""
        # В текущей реализации нет постоянных соединений для закрытия
        # Метод добавлен для совместимости с shutdown процедурой
        pass