"""
Модуль для сбора обратной связи (feedback) для дообучения ML моделей.
Собирает данные для TaskLoad и TaskPriority.
"""

from datetime import datetime
from local_db.data_manager import (
    insert_ml_feedback_taskload,
    insert_ml_feedback_taskpriority,
    select_capacity_parametrs,
    get_unsynced_ml_feedback_taskload,
    get_unsynced_ml_feedback_taskpriority,
    mark_ml_feedback_taskload_synced,
    mark_ml_feedback_taskpriority_synced,
    get_ml_feedback_stats
)
from ml.load import calculate_working_hours, predict_capacity


class FeedbackCollector:
    """
    Класс для сбора и управления обратной связью пользователя.
    """
    
    @staticmethod
    def submit_workload_feedback(workload_rating: int):
        """
        Сохраняет обратную связь для дообучения модели TaskLoad.
        
        Args:
            workload_rating: оценка пользователя от 0 до 100
            
        Хранит:
        - predicted_workload: предсказание модели (0-100)
        - actual_workload: оценка пользователя (0-100)
        """
        if not 0 <= workload_rating <= 100:
            raise ValueError("workload_rating должен быть от 0 до 100")
        
        # Получаем текущие параметры из БД
        active_tasks, avg_priority, max_priority, avg_hours_to_deadline, overdue_tasks = select_capacity_parametrs()
        
        # Получаем предсказание модели (то что показывает круговой график)
        predicted_workload = predict_capacity(
            active_tasks=active_tasks,
            avg_priority=avg_priority if avg_priority else 0,
            max_priority=max_priority if max_priority else 0,
            avg_hours_to_deadline=avg_hours_to_deadline if avg_hours_to_deadline else 0,
            overdue_tasks=overdue_tasks
        )
        
        # Сохраняем feedback с обоими значениями (без конвертации)
        insert_ml_feedback_taskload(
            active_tasks=active_tasks,
            avg_priority=avg_priority if avg_priority else 0,
            max_priority=max_priority if max_priority else 0,
            avg_hours_to_deadline=avg_hours_to_deadline if avg_hours_to_deadline else 0,
            overdue_tasks=overdue_tasks,
            predicted_workload=predicted_workload,
            actual_workload=workload_rating  #直接使用 0-100
        )
    
    @staticmethod
    def submit_task_priority_feedback(task_id: str, task_type: str, deadline: datetime, 
                                       urgency: int, user_priority: str):
        """
        Сохраняет данные о задаче где пользователь вручную выставил приоритет.
        
        Args:
            task_id: ID задачи
            task_type: тип задачи (строка)
            deadline: дедлайн задачи
            urgency: срочность (0-10)
            user_priority: приоритет который выбрал пользователь (Casual/Low/Mid/High/Extreme)
        """
        # Вычисляем часы до дедлайна
        hours_left = calculate_working_hours(deadline.strftime("%Y-%m-%d"))
        
        # Сохраняем feedback
        insert_ml_feedback_taskpriority(
            task_id=task_id,
            task_type=task_type,
            hours_left=hours_left,
            urgency=urgency,
            user_priority=user_priority
        )
    
    @staticmethod
    def get_feedback_stats():
        """
        Возвращает статистику по feedback записям.
        
        Returns:
            dict с полями:
                taskload_total, taskload_unsynced,
                taskpriority_total, taskpriority_unsynced
        """
        return get_ml_feedback_stats()
    
    @staticmethod
    def get_unsynced_feedback_for_upload():
        """
        Возвращает все несинхронизированные записи для отправки на сервер.
        
        Returns:
            dict с полями:
                taskload: список словарей с данными
                taskpriority: список словарей с данными
        """
        taskload_records = get_unsynced_ml_feedback_taskload()
        taskpriority_records = get_unsynced_ml_feedback_taskpriority()
        
        taskload_data = [
            {
                "id": record.id,
                "timestamp": record.timestamp.isoformat(),
                "workload": record.workload,
                "active_tasks": record.active_tasks,
                "avg_priority": record.avg_priority,
                "max_priority": record.max_priority,
                "avg_hours_to_deadline": record.avg_hours_to_deadline,
                "overdue_tasks": record.overdue_tasks
            }
            for record in taskload_records
        ]
        
        taskpriority_data = [
            {
                "id": record.id,
                "timestamp": record.timestamp.isoformat(),
                "task_id": record.task_id,
                "task_type": record.task_type,
                "hours_left": record.hours_left,
                "urgency": record.urgency,
                "user_priority": record.user_priority
            }
            for record in taskpriority_records
        ]
        
        return {
            "taskload": taskload_data,
            "taskpriority": taskpriority_data
        }
    
    @staticmethod
    def mark_feedback_as_synced(taskload_ids=None, taskpriority_ids=None):
        """
        Отмечает записи как синхронизированные после успешной отправки на сервер.
        
        Args:
            taskload_ids: список ID записей TaskLoad
            taskpriority_ids: список ID записей TaskPriority
        """
        if taskload_ids:
            mark_ml_feedback_taskload_synced(taskload_ids)
        
        if taskpriority_ids:
            mark_ml_feedback_taskpriority_synced(taskpriority_ids)
