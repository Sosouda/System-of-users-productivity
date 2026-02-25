import requests
from PyQt6.QtCore import QSettings
from datetime import datetime, timezone
from local_db.models import Task, TaskType
from local_db.data_manager import Session
import json
import os


class SyncService:
    def __init__(self, token):
        self.token = token
        self.headers = {"Authorization": f"Bearer {token}"}

        config_path = os.path.join(os.path.dirname(__file__), '..', 'config.json')
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            self.url = f"{config.get('server_url', 'http://localhost:8000')}/sync"
        except FileNotFoundError:
            self.url = "http://localhost:8000/sync"
            print(f"WARNING: config.json not found, using default URL: {self.url}")

        self.settings = QSettings("MyCompany", "SPS")

    def run_sync(self):
        session = Session()
        tasks_count = session.query(Task).count()

        if tasks_count == 0:
            last_sync = "2000-01-01T00:00:00Z"
        else:
            last_sync = str(self.settings.value("last_sync_time", "2000-01-01T00:00:00Z"))
        try:
            last_sync_dt = datetime.fromisoformat(last_sync.replace('Z', '+00:00'))
            local_updates = session.query(Task).filter(Task.updated_at > last_sync_dt).all()

            for task in local_updates:
                task_data = {
                    "id": task.id,
                    "title": task.title,
                    "description": task.description,
                    "task_type_id": task.task_type_id,
                    "personal_priority": task.personal_priority,
                    "influence": task.influence,
                    "status": task.status,
                    "deadline": task.deadline.isoformat() if task.deadline else None,
                    "created_at": task.created_at.isoformat() if task.created_at else datetime.now(timezone.utc).isoformat(),
                    "updated_at": task.updated_at.isoformat(),
                    "final_priority": task.final_priority
                }

                full_payload = {"tasks": [task_data]}

                resp = requests.post(f"{self.url}/push", json=full_payload, headers=self.headers)
                if resp.status_code == 422:
                    print("!!! ОШИБКА ВАЛИДАЦИИ (422) !!!")
                    print(f"Отправленный payload: {full_payload}")
                    print(f"Что ответил сервер: {resp.json()}")
                    return False, "Ошибка валидации данных на сервере"

            response = requests.get(f"{self.url}/pull", params={"last_sync": last_sync}, headers=self.headers)

            if response.status_code == 200:
                data = response.json()

                remote_tasks = data.get("tasks", [])
                print(f"DEBUG: Получено задач от сервера: {len(remote_tasks)}")
                for r_task in remote_tasks:
                    self._merge_task(session, r_task)

                new_sync_time = data.get("server_time")
                if new_sync_time:
                    self.settings.setValue("last_sync_time", new_sync_time)
                    print(f"✅ Sync time updated to server time: {new_sync_time}")

            session.commit()
            return True, "Синхронизация завершена"

        except Exception as e:
            session.rollback()
            print(f"❌ Sync error: {e}")
            return False, str(e)
        finally:
            session.close()

    def _parse_dt(self, dt_str):
        if not dt_str:
            return None
        iso_str = dt_str.replace(" ", "T").replace("Z", "+00:00")
        return datetime.fromisoformat(iso_str)

    def _merge_task(self, session, r_task):
        try:
            r_updated = self._parse_dt(r_task.get('updated_at')).replace(tzinfo=None)
            r_created = self._parse_dt(r_task.get('created_at')).replace(tzinfo=None)
            r_deadline = self._parse_dt(r_task.get('deadline'))

            local_task = session.query(Task).filter_by(id=r_task['id']).first()

            if not local_task:
                print(f"DEBUG: Пытаюсь добавить задачу: {r_task['title']}")
                new_task = Task(
                    id=r_task['id'],
                    title=r_task['title'],
                    description=r_task.get('description', ""),
                    task_type_id=r_task['task_type_id'],
                    personal_priority=r_task.get('personal_priority', 0),
                    influence=r_task.get('influence', 0),
                    status=r_task.get('status', 'underway'),
                    final_priority=r_task.get('final_priority', 'Mid'),
                    created_at=r_created,
                    updated_at=r_updated,
                    deadline=r_deadline
                )
                session.add(new_task)
                print(f"✅ DEBUG: Задача {r_task['title']} успешно добавлена в сессию")
            else:
                l_updated = local_task.updated_at

                if r_updated > l_updated:
                    print(f"DEBUG: Обновление существующей задачи: {r_task['title']}")
                    print(f"DEBUG: Старый статус: {local_task.status}, Новый: {r_task.get('status')}")

                    local_task.title = r_task.get('title')
                    local_task.description = r_task.get('description')
                    local_task.task_type_id = r_task.get('task_type_id')
                    local_task.personal_priority = r_task.get('personal_priority')
                    local_task.influence = r_task.get('influence')
                    local_task.status = r_task.get('status')
                    local_task.final_priority = r_task.get('final_priority')
                    local_task.deadline = r_deadline
                    local_task.updated_at = r_updated
                else:
                    print(f"DEBUG: Задача {r_task['title']} на ПК новее или такая же, пропускаем.")

        except Exception as e:
            print(f"❌ DEBUG: Ошибка в _merge_task для задачи {r_task.get('title')}: {e}")