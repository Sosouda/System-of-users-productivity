from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QPushButton, QLabel, QComboBox, \
    QHBoxLayout, QCheckBox
from PyQt6.QtCore import Qt
from datetime import date as dt_date

from local_db.data_manager import update_task_propeties, update_daily_info_complete_task


class EditWindow(QWidget):
    def __init__(self,title,description,t_type,ddln,priority, parent):
        super().__init__()
        self.setWindowFlag(Qt.WindowType.Window)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.title = title
        self.description = description
        self.t_type = t_type
        self.ddln = ddln
        self.priority = priority
        self.parent = parent
        self.initializeUI()



    def initializeUI(self):
        self.setGeometry(300,200,400,300)
        self.setWindowTitle("Редактирование задачи")
        self.taskEditorWindow()
        self.setStyleSheet("""
        QWidget {
            background-color: #f7f9fc;
            color: #2e3440;
            font-family: "Segoe UI", "Roboto", sans-serif;
            font-size: 14px;
        }
    
    /* === Кнопки === */
    QPushButton {
        background-color: #4a90e2;
        color: white;
        border-radius: 8px;
        padding: 6px 14px;
        border: none;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    QPushButton:hover {
        background-color: #5aa1f2;
    }
    QPushButton:pressed {
        background-color: #357abd;
    }
    QPushButton:disabled {
        background-color: #c8d4e2;
        color: #7f8c9a;
    }
    
    /* === Поля ввода === */
    QLineEdit, QTextEdit, QPlainTextEdit {
        background-color: white;
        border: 1px solid #d0d7de;
        border-radius: 6px;
        padding: 6px;
        selection-background-color: #4a90e2;
    }
    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
        border: 1px solid #4a90e2;
        background-color: #ffffff;
    }
    
    /* === Метки === */
    QLabel {
        color: #2e3440;
        font-weight: 500;
    }
    
    /* === ComboBox === */
    QComboBox {
        background-color: white;
        border: 1px solid #d0d7de;
        border-radius: 6px;
        padding: 4px 8px;
    }
    QComboBox:hover {
        border: 1px solid #4a90e2;
    }
    QComboBox::drop-down {
        border: none;
        width: 25px;
    }
    QComboBox::down-arrow {
        image: url(:/icons/down-arrow.png); /* можно заменить или убрать */
    }
    
    /* === Таблицы === */
    QTableWidget, QTableView {
        background-color: white;
        border: 1px solid #d0d7de;
        border-radius: 8px;
        gridline-color: #e1e8ef;
        selection-background-color: #4a90e2;
        selection-color: white;
    }
    QHeaderView::section {
        background-color: #eef2f7;
        color: #2e3440;
        padding: 6px;
        border: none;
        border-bottom: 1px solid #d0d7de;
        font-weight: 600;
    }
    
    /* === ScrollBar === */
    QScrollBar:vertical {
        background: #f0f3f8;
        width: 10px;
        margin: 2px;
        border-radius: 5px;
    }
    QScrollBar::handle:vertical {
        background: #c3cad5;
        border-radius: 5px;
    }
    QScrollBar::handle:vertical:hover {
        background: #aab3c2;
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        background: none;
        border: none;
    }
    
    /* === GroupBox === */
    QGroupBox {
        border: 1px solid #d0d7de;
        border-radius: 8px;
        margin-top: 10px;
        font-weight: bold;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 0 8px;
    }
    
    /* === Checkbox / Radio === */
    QCheckBox, QRadioButton {
        spacing: 6px;
    }
    QCheckBox::indicator, QRadioButton::indicator {
        width: 16px;
        height: 16px;
    }
    QRadioButton::indicator:checked {
        background-color: #4a90e2;
        border-radius: 8px;
    }
    
    """)
        self.show()

    def taskEditorWindow(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        header_layout = QVBoxLayout()
        title_label = QLabel(self.title)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #4a90e2;")

        desc_label = QLabel(self.description)
        desc_label.setStyleSheet("color: #606770; font-size: 13px;")
        desc_label.setWordWrap(True)

        header_layout.addWidget(title_label)
        header_layout.addWidget(desc_label)
        main_layout.addLayout(header_layout)

        line = QLabel()
        line.setFixedHeight(1)
        line.setStyleSheet("background-color: #d0d7de;")
        main_layout.addWidget(line)

        grid_params = QHBoxLayout()
        grid_params.setSpacing(20)

        left_col = QVBoxLayout()

        left_col.addWidget(QLabel("Тип задачи:"))
        self.task_type_edcombo = QComboBox()
        self.task_type_map = {
            "Другое": "Other",
            "Уборка": "Dust Cleaning",
            "Встреча": "Meeting",
            "Документация": "Documentation",
            "Поддержка клиентов": "Customer Support",
            "Исправление ошибок": "Code Bug Fix",
            "Исследование": "Research",
            "Разработка функционала": "Feature Development",
            "Оптимизация": "Optimization",
            "Развертывание": "Deployment",
            "Управление проектом": "Project Management"
        }
        self.reverse_task_type_map = {v: k for k, v in self.task_type_map.items()}

        russian_task_types = list(self.task_type_map.keys())
        self.task_type_edcombo.addItems(russian_task_types)

        current_russian_type = self.reverse_task_type_map.get(self.t_type, self.t_type)
        self.task_type_edcombo.setCurrentText(current_russian_type)
        left_col.addWidget(self.task_type_edcombo)

        left_col.addWidget(QLabel("Приоритет:"))
        self.priority_edcombo = QComboBox()
        self.priority_map = {
            "Обычный": "Casual",
            "Низкий": "Low",
            "Средний": "Mid",
            "Высокий": "High",
            "Критичный": "Extreme"
        }

        self.reverse_priority_map = {v: k for k, v in self.priority_map.items()}

        russian_priorities = list(self.priority_map.keys())
        self.priority_edcombo.addItems(russian_priorities)

        current_russian_priority = self.reverse_priority_map.get(self.priority, self.priority)
        self.priority_edcombo.setCurrentText(current_russian_priority)
        left_col.addWidget(self.priority_edcombo)

        right_col = QVBoxLayout()

        right_col.addWidget(QLabel("Срок (ГГГГ-ММ-ДД):"))
        self.deadline_edline = QLineEdit(f"{self.ddln}")
        right_col.addWidget(self.deadline_edline)

        right_col.addStretch()  # Поджимаем чекбокс вниз
        self.done_checkbox = QCheckBox("Задача выполнена")
        self.done_checkbox.setStyleSheet("font-weight: bold; color: #2e7d32;")
        self.done_checkbox.setStyleSheet("""QCheckBox::indicator:checked {
                                                background-color: #2e7d32; 
                                                border: 2px solid #2e7d32;
                                            }""")
        self.cancel_checkbox = QCheckBox("Отменить задачу")
        self.cancel_checkbox.setStyleSheet("font-weight: bold; color: #960018;")
        self.cancel_checkbox.setStyleSheet("""QCheckBox::indicator:checked {
                                                        background-color: #960018; 
                                                        border: 2px solid #960018;
                                                    }""")
        right_col.addWidget(self.done_checkbox)
        right_col.addWidget(self.cancel_checkbox)

        grid_params.addLayout(left_col)
        grid_params.addLayout(right_col)
        main_layout.addLayout(grid_params)

        main_layout.addStretch()

        savechage_btn = QPushButton("Save Changes")
        savechage_btn.setFixedHeight(40)
        savechage_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        savechage_btn.clicked.connect(self.updateTask)
        main_layout.addWidget(savechage_btn)

        self.setLayout(main_layout)
    def updateTask(self):
        if self.done_checkbox.isChecked() == True:
            new_status = "completed"
            today = dt_date.today()
            update_daily_info_complete_task(today,self.title,self.description)
        elif self.cancel_checkbox.isChecked() == True:
            new_status = "cancelled"
        else:
            new_status = "underway"
        russian_task_type = self.task_type_edcombo.currentText()
        new_task_type = self.task_type_map.get(russian_task_type, russian_task_type)

        russian_priority = self.priority_edcombo.currentText()
        new_priority = self.priority_map.get(russian_priority, russian_priority)
        new_deadline = self.deadline_edline.text()
        update_task_propeties(self.title, self.description, new_deadline, new_status, new_priority, new_task_type)
        self.close()

    def closeEvent(self, event):
        if self.parent:
            self.parent.refreshTaskList()
        event.accept()



