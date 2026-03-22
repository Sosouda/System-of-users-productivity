"""
API для синхронизации ML весов моделей.
Интегрировано в существующую систему синхронизации.
"""

import os
import json
import hashlib
import pickle
from datetime import datetime, timezone
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
import numpy as np

from ..database import get_db
from ..models import User
from ..auth import get_current_user

router = APIRouter(prefix="/ml", tags=["Machine Learning"])

# Пути к хранилищу
STORAGE_DIR = Path(__file__).parent.parent / "ml_storage"
STORAGE_DIR.mkdir(exist_ok=True)

# Метаданные версий
VERSIONS_FILE = STORAGE_DIR / "versions.json"


def load_versions():
    """Загрузить текущие версии моделей"""
    if VERSIONS_FILE.exists():
        with open(VERSIONS_FILE, 'r') as f:
            return json.load(f)
    return {
        "taskload": "1.0.0",
        "taskpriority": "1.0.0"
    }


def save_versions(versions):
    """Сохранить версии моделей"""
    with open(VERSIONS_FILE, 'w') as f:
        json.dump(versions, f, indent=2)


def get_user_backup_dir(user_id: str):
    """Получить директорию для бэкапа весов пользователя"""
    dir_path = STORAGE_DIR / "backups" / str(user_id)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


@router.get("/check-version")
async def check_version(
    taskload_version: str = None,
    taskpriority_version: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Проверить актуальность версий моделей.
    
    Returns:
        {
            "taskload": {"current": "1.0.0", "needs_update": False},
            "taskpriority": {"current": "1.0.0", "needs_update": False}
        }
    """
    versions = load_versions()
    
    result = {}
    
    if taskload_version is not None:
        current = versions.get("taskload", "1.0.0")
        result["taskload"] = {
            "current": current,
            "needs_update": current != taskload_version
        }
    
    if taskpriority_version is not None:
        current = versions.get("taskpriority", "1.0.0")
        result["taskpriority"] = {
            "current": current,
            "needs_update": current != taskpriority_version
        }
    
    return result


@router.post("/backup-weights")
async def backup_weights(
    model_type: str = Form(...),
    version: str = Form(...),
    weights_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Сохранить бэкап весов модели пользователя на сервер.
    
    Это резервная копия на случай потери данных клиентом.
    """
    if model_type not in ["taskload", "taskpriority"]:
        raise HTTPException(status_code=400, detail=f"Unknown model type: {model_type}")
    
    # Читаем файл
    weights_bytes = await weights_file.read()
    
    # Проверяем целостность
    weights_hash = hashlib.sha256(weights_bytes).hexdigest()[:16]
    
    # Сохраняем в файловое хранилище
    backup_dir = get_user_backup_dir(str(current_user.id))
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"{model_type}_{version}_{timestamp}.pkl"
    filepath = backup_dir / filename
    
    with open(filepath, 'wb') as f:
        f.write(weights_bytes)
    
    # Логируем
    log_entry = {
        "user_id": str(current_user.id),
        "model_type": model_type,
        "version": version,
        "hash": weights_hash,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "file": str(filepath)
    }
    
    log_file = STORAGE_DIR / "backup_log.jsonl"
    with open(log_file, 'a') as f:
        f.write(json.dumps(log_entry) + "\n")
    
    print(f"✅ Бэкап весов от пользователя {current_user.id} | Модель: {model_type} | Версия: {version}")
    
    return {
        "status": "success",
        "message": "Weights backed up successfully",
        "file": str(filepath),
        "hash": weights_hash
    }


@router.get("/download-weights")
async def download_weights(
    model_type: str,
    version: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Скачать базовые веса модели (для новой установки или сброса).
    """
    if model_type not in ["taskload", "taskpriority"]:
        raise HTTPException(status_code=400, detail=f"Unknown model type: {model_type}")
    
    # Путь к базовым весам (общие для всех)
    base_weights_path = STORAGE_DIR / "base" / model_type / f"{version}.pkl"
    
    if not base_weights_path.exists():
        raise HTTPException(status_code=404, detail=f"No weights found for {model_type} v{version}")
    
    # Возвращаем файл
    from fastapi.responses import FileResponse
    
    return FileResponse(
        str(base_weights_path),
        media_type="application/octet-stream",
        filename=f"{model_type}_weights_{version}.pkl"
    )


@router.post("/update-version")
async def update_version(
    model_type: str = Form(...),
    new_version: str = Form(...),
    base_weights: UploadFile = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Обновить версию модели (админская операция).
    
    Если переданы base_weights — сохраняем как базовые для всех.
    """
    # TODO: Добавить проверку прав администратора
    versions = load_versions()
    old_version = versions.get(model_type, "1.0.0")
    versions[model_type] = new_version
    save_versions(versions)
    
    # Сохраняем базовые веса если переданы
    if base_weights:
        base_dir = STORAGE_DIR / "base" / model_type
        base_dir.mkdir(parents=True, exist_ok=True)
        base_path = base_dir / f"{new_version}.pkl"
        
        weights_bytes = await base_weights.read()
        with open(base_path, 'wb') as f:
            f.write(weights_bytes)
        
        print(f"✅ Базовые веса сохранены: {base_path}")
    
    print(f"✅ Версия модели {model_type} обновлена: {old_version} → {new_version}")
    
    return {
        "status": "success",
        "model_type": model_type,
        "old_version": old_version,
        "new_version": new_version
    }


@router.get("/stats")
async def get_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Получить статистику по ML весам.
    """
    versions = load_versions()
    
    backup_dir = get_user_backup_dir(str(current_user.id))
    user_backups = list(backup_dir.glob("*.pkl"))
    
    stats = {
        "versions": versions,
        "user_backups": {
            "count": len(user_backups),
            "files": [b.name for b in user_backups[-10:]]  
        }
    }
    
    return stats
