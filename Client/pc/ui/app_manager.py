import sys

from PyQt6.QtWidgets import QStackedWidget, QApplication

from api.auth_manager import AuthManager
from ui.login_window import LoginScreen
from ui.main_window import MainWindow


class AppManager(QStackedWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(800, 600)
        self.setWindowTitle("Self Productivity System")

        saved_token = AuthManager.get_valid_token()

        if saved_token:
            self.show_main_window(saved_token)
        else:
            self.show_login_screen()

    def show_login_screen(self):
        self.login_screen = LoginScreen(on_success=self.show_main_window)
        self.addWidget(self.login_screen)
        self.setCurrentWidget(self.login_screen)

    def show_main_window(self, token):
        AuthManager.save_session(token)
        self.token = token
        self.main_window = MainWindow(token)
        self.addWidget(self.main_window)
        self.setCurrentWidget(self.main_window)


def run_app():
    app = QApplication(sys.argv)
    manager = AppManager()
    manager.setStyleSheet("""
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
    manager.show()
    sys.exit(app.exec())