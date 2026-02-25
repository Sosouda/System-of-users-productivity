import uuid
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Boolean, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    tasks = relationship("Task", back_populates="owner")


class TaskType(Base):
    __tablename__ = "task_types"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)

    tasks = relationship("Task", back_populates="task_type")


class DailyStats(Base):
    __tablename__ = "daily_stats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    date = Column(Date, nullable=False)
    total_tasks = Column(Integer, default=0)
    completed_tasks = Column(Integer, default=0)
    overdue_tasks = Column(Integer, default=0)
    in_progress_tasks = Column(Integer, default=0)

    owner = relationship("User")

class Task(Base):
    __tablename__ = "tasks"

    id = Column(String(36), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    title = Column(String, nullable=False)
    description = Column(String)
    task_type_id = Column(Integer, ForeignKey("task_types.id"))

    personal_priority = Column(Integer)
    influence = Column(Integer)

    created_at = Column(DateTime)
    deadline = Column(DateTime)

    final_priority = Column(String)
    status = Column(String)

    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    owner = relationship("User", back_populates="tasks")
    task_type = relationship("TaskType", back_populates="tasks")