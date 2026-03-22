from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QProgressBar)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


class SyncProgressDialog(QDialog):
    """
    Диалог прогресса синхронизации.
    Показывается при входе в приложение.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Синхронизация")
        self.setModal(True)
        self.setFixedSize(400, 200)
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowType.WindowCloseButtonHint
        )
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)
        
        title_label = QLabel("🔄 Синхронизация данных")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        self.status_label = QLabel("Подождите, синхронизируем данные...")
        self.status_label.setFont(QFont("Arial", 11))
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #7f8c8a;")
        layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(10)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #ecf0f1;
                border: none;
                border-radius: 5px;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                border-radius: 5px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        self.details_label = QLabel("")
        self.details_label.setFont(QFont("Arial", 9))
        self.details_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.details_label.setStyleSheet("color: #95a5a6;")
        self.details_label.setWordWrap(True)
        layout.addWidget(self.details_label)
    
    def set_status(self, text):
        """Установить статус"""
        self.status_label.setText(text)
    
    def set_details(self, text):
        """Установить детали"""
        self.details_label.setText(text)
    
    def finish(self):
        """Завершить синхронизацию"""
        self.accept()
