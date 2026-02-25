import requests
import json
import os
from local_db.models import Task
from datetime import datetime, timezone


def get_server_url():
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config.json')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config.get('server_url', 'http://localhost:8000')
    except FileNotFoundError:
        print(f"WARNING: config.json not found, using default URL")
        return "http://localhost:8000"


def push_to_server(session, token):
    dirty_tasks = session.query(Task).filter_by(is_dirty=True).all()
    server_url = get_server_url()

    for task in dirty_tasks:
        payload = {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "task_type_id": task.task_type_id,
            "personal_priority": task.personal_priority,
            "influence": task.influence,
            "status": task.status,
            "deadline": task.deadline.isoformat() if task.deadline else None,
            "updated_at": task.updated_at.isoformat()
        }
        resp = requests.post(f"{server_url}/sync/push",
                             json=payload,
                             headers={"Authorization": f"Bearer {token}"})
    session.commit()


def pull_from_server(session, token, last_sync_time):
    server_url = get_server_url()
    resp = requests.get(f"{server_url}/sync/pull?last_sync={last_sync_time}",
                        headers={"Authorization": f"Bearer {token}"})
    if resp.status_code == 200:
        data = resp.json()
        remote_tasks = data.get("tasks", [])
        for r_task in remote_tasks:
            local = session.get(Task, r_task['id'])

            r_updated_str = r_task['updated_at'].replace('Z', '+00:00')
            r_updated = datetime.fromisoformat(r_updated_str)

            if not local:
                new_task_data = {k: v for k, v in r_task.items() if hasattr(Task, k)}
                new_l = Task(**new_task_data, is_dirty=False)
                new_l.updated_at = r_updated
                session.add(new_l)
                print(f"Добавлена новая задача: {r_task['id']}")
            elif r_updated > local.updated_at.replace(tzinfo=timezone.utc):
                print(f"Обновление задачи {r_task['id']}. Статус сервер: {r_task['status']}")

                local.title = r_task.get('title', local.title)
                local.description = r_task.get('description', local.description)
                local.status = r_task.get('status', local.status)
                local.task_type_id = r_task.get('task_type_id', local.task_type_id)
                local.final_priority = r_task.get('final_priority', local.final_priority)
                from sqlalchemy import inspect
                print(f"Состояние объекта: {inspect(local).key} - dirty: {local in session.dirty}")

                local.updated_at = r_updated
                local.is_dirty = False
        session.commit()
        print("Синхронизация (PULL) завершена.")