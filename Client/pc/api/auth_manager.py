from PyQt6.QtCore import QSettings, QDateTime, Qt
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os
import hashlib


class AuthManager:
    _encryption_key = None

    @classmethod
    def _get_machine_key(cls):
        if cls._encryption_key is not None:
            return cls._encryption_key

        try:
            import subprocess
            result = subprocess.run(
                ['wmic', 'csproduct', 'get', 'UUID'],
                capture_output=True,
                text=True
            )
            machine_id = result.stdout.strip().split('\n')[-1].strip()
        except:
            import socket
            machine_id = socket.gethostname()

        salt = hashlib.sha256(machine_id.encode()).digest()

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(b"ProductivitySystemFixedKey"))

        cls._encryption_key = key
        return key

    @classmethod
    def _encrypt(cls, data: str) -> str:
        f = Fernet(cls._get_machine_key())
        return f.encrypt(data.encode()).decode()

    @classmethod
    def _decrypt(cls, data: str) -> str:
        f = Fernet(cls._get_machine_key())
        return f.decrypt(data.encode()).decode()

    settings = QSettings("MyCompany", "ProductivitySystem")

    @classmethod
    def save_session(cls, token):
        encrypted_token = cls._encrypt(token)
        cls.settings.setValue("token", encrypted_token)

        expiry_date = QDateTime.currentDateTime().addDays(30)
        cls.settings.setValue("expiry", expiry_date.toString(Qt.DateFormat.ISODate))

    @classmethod
    def get_valid_token(cls):
        try:
            encrypted_token = cls.settings.value("token")
            expiry_str = cls.settings.value("expiry")

            if not encrypted_token or not expiry_str:
                return None

            token = cls._decrypt(encrypted_token)

            expiry_date = QDateTime.fromString(expiry_str, Qt.DateFormat.ISODate)
            if QDateTime.currentDateTime() > expiry_date:
                cls.clear_session()
                return None

            return token
        except Exception as e:
            print(f"Token decryption error: {e}")
            cls.clear_session()
            return None

    @classmethod
    def clear_session(cls):
        cls.settings.remove("token")
        cls.settings.remove("expiry")
