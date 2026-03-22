from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QFrame, QSlider, QMessageBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from ml.feedback_collector import FeedbackCollector
from ml.fine_tune_onnx import extract_onnx_weights, create_torch_model_from_onnx, fine_tune_torch_model, get_torch_weights, save_onnx_with_weights
from pathlib import Path
import pickle
import json
import shutil
from datetime import datetime


class WorkloadFeedbackDialog(QDialog):
    """
    Диалоговое окно для сбора оценки нагрузки пользователя (0-100).
    Вызывается при выходе из приложения.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_workload = None
        self.setWindowTitle("Оценка нагрузки")
        self.setModal(True)
        self.setMinimumWidth(500)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Заголовок
        title_label = QLabel("Как вы оцениваете свою нагрузку сегодня?")
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setWordWrap(True)
        layout.addWidget(title_label)

        # Подзаголовок
        subtitle_label = QLabel("Выберите значение от 0 (нет нагрузки) до 100 (максимальная)")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet("color: #7f8c8a; font-size: 12px;")
        layout.addWidget(subtitle_label)

        # Ползунок (слайдер)
        slider_layout = QHBoxLayout()
        slider_layout.setSpacing(10)

        self.value_label = QLabel("50")
        self.value_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        self.value_label.setFixedWidth(60)
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        slider_layout.addWidget(self.value_label)

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(100)
        self.slider.setValue(50)
        self.slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.slider.setTickInterval(10)
        self.slider.setMinimumHeight(40)
        self.slider.valueChanged.connect(self._on_slider_change)
        slider_layout.addWidget(self.slider)

        layout.addLayout(slider_layout)

        scale_label = QLabel("0 — Нет нагрузки ; 50 — Средняя ; 100 — Максимальная")
        scale_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        scale_label.setStyleSheet("color: #95a5a6; font-size: 11px;")
        layout.addWidget(scale_label)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("background-color: #ecf0f1;")
        layout.addWidget(line)
        
        self.train_btn = QPushButton("🚀 Дообучить модели")
        self.train_btn.setFixedHeight(40)
        self.train_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                border: 2px solid #229954;
                border-radius: 6px;
                color: white;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
            QPushButton:pressed {
                background-color: #229954;
            }
        """)
        self.train_btn.clicked.connect(self._on_train_models)
        layout.addWidget(self.train_btn)
        
        self.rollback_btn = QPushButton("↩️ Откатить к базовой версии")
        self.rollback_btn.setFixedHeight(35)
        self.rollback_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                border: 2px solid #c0392b;
                border-radius: 6px;
                color: white;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        self.rollback_btn.clicked.connect(self._on_rollback)
        layout.addWidget(self.rollback_btn)
        
        action_layout = QHBoxLayout()

        skip_btn = QPushButton("Пропустить")
        skip_btn.setFixedHeight(40)
        skip_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 2px solid #bdc3c7;
                border-radius: 6px;
                color: #7f8c8a;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ecf0f1;
            }
        """)
        skip_btn.clicked.connect(self._on_skip)

        submit_btn = QPushButton("Отправить")
        submit_btn.setFixedHeight(40)
        submit_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                border: 2px solid #2980b9;
                border-radius: 6px;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                border-color: #95a5a6;
            }
        """)
        submit_btn.setEnabled(False)
        submit_btn.clicked.connect(self._on_submit)

        self.submit_button = submit_btn

        action_layout.addWidget(skip_btn)
        action_layout.addWidget(submit_btn)
        layout.addLayout(action_layout)

    def _on_slider_change(self, value):
        """Обработка изменения ползунка"""
        self.selected_workload = value
        self.value_label.setText(str(value))
        self.submit_button.setEnabled(True)
    
    def _on_train_models(self):
        """Дообучение моделей"""

        QMessageBox.information(
            self,
            "Дообучение моделей",
            "Начинаю дообучение моделей на ваших данных...\n\n"
            "Это может занять несколько секунд."
        )
        
        try:
            from local_db.data_manager import get_unsynced_ml_feedback_taskload, get_unsynced_ml_feedback_taskpriority, mark_ml_feedback_taskload_synced, mark_ml_feedback_taskpriority_synced
            
            taskload_records = get_unsynced_ml_feedback_taskload()
            taskpriority_records = get_unsynced_ml_feedback_taskpriority()
            
            results = []
            trained_models = []
            taskload_ids = [r.id for r in taskload_records]
            taskpriority_ids = [r.id for r in taskpriority_records]
            
            if len(taskload_records) >= 3:
                self._train_taskload(taskload_records)
                trained_models.append("taskload")
                results.append("✅ TaskLoad дообучена")
            else:
                results.append("⚠️ TaskLoad: недостаточно данных (минимум 3)")
            
            if len(taskpriority_records) >= 3:
                self._train_taskpriority(taskpriority_records)
                trained_models.append("taskpriority")
                results.append("✅ TaskPriority дообучена")
            else:
                results.append("⚠️ TaskPriority: недостаточно данных (минимум 3)")
            
            if trained_models:
                QMessageBox.information(
                    self,
                    "Отправка на сервер",
                    f" Отправляю бэкап весов на сервер...\n\n"
                    f"Модели: {', '.join(trained_models)}"
                )
                
                from api.sync_service import SyncService
                from api.auth_manager import AuthManager
                
                token = AuthManager.get_valid_token()
                if token:
                    sync_service = SyncService(token)
                    
                    if "taskload" in trained_models:
                        sync_service.ml_sync.backup_weights("taskload")
                        if taskload_ids:
                            mark_ml_feedback_taskload_synced(taskload_ids)
                        results.append(f"\n TaskLoad бэкап отправлен на сервер!")
                    
                    if "taskpriority" in trained_models:
                        sync_service.ml_sync.backup_weights("taskpriority")
                        if taskpriority_ids:
                            mark_ml_feedback_taskpriority_synced(taskpriority_ids)
                        results.append(f" TaskPriority бэкап отправлен на сервер!")
                    
                    results.append("Ваши персональные веса сохранены в облаке.")
                    results.append("Данные дообучения помечены как использованные.")

                    self._update_versions()

            QMessageBox.information(
                self,
                "Дообучение завершено",
                "\n".join(results) + "\n\n"
                "Теперь модели работают точнее! 🎉"
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Ошибка",
                f"❌ Ошибка при дообучении:\n{e}"
            )
    
    def _train_taskload(self, records):
        """Дообучение TaskLoad"""
        from ml.fine_tune_onnx import extract_onnx_weights, create_torch_model_from_onnx, fine_tune_torch_model, get_torch_weights, save_onnx_with_weights
        from pathlib import Path
        
        script_dir = Path(__file__).parent.parent
        model_path = script_dir / "ml" / "TaskLoad" / "tlm.onnx"
        
        weights = extract_onnx_weights(str(model_path))
        
        model = create_torch_model_from_onnx(weights, model_type="taskload")

        model, loss_history = fine_tune_torch_model(model, records, model_type="taskload", epochs=10, lr=0.001)

        new_weights = get_torch_weights(model, model_type="taskload")
        save_onnx_with_weights(str(model_path), new_weights, str(model_path))
    
    def _train_taskpriority(self, records):
        """Дообучение TaskPriority"""
        from ml.fine_tune_onnx import extract_onnx_weights, create_torch_model_from_onnx, fine_tune_torch_model, get_torch_weights, save_onnx_with_weights
        from pathlib import Path
  
        script_dir = Path(__file__).parent.parent
        model_path = script_dir / "ml" / "TaskPriority" / "dualhead_tpm.onnx"
        
        weights = extract_onnx_weights(str(model_path))
        
        model = create_torch_model_from_onnx(weights, model_type="taskpriority")
        
        model, loss_history = fine_tune_torch_model(model, records, model_type="taskpriority", epochs=10, lr=0.001)
        
        new_weights = get_torch_weights(model, model_type="taskpriority")
        save_onnx_with_weights(str(model_path), new_weights, str(model_path))
    
    def _on_rollback(self):
        """Откат к базовой версии модели"""
        reply = QMessageBox.question(
            self,
            "Откат модели",
            "⚠️ Вы уверены что хотите откатиться к базовой версии?\n\n"
            "Это заменит текущие персональные веса на базовые.\n"
            "Все ваши дообученные данные будут сохранены в архиве.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        try:
            script_dir = Path(__file__).parent.parent
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archive_dir = script_dir / "ml" / "archived_weights" / timestamp
            archive_dir.mkdir(parents=True, exist_ok=True)
            
            shutil.copy(
                script_dir / "ml" / "TaskLoad" / "tlm.onnx",
                archive_dir / "tlm_archived.onnx"
            )
            shutil.copy(
                script_dir / "ml" / "TaskPriority" / "dualhead_tpm.onnx",
                archive_dir / "dualhead_tpm_archived.onnx"
            )
            
            base_taskload = script_dir / "ml" / "TaskLoad" / "tlm_base_v1.0.0.onnx"
            base_taskpriority = script_dir / "ml" / "TaskPriority" / "dualhead_tpm_base_v1.0.0.onnx"
            
            if base_taskload.exists():
                shutil.copy(base_taskload, script_dir / "ml" / "TaskLoad" / "tlm.onnx")
            
            if base_taskpriority.exists():
                shutil.copy(base_taskpriority, script_dir / "ml" / "TaskPriority" / "dualhead_tpm.onnx")
            
            self._reset_versions()
            
            QMessageBox.information(
                self,
                "Откат завершён",
                f"✅ Модели откатаны к базовой версии v1.0.0\n\n"
                f"Архив ваших весов сохранён:\n{archive_dir}\n\n"
                "Теперь можно начать дообучение заново!"
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Ошибка",
                f"❌ Ошибка при откате:\n{e}"
            )
    
    def _reset_versions(self):
        """Сбросить версии к базовым"""
        versions_file = Path(__file__).parent.parent / "ml" / "versions.json"
        versions = {
            "taskload": "1.0.0",
            "taskpriority": "1.0.0"
        }
        with open(versions_file, 'w') as f:
            json.dump(versions, f, indent=2)
    
    def _update_versions(self):
        """Обновить версии (инкрементировать)"""
        versions_file = Path(__file__).parent.parent / "ml" / "versions.json"
        try:
            with open(versions_file, 'r') as f:
                versions = json.load(f)
        except:
            versions = {"taskload": "1.0.0", "taskpriority": "1.0.0"}
        
        current = versions.get("taskload", "1.0.0").split('.')
        current[-1] = str(int(current[-1]) + 1)
        versions["taskload"] = '.'.join(current)
        
        current = versions.get("taskpriority", "1.0.0").split('.')
        current[-1] = str(int(current[-1]) + 1)
        versions["taskpriority"] = '.'.join(current)
        
        with open(versions_file, 'w') as f:
            json.dump(versions, f, indent=2)

    def _on_skip(self):
        """Пользователь пропустил оценку"""
        self.selected_workload = None
        self.reject()

    def _on_submit(self):
        """Пользователь отправил оценку"""
        if self.selected_workload is not None:
            self.accept()

    def get_workload(self):
        """Возвращает выбранную оценку нагрузки"""
        return self.selected_workload
