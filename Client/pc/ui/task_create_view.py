
from PyQt6.QtWidgets import (QWidget, QVBoxLayout,QLineEdit,QPushButton,QLabel,QSpinBox,
                             QComboBox,QMessageBox)
from PyQt6.QtCore import pyqtSignal, Qt

from local_db.data_manager import insert_task, update_daily_info_add_task, select_tasks_for_dupsearch, \
    select_duplicate_deadline
from datetime import date as dt_date
from difflib import SequenceMatcher

from ml.load import  predict_priority

class TaskWindow(QWidget):
    task_saved = pyqtSignal(str, str)
    def __init__(self, deadline_str):
        super().__init__()
        self.setWindowFlag(Qt.WindowType.Window)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.initializeUI()
        self.deadline_str = deadline_str


    def initializeUI(self):
        self.setGeometry(300,200,400,300)
        self.setWindowTitle("Создание задачи")
        self.taskCreatorWindow()
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
    QCheckBox::indicator:checked {
        image: url(:/icons/check.png);
    }
    QRadioButton::indicator:checked {
        background-color: #4a90e2;
        border-radius: 8px;
    }
    """)
        self.show()

    def taskCreatorWindow(self):
        layout = QVBoxLayout()

        label = QLabel("Создание новой задачи")
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Введите название задачи")
        self.desc_input = QLineEdit()
        self.desc_input.setPlaceholderText("Опишите задачу")
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

        task_types = list(self.task_type_map.keys())
        tt_label = QLabel("Выберите тип задачи")
        self.tt_combo = QComboBox()
        self.tt_combo.addItems(task_types)
        self.tt_combo.setCurrentText(task_types[0])
        sp_label = QLabel("Укажите насколько задача важна для вас")
        self.self_priority = QSpinBox()
        self.self_priority.setMinimum(0)
        self.self_priority.setMaximum(10)
        self.self_priority.setSingleStep(1)
        self.self_priority.setValue(0)
        infl_label = QLabel("Укажите сколько задач зависит от этой")
        self.influence = QSpinBox()
        self.influence.setMinimum(0)
        self.influence.setMaximum(10)
        self.influence.setSingleStep(1)
        self.influence.setValue(0)
        self.priority_map = {
            "Авто": "Auto",
            "Обычный": "Casual",
            "Низкий": "Low",
            "Средний": "Mid",
            "Высокий": "High",
            "Критичный": "Extreme"
        }
        priority_list = list(self.priority_map.keys())
        priority_label = QLabel("Выберите итоговый приоритет задачи.(Авто - если хотите чтобы приоритет выбрала нейросеть)")
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(priority_list)
        self.priority_combo.setCurrentText(priority_list[0])
        save_btn = QPushButton("Сохранить")
        save_btn.clicked.connect(self.saveTask)

        layout.addWidget(label)
        layout.addWidget(self.title_input)
        layout.addWidget(self.desc_input)
        layout.addWidget(tt_label)
        layout.addWidget(self.tt_combo)
        layout.addWidget(sp_label)
        layout.addWidget(self.self_priority)
        layout.addWidget(infl_label)
        layout.addWidget(self.influence)
        layout.addWidget(priority_label)
        layout.addWidget(self.priority_combo)

        layout.addWidget(save_btn)

        self.setLayout(layout)

    def saveTask(self):
        title = self.title_input.text()
        desc = self.desc_input.text()
        russian_task_type = self.tt_combo.currentText()
        task_type = self.task_type_map.get(russian_task_type, russian_task_type)
        self_priority = self.self_priority.value()
        influence = self.influence.value()
        russian_priority = self.priority_combo.currentText()
        priority = self.priority_map.get(russian_priority, russian_priority)
        deadline = self.deadline_str
        urgency = influence + self_priority
        tasks = select_tasks_for_dupsearch()
        duplicates = check_for_duplicates(title, desc, tasks)
        if duplicates:
            top_dup = duplicates[0]
            dup_deadline = select_duplicate_deadline(top_dup[0],top_dup[1])
            msg = QMessageBox(self)
            msg.setWindowTitle("Похожая задача найдена")
            msg.setText(
                f"На {dup_deadline} уже есть похожая задача:\n\n"
                f"{top_dup[0]}\n\n"
                f"{top_dup[1]}\n\n"
                f"Вы уверены, что хотите добавить новую задачу?"
            )
            msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            msg.setDefaultButton(QMessageBox.StandardButton.No)
            user_choice = msg.exec()

            if user_choice == QMessageBox.StandardButton.No:
                return
        if priority == "Auto":
            priority = predict_priority(task_type,deadline,urgency)
        insert_task(title, desc, task_type, self_priority, influence, deadline ,priority)
        today = dt_date.today()
        update_daily_info_add_task(today)
        self.task_saved.emit(title, priority)
        self.close()



def check_for_duplicates(new_title: str, new_description: str, tasks: list, threshold: float = 0.8):
    duplicates = []
    for title, description in tasks:
        title_similarity = SequenceMatcher(None, new_title.lower(), title.lower()).ratio()
        desc_similarity = SequenceMatcher(None, new_description.lower(), description.lower()).ratio()

        if (title_similarity >= threshold or desc_similarity >= threshold) and new_description.lower() != '':
            duplicates.append((title, description, title_similarity, desc_similarity))

    return duplicates

