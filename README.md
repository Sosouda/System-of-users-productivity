# 🚀 ProductivitySync — Система управления продуктивностью с AI

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)

**ProductivitySync** — это кроссплатформенная система управления задачами с машинным обучением, которая помогает прогнозировать вашу загрузку и автоматически расставлять приоритеты.

---

## 📋 Содержание

- [Возможности](#-возможности)
- [Архитектура](#-архитектура)
- [Установка](#-установка)
- [API Документация](#-api-документация)
- [Безопасность](#-безопасность)
- [Лицензия](#-лицензия)

---

## ✨ Возможности

### 🤖 Машинное обучение
- **Прогноз загрузки** — предсказание вашей занятости
- **Автоприоритизация** — ML определяет важность задач

### 📱 Кроссплатформенность
- **Android** — мобильное приложение (API 24+)
- **Windows/Linux/macOS** — десктопное приложение
- **Синхронизация** — все устройства в реальном времени
- **Офлайн режим** — работа без интернета

### 🔐 Безопасность
- JWT аутентификация
- Хеширование паролей (bcrypt)
- Шифрование токенов на клиенте
- HTTPS поддержка

---

## 🏗️ Архитектура

```
┌─────────────────────────────────────────────────────────┐
│                    ProductivitySync                     │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐         ┌──────────────┐              │
│  │   Android    │         │  Desktop PC  │              │
│  │   Client     │◄───────►│   Client     │              │
│  │   (Kotlin)   │         │   (Python)   │              │
│  └──────────────┘         └──────────────┘              │
│           │                         │                   │
│           └──────────┬──────────────┘                   │
│                      │                                  │
│                      ▼                                  │
│            ┌─────────────────┐                          │
│            │   Sync Server   │                          │
│            │   (FastAPI)     │                          │
│            └────────┬────────┘                          │
│                     │                                   │
│            ┌────────▼────────┐                          │
│            │  PostgreSQL DB  │                          │
│            └─────────────────┘                          │
│                                                         │
└─────────────────────────────────────────────────────────┘
```


## 📦 Установка

### Требования

| Компонент | Версия | Примечание |
|-----------|--------|------------|
| **Python** | 3.12+ | Для сервера и PC клиента |
| **PostgreSQL** | 15+ | База данных |
| **Docker** | 24+ | Опционально (рекомендуется) |
| **Android Studio** | Arctic Fox+ | Для Android приложения |

---

### Сервер: Вариант 1 (Docker — рекомендуется)

```bash
cd Backend/sync_server

# Создайте .env
cp .env.docker.example .env

# Отредактируйте .env
# POSTGRES_PASSWORD=ваш_пароль
# SECRET_KEY=ваш_ключ

# Запустите
docker compose up -d

# Проверьте
curl http://localhost:8000/
```

---

### Сервер: Вариант 2 (Без Docker)

```bash
cd Backend/sync_server

# Создайте виртуальное окружение
python3 -m venv .venv
source .venv/bin/activate

# Установите зависимости
pip install -r requirements.txt

# Создайте .env
cp .env.example .env
nano .env

# Запустите
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

### PC клиент: Windows

```bash
cd Client/pc

# Установите зависимости
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# Запустите
python main.py
```

**Или скачайте готовый EXE:**
1. Перейдите в [Releases](https://github.com/sosouda/productivity-sync/releases)
2. Скачайте `ProductivitySync-Windows.exe`
3. Запустите

---

### PC клиент: Linux/macOS

```bash
cd Client/pc

# Установите зависимости
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Запустите
python3 main.py
```

---

### Android приложение

#### Вариант 1: Готовый APK

1. Скачайте из [Releases](https://github.com/sosouda/productivity-sync/releases)
2. Разрешите установку из неизвестных источников
3. Установите APK

#### Вариант 2: Сборка из исходников

```bash
cd Client/android

# Откройте в Android Studio
# Или соберите:
./gradlew assembleRelease

# APK: app/build/outputs/apk/release/app-release.apk
```

---

## 📚 API Документация

### Основные эндпоинты

| Метод | Путь | Описание |
|-------|------|----------|
| `GET` | `/` | Статус сервера |
| `POST` | `/auth/register` | Регистрация |
| `POST` | `/auth/login` | Вход |
| `POST` | `/sync/push` | Отправка задач |
| `GET` | `/sync/pull` | Получение задач |
| `GET` | `/docs` | Swagger UI |

### Модели данных

**Task (Задача):**
```json
{
  "id": "uuid-string",
  "title": "Название задачи",
  "description": "Описание",
  "task_type_id": 1,
  "personal_priority": 3,
  "influence": 5,
  "status": "underway",
  "deadline": "2026-03-01T00:00:00Z",
  "created_at": "2026-02-19T12:00:00Z",
  "updated_at": "2026-02-19T12:00:00Z",
  "final_priority": "High"
}
```

**Статусы задач:**
- `underway` — в работе
- `completed` — выполнена
- `overdue` — просрочена

**Приоритеты:**
- `Casual` — минимальный
- `Low` — низкий
- `Mid` — средний
- `High` — высокий
- `Extreme` — критический

---

## 🔐 Безопасность

### Что защищено

| Данные | Метод защиты |
|--------|--------------|
| Пароли | Хеширование bcrypt |
| JWT токены | Подпись SECRET_KEY |
| Токены на клиенте | Шифрование Fernet + HWID |
| Соединение | HTTPS (рекомендуется) |



## 📄 Лицензия

MIT License — см. [LICENSE](LICENSE) файл для деталей.

---

## 🤝 Помощь

1. Fork репозиторий
2. Создайте feature branch (`git checkout -b feature/amazing-feature`)
3. Commit изменения (`git commit -m 'Add amazing feature'`)
4. Push в branch (`git push origin feature/amazing-feature`)
5. Откройте Pull Request

---

## 📞 Контакты

- **Issues:** [GitHub Issues](https://github.com/Sosouda/System-of-users-productivity/issues)
- **Email:** silverhedgehog432@gmail.com
- **Telegram:** @sosouda

---

<div align="center">

**ProductivitySync** © 2026

[⬆️ Вернуться к началу](#-productivitysync--система-управления-продуктивностью-с-ai)

</div>
