from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import models, schemas, database, auth
from datetime import datetime, timezone

router = APIRouter(prefix="/sync", tags=["Sync"])


@router.post("/push")
def push_tasks(
        sync_data: schemas.SyncData,
        db: Session = Depends(database.get_db),
        current_user: models.User = Depends(auth.get_current_user)
):
    for task_in in sync_data.tasks:
        db_task = db.query(models.Task).filter(
            models.Task.id == task_in.id,
            models.Task.user_id == current_user.id
        ).first()

        if not db_task:
            new_task = models.Task(**task_in.model_dump(), user_id=current_user.id)
            db.add(new_task)
        else:
            if task_in.updated_at > db_task.updated_at.replace(tzinfo=task_in.updated_at.tzinfo):
                for key, value in task_in.model_dump().items():
                    setattr(db_task, key, value)

    db.commit()
    return {"status": "success", "message": "Tasks synced"}


@router.get("/pull", response_model=schemas.PullResponse)
def pull_tasks(
        last_sync: str,
        db: Session = Depends(database.get_db),
        current_user: models.User = Depends(auth.get_current_user)
):
    current_server_time = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    tasks = db.query(models.Task).filter(
        models.Task.user_id == current_user.id,
        models.Task.updated_at > last_sync
    ).all()

    return {
        "tasks": tasks,
        "server_time": current_server_time
    }