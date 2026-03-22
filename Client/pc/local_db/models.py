from sqlalchemy import (
    Column, Integer, String, DateTime, Date, ForeignKey, CheckConstraint, Float, Boolean
)
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime, timezone
import uuid

Base = declarative_base()

class TaskType(Base):
    __tablename__ = "task_types"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)

    tasks = relationship("Task", back_populates="task_type")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)
    description = Column(String)
    task_type_id = Column(Integer, ForeignKey("task_types.id"))
    personal_priority = Column(Integer, CheckConstraint("personal_priority BETWEEN 0 AND 10"))
    influence = Column(Integer, CheckConstraint("influence BETWEEN 0 AND 10"))
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
    deadline = Column(DateTime, nullable=False)
    final_priority = Column(
        String, CheckConstraint("final_priority IN ('Casual','Low','Mid','High','Extreme')")
    )
    status = Column(
        String, CheckConstraint("status IN ('underway','completed','overdue','cancelled')"), default='underway'
    )

    task_type = relationship("TaskType", back_populates="tasks")


class DailyStats(Base):
    __tablename__ = "daily_stats"

    date = Column(Date, primary_key=True)
    total_tasks = Column(Integer)
    completed_tasks = Column(Integer)
    overdue_tasks = Column(Integer)
    in_progress_tasks = Column(Integer)


class MLFeedbackTaskLoad(Base):
    __tablename__ = "ml_feedback_taskload"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.now(timezone.utc))
    
    active_tasks = Column(Integer)
    avg_priority = Column(Float)
    max_priority = Column(Float)
    avg_hours_to_deadline = Column(Float)
    overdue_tasks = Column(Integer)
    
    predicted_workload = Column(Integer, CheckConstraint("predicted_workload BETWEEN 0 AND 100"))
    
    actual_workload = Column(Integer, CheckConstraint("actual_workload BETWEEN 0 AND 100"))
    
    is_synced = Column(Boolean, default=False)


class MLFeedbackTaskPriority(Base):
    __tablename__ = "ml_feedback_taskpriority"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.now(timezone.utc))
    
    task_id = Column(String(36))
    task_type = Column(String)
    hours_left = Column(Float)
    urgency = Column(Integer)
    user_priority = Column(String)
    
    is_synced = Column(Boolean, default=False)



