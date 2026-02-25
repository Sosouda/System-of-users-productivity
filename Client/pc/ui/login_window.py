from PyQt6.QtWidgets import (QVBoxLayout, QLineEdit, QPushButton, QLabel, QMessageBox, QWidget)
from PyQt6.QtCore import Qt
import requests


class LoginScreen(QWidget):
    def __init__(self, on_success):
        super().__init__()
        self.on_success = on_success
        self.is_login_mode = True
        self.initUI()

    def initUI(self):
        self.layout = QVBoxLayout()
        self.layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.title = QLabel("Вход в систему")
        self.title.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 20px;")

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Почта(email)")
        self.username_input.setFixedWidth(300)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Пароль")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setFixedWidth(300)

        self.submit_btn = QPushButton("Войти")
        self.submit_btn.setFixedWidth(300)
        self.submit_btn.clicked.connect(self.handle_auth)

        self.switch_btn = QPushButton("Нет аккаунта? Зарегистрироваться")
        self.switch_btn.setFlat(True)
        self.switch_btn.clicked.connect(self.toggle_mode)

        self.layout.addWidget(self.title, alignment=Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.username_input)
        self.layout.addWidget(self.password_input)
        self.layout.addWidget(self.submit_btn)
        self.layout.addWidget(self.switch_btn)

        self.setLayout(self.layout)

    def toggle_mode(self):
        self.is_login_mode = not self.is_login_mode
        if self.is_login_mode:
            self.title.setText("Вход в систему")
            self.submit_btn.setText("Войти")
            self.switch_btn.setText("Нет аккаунта? Зарегистрироваться")
        else:
            self.title.setText("Регистрация")
            self.submit_btn.setText("Создать аккаунт")
            self.switch_btn.setText("Уже есть аккаунт? Войти")

    def handle_auth(self):
        username = self.username_input.text()
        password = self.password_input.text()

        if not username or not password:
            QMessageBox.warning(self, "Ошибка", "Заполните все поля")
            return

        import json
        import os
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config.json')
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            base_url = config.get('server_url', 'http://localhost:8000')
        except FileNotFoundError:
            base_url = "http://localhost:8000"
            QMessageBox.warning(self, "Предупреждение", "config.json не найден. Используем localhost.")

        path = "/auth/login" if self.is_login_mode else "/auth/register"

        try:
            if self.is_login_mode:
                response = requests.post(f"{base_url}{path}", data={"username": username, "password": password})
            else:
                response = requests.post(f"{base_url}{path}", json={"email": username, "password": password})

            if response.status_code == 200:
                if self.is_login_mode:
                    token_data = response.json()
                    self.on_success(token_data.get("access_token"))
                else:
                    print("Регистрация ок, запрашиваю токен...")
                    self.is_login_mode = True
                    self.handle_auth()
            else:
                QMessageBox.critical(self, "Ошибка", f"Ошибка авторизации: {response.text}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось связаться с сервером: {str(e)}")


