from PyQt6.QtWidgets import QMessageBox
from sqlalchemy import create_engine, select,func,case
from sqlalchemy.orm import sessionmaker
from datetime import datetime, date as dt_date
import uuid
from datetime import timezone
import shutil

from local_db.models import Base, TaskType, Task, DailyStats
import os
import sys

def get_db_path():
    if getattr(sys, 'frozen', False):
        if sys.platform == "win32":
            app_data = os.path.join(os.environ.get('APPDATA', ''), 'MyProductivityApp')
        elif sys.platform == "darwin":
            app_data = os.path.join(os.path.expanduser("~"), 'Library', 'Application Support', 'MyProductivityApp')
        else:
            app_data = os.path.join(os.path.expanduser("~"), '.local', 'share', 'MyProductivityApp')

        if not os.path.exists(app_data):
            os.makedirs(app_data)
        return os.path.join(app_data, "SPS.db")
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
        db_dir = os.path.join(base_path, "local_db")
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)
        return os.path.join(db_dir, "SPS.db")


def get_template_db_path():
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
        return os.path.join(base_path, "local_db", "SPS.db")
    return None


def init_db():
    db_path = get_db_path()

    if getattr(sys, 'frozen', False) and not os.path.exists(db_path):
        template_path = get_template_db_path()
        if template_path and os.path.exists(template_path):
            shutil.copy2(template_path, db_path)
        else:
            _create_db_structure(db_path)
    elif not os.path.exists(db_path):
        _create_db_structure(db_path)
    else:
        print(f"ℹ️ БД найдена: {db_path}")

    return db_path


def _create_db_structure(db_path):
    temp_engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(temp_engine)
    temp_session = sessionmaker(bind=temp_engine)()
    try:
        initial_types = [
            "Other", "Meeting", "Dust Cleaning", "Documentation",
            "Customer Support", "Code Bug Fix", "Research",
            "Optimization", "Deployment", "Project Management",
            "Feature Development"
        ]
        temp_session.add_all([TaskType(name=t) for t in initial_types])
        temp_session.commit()
    finally:
        temp_session.close()
        temp_engine.dispose()


db_full_path = get_db_path()
engine = create_engine(f"sqlite:///{db_full_path}", connect_args={"check_same_thread": False}, echo=False)

Session = sessionmaker(bind=engine)


def insert_task(title, desc, task_type_name, self_priority, influence, deadline_str, priority):
    session = Session()
    try:
        new_task_id = str(uuid.uuid4())
        dt = datetime.strptime(deadline_str, "%Y-%m-%d")
        deadline = datetime.combine(dt.date(), datetime.min.time())
        now = datetime.now(timezone.utc)
        task_type = session.query(TaskType).filter_by(name=task_type_name).first()
        if not task_type:
            raise ValueError(f"TaskType '{task_type_name}' не найден")

        task = Task(
            id = new_task_id,
            title=title,
            description=desc,
            task_type_id=task_type.id,
            personal_priority=self_priority,
            influence=influence,
            created_at=now,
            deadline=deadline,
            final_priority=priority,
            updated_at=now
        )

        session.add(task)
        session.commit()
        print(f"✅ Задача '{title}' добавлена.")
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def select_daily_tasks(calendar_date):
    session = Session()
    date = datetime.combine(calendar_date, datetime.min.time())
    tasks = []
    query = select(Task).where(Task.deadline == date)
    result = session.execute(query)
    tasks_obj = result.scalars().all()
    for task in tasks_obj:
        tasks.append((task.title," — ",task.final_priority))
    session.close()
    return tasks

def select_underway_tasks():
    session = Session()
    tasks = []
    query = select(Task.title).where((Task.status == "underway") | (Task.status == "overdue"))
    result = session.execute(query)
    tasks_obj = result.all()
    for task in tasks_obj:
        tasks.append(task.title)
    session.close()
    return tasks


def select_task_property_for_edit(task_title):
    session = Session()
    query = session.query(Task).filter(Task.title == task_title).all()

    for task in query:
        title = task.title
        desc = task.description
        t_type = task.task_type.name
        dl = task.deadline
        prio = task.final_priority
    session.close()
    return title, desc, t_type, dl, prio


def update_task_propeties(task_title: str,task_description: str,new_deadline: str,
                          new_status: str,new_priority: str,new_task_type_name: str):
    session = Session()
    try:
        task = (
            session.query(Task)
            .filter_by(title=task_title, description=task_description)
            .first()
        )

        if not task:
            print("Задача не найдена.")
            return
        deadline = datetime.strptime(new_deadline, "%Y-%m-%d")

        task_type = session.query(TaskType).filter_by(name=new_task_type_name).first()
        if not task_type:
            raise ValueError(f"Тип задачи '{new_task_type_name}' не найден.")

        task.deadline = deadline
        task.status = new_status
        task.final_priority = new_priority
        task.task_type_id = task_type.id
        task.updated_at = datetime.now(timezone.utc)
        session.commit()
    except Exception as e:
        session.rollback()
        print("Ошибка при обновлении:", e)
    finally:
        session.close()

def select_priority_counts():
    session = Session()
    query = select(Task.final_priority, func.count(Task.final_priority)).where((Task.status == "underway")|(Task.status == "overdue")).group_by(Task.final_priority)
    result = session.execute(query)
    priority_count = result.all()
    session.close()
    if not priority_count:
        QMessageBox.information(None, "Внимание", "Нет данных для отображения")
        return [], []
    labels, values = zip(*priority_count)
    labels = list(labels)
    values = list(values)
    return labels,values

def daily_insert():
    session = Session()
    today = dt_date.today()
    exists = session.query(DailyStats).filter(DailyStats.date == today).first()
    if exists:
        print("today stats exists")
        pass
    else:
        insert_daily_info(today)
    session.close()


def insert_daily_info(date):
    session = Session()

    all_tasks = session.execute(select(func.count(Task.title))).scalar()

    daily_info = session.execute(
        select(Task.status, func.count(Task.status))
        .where(Task.status != "completed")
        .group_by(Task.status)
    ).all()

    if daily_info:
        stats, count = zip(*daily_info)
        stats = list(stats)
        count = list(count)
    else:
        session.close()
        return  0,0

    overdue_tasks = count[0] if len(count) > 0 else 0
    in_progress_tasks = count[1] if len(count) > 1 else 0

    daily_stat = DailyStats(
        date=date,
        total_tasks=all_tasks,
        completed_tasks=0,
        overdue_tasks=overdue_tasks,
        in_progress_tasks=in_progress_tasks,
    )

    session.add(daily_stat)
    session.commit()

def update_daily_info_add_task(date: dt_date, new_total_tasks: int = 1, new_in_progress_tasks: int = 1):
    session = Session()
    try:
        record = session.query(DailyStats).filter(DailyStats.date == date).first()
        record.total_tasks += new_total_tasks
        record.in_progress_tasks += new_in_progress_tasks
        session.commit()
    except Exception as e:
        session.rollback()
        print("Ошибка при обновлении total/in-progress:", e)
    finally:
        session.close()


def update_daily_info_overdue_tasks(date, new_overdue_tasks, new_in_progress_tasks):
    session = Session()
    try:
        record = session.query(DailyStats).filter(DailyStats.date == date).first()
        if record is None:
            record = DailyStats(
                date=date,
                total_tasks=0,
                completed_tasks=0,
                overdue_tasks=new_overdue_tasks,
                in_progress_tasks=new_in_progress_tasks,
            )
            session.add(record)
        else:
            record.in_progress_tasks = new_in_progress_tasks
            record.overdue_tasks = new_overdue_tasks
        session.commit()
    except Exception as e:
        session.rollback()
        print("Ошибка при обновлении overdue:", e)
    finally:
        session.close()


def update_daily_info_complete_task(date, title, description):
    session = Session()
    try:
        task = (
            session.query(Task)
            .filter(Task.title == title, Task.description == description)
            .first()
        )
        was_overdue = (task.status == "overdue")
        task.status = "completed"
        task.updated_at = datetime.now(timezone.utc)
        record = session.query(DailyStats).filter(DailyStats.date == date).first()
        record.completed_tasks += 1
        if was_overdue:
            record.overdue_tasks -= 1
        else:
            record.in_progress_tasks -= 1

        session.commit()
    except Exception as e:
        session.rollback()
        print("Ошибка при обновлении completed:", e)
    finally:
        session.close()

def update_tasks_status():
    session = Session()
    try:
        now = datetime.now(timezone.utc)
        tasks = session.query(Task).filter(Task.status != "completed").all()
        for task in tasks:
            if task.deadline < now:
                task.status = "overdue"

        overdue_tasks = len(session.query(Task).filter(Task.status == "overdue").all())
        in_progress_tasks = len(session.query(Task).filter(Task.status == "underway").all())
        session.commit()
        session.close()
        today = dt_date.today()
        update_daily_info_overdue_tasks(today,overdue_tasks,in_progress_tasks)
    except Exception as e:
        print("Ошбика обновления статуса", e)
        session.rollback()
        session.close()

def select_daily_task_complete():
    session = Session()
    query = select(DailyStats.date,DailyStats.completed_tasks)
    result = session.execute(query)
    daily_info = result.all()
    session.close()
    return daily_info

def select_closest_tasks():
    now = dt_date.today()
    session = Session()
    query = (select(Task.title,Task.description).where((Task.deadline >= now) & (Task.status == "underway"))
             .order_by(Task.deadline.asc()).limit(3))
    result = session.execute(query).all()
    session.close()
    return result

def select_all_tasks():
    session = Session()
    query = select(Task.status,func.count(Task.title)).group_by(Task.status)
    result = session.execute(query).all()
    session.close()
    if not result:
        QMessageBox.information(None, "Внимание", "Нет данных для отображения")
        return [], []
    status, count = zip(*result)
    status = list(status)
    count = list(count)
    return status, count

def select_tasks_by_type():
    session = Session()
    query = select(TaskType.name,func.count(Task.title)).join(TaskType).group_by(TaskType.name)
    result = session.execute(query).all()
    session.close()
    if not result:
        QMessageBox.information(None, "Внимание", "Нет данных для отображения")
        return [], []
    type, count = zip(*result)
    type = list(type)
    count = list(count)
    return type, count

def select_completed_by_types():
    session = Session()
    query = select(TaskType.name, func.count(Task.title)).join(TaskType).where(Task.status == "completed").group_by(TaskType.name)
    result = session.execute(query).all()
    session.close()
    if not result:
        QMessageBox.information(None, "Внимание", "Нет данных для отображения")
        return [], []
    type, count = zip(*result)
    type = list(type)
    count = list(count)
    return type, count

def select_daily_tasks_underday():
    session = Session()
    query = select(DailyStats.date, DailyStats.in_progress_tasks)
    result = session.execute(query)
    daily_info = result.all()
    session.close()
    if not result:
        QMessageBox.information(None, "Внимание", "Нет данных для отображения")
        return [], []
    return daily_info

def select_capacity_parametrs():
    session = Session()
    query = select(func.count(Task.title)).where(Task.status == "underway")
    active_tasks = session.execute(query).scalar()
    query = select(func.avg(
        case(
            (Task.final_priority == "Casual", 1),
            (Task.final_priority == "Low", 2),
            (Task.final_priority == "Mid", 3),
            (Task.final_priority == "High", 4),
            (Task.final_priority == "Extreme", 5),
        )
    )).where(Task.status == "underway")
    avg_priority = session.execute(query).scalar()
    query = select(func.max(
        case(
            (Task.final_priority == "Casual", 1),
            (Task.final_priority == "Low", 2),
            (Task.final_priority == "Mid", 3),
            (Task.final_priority == "High", 4),
            (Task.final_priority == "Extreme", 5),
        )
    )).where(Task.status == "underway")
    max_priority = session.execute(query).scalar()
    query = select(
        (func.julianday(Task.deadline) - func.julianday(func.current_timestamp())) * 24
    ).where(Task.status == "underway")
    avg_hours_to_deadline = session.execute(query).scalar()
    query = select(func.count(Task.title)).where(Task.status == "overdue")
    overdue_tasks = session.execute(query).scalar()
    session.close()
    if avg_hours_to_deadline == None:
        return 0,0,0,0,0
    return active_tasks, avg_priority, max_priority, int(avg_hours_to_deadline), overdue_tasks

def select_tasks_for_dupsearch():
    session = Session()
    tasks = []
    query = select(Task.title,Task.description).where((Task.status == "underway") | (Task.status == "overdue"))
    result = session.execute(query)
    tasks_obj = result.all()
    for task in tasks_obj:
        tasks.append([task.title,task.description])
    session.close()
    return tasks

def select_duplicate_deadline(title,description):
    session = Session()
    query = select(Task.deadline).where((Task.title == title)&(Task.description == description))
    result = session.execute(query)
    task_dup = result.scalar()
    session.close()
    dup_deadline = datetime.date(task_dup)
    return dup_deadline

