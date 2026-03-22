"""
Модуль для синхронизации ML весов с сервером.
Интегрирован в существующую систему синхронизации.
"""

import os
import json
import pickle
import requests
from datetime import datetime
from pathlib import Path
from PyQt6.QtCore import QSettings

from ml.feedback_collector import FeedbackCollector
from ml.fine_tune_onnx import (
    extract_onnx_weights,
    create_torch_model_from_onnx,
    fine_tune_torch_model,
    get_torch_weights,
    save_onnx_with_weights
)


class MLWeightsSync:
    """
    Сервис для синхронизации ML весов с сервером.
    """
    
    def __init__(self, token):
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}"
        }
        
        config_path = Path(__file__).parent.parent / "config.json"
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            self.base_url = config.get('server_url', 'http://localhost:8000')
        except FileNotFoundError:
            self.base_url = "http://localhost:8000"
        
        self.ml_url = f"{self.base_url}/ml"
        
        self.models_dir = Path(__file__).parent.parent / "ml"
        self.taskload_model_path = self.models_dir / "TaskLoad" / "tlm.onnx"
        self.taskpriority_model_path = self.models_dir / "TaskPriority" / "dualhead_tpm.onnx"
        
        self.versions_file = self.models_dir / "versions.json"
        self._load_versions()
    
    def _load_versions(self):
        """Загрузка текущих версий моделей"""
        try:
            with open(self.versions_file, 'r') as f:
                self.versions = json.load(f)
        except FileNotFoundError:
            self.versions = {
                "taskload": "1.0.0",
                "taskpriority": "1.0.0"
            }
            self._save_versions()
    
    def _save_versions(self):
        """Сохранение версий моделей"""
        with open(self.versions_file, 'w') as f:
            json.dump(self.versions, f, indent=2)
    
    def check_versions(self):
        """
        Проверить актуальность версий моделей на сервере.
        
        Returns:
            dict: {'taskload': {'current': '1.0.0', 'needs_update': False}, ...}
        """
        try:
            params = {}
            if 'taskload' in self.versions:
                params['taskload_version'] = self.versions['taskload']
            if 'taskpriority' in self.versions:
                params['taskpriority_version'] = self.versions['taskpriority']
            
            response = requests.get(
                f"{self.ml_url}/check-version",
                params=params,
                headers=self.headers
            )
            
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"⚠️ Не удалось проверить версии: {e}")
        
        return {}
    
    def backup_weights(self, model_type="taskload"):
        """
        Отправить бэкап весов на сервер.
        
        Args:
            model_type: "taskload" или "taskpriority"
        
        Returns:
            bool: True если успешно
        """
        try:
            if model_type == "taskload":
                model_path = str(self.taskload_model_path)
                version = self.versions.get('taskload', '1.0.0')
            else:
                model_path = str(self.taskpriority_model_path)
                version = self.versions.get('taskpriority', '1.0.0')
            
            weights = extract_onnx_weights(model_path)
            
            weights_bytes = pickle.dumps(weights)
            
            files = {
                'weights_file': ('weights.pkl', weights_bytes, 'application/octet-stream')
            }
            data = {
                'model_type': model_type,
                'version': version
            }
            
            response = requests.post(
                f"{self.ml_url}/backup-weights",
                files=files,
                data=data,
                headers={"Authorization": self.headers["Authorization"]}
            )
            
            if response.status_code == 200:
                print(f"✅ Бэкап {model_type} весов отправлен на сервер")
                return True
            else:
                print(f"❌ Ошибка бэкапа: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка бэкапа весов: {e}")
            return False
    
    def download_base_weights(self, model_type="taskload"):
        """
        Скачать базовые веса модели.
        
        Args:
            model_type: "taskload" или "taskpriority"
        
        Returns:
            bool: True если успешно
        """
        try:
            version = self.versions.get(model_type, '1.0.0')
            
            response = requests.get(
                f"{self.ml_url}/download-weights",
                params={
                    'model_type': model_type,
                    'version': version
                },
                headers=self.headers
            )
            
            if response.status_code == 200:
                if model_type == "taskload":
                    save_path = self.models_dir / "TaskLoad" / f"tlm_base_v{version}.onnx"
                else:
                    save_path = self.models_dir / "TaskPriority" / f"dualhead_tpm_base_v{version}.onnx"
                
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                
                print(f"✅ Базовые веса {model_type} v{version} скачаны")
                return True
            else:
                print(f"❌ Ошибка скачивания: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка скачивания весов: {e}")
            return False
    
    def sync_after_training(self, model_type="taskload"):
        """
        Синхронизация после локального дообучения.
        
        1. Отправляет бэкап новых весов на сервер
        2. Проверяет версии
        
        Args:
            model_type: "taskload" или "taskpriority"
        """
        print(f"\n🔄 ML синхронизация ({model_type})...")
        

        self.backup_weights(model_type)
        

        versions_status = self.check_versions()
        
        if versions_status:
            for mt, status in versions_status.items():
                if status.get('needs_update'):
                    print(f"⚠️ Доступна новая версия {mt}: {status['current']}")
                else:
                    print(f"✅ {mt}: версия актуальна")
    
    def full_sync(self):
        """
        Полная синхронизация ML весов.
        
        1. Проверяем версии
        2. Если есть новые — скачиваем
        3. Отправляем бэкап текущих весов
        """
        print("\n" + "="*60)
        print("🔄 ПОЛНАЯ ML СИНХРОНИЗАЦИЯ")
        print("="*60)
        
        versions_status = self.check_versions()
        
        for model_type in ['taskload', 'taskpriority']:
            if model_type in versions_status:
                status = versions_status[model_type]
                
                if status.get('needs_update'):
                    print(f"\n📥 Скачивание новой версии {model_type}...")
                    self.download_base_weights(model_type)
                else:
                    print(f"\n✅ {model_type}: версия актуальна")
        
        print("\n📤 Отправка бэкапа весов...")
        self.backup_weights("taskload")
        self.backup_weights("taskpriority")
        
        print("\n✅ ML синхронизация завершена")
        print("="*60 + "\n")
