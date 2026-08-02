# 🛠 Полная инструкция по установке и запуску

> **APAS Ecosystem v0.1.0-canary** · Экспериментальная версия.
> Перед запуском обязательно прочитайте [KNOWN-ISSUES.md](KNOWN-ISSUES.md)
> и оба аудита безопасности ([AUDIT-01](AUDIT-01-deepseek.md),
> [AUDIT-02](AUDIT-02-codex.md)) — версия содержит задокументированные
> уязвимости и не предназначена для production.

---

## 📋 Содержание

1. [Что нужно знать перед началом](#-что-нужно-знать-перед-началом)
2. [Быстрый старт: Telegram-бот](#1--telegram-бот-за-10-минут)
3. [Mini App (ISS.ME)](#2--mini-app-issme)
4. [APAS Connect (Python)](#3--apas-connect-python)
5. [APAS Connect (Qt/C++)](#4--apas-connect-qtc)
6. [Привязка Mini App к боту](#-привязка-mini-app-к-боту)
7. [Проверка после установки](#-проверка-после-установки)
8. [Устранение неполадок](#-устранение-неполадок)
9. [Безопасность перед публичным запуском](#-безопасность-перед-публичным-запуском)

---

## ⚠️ Что нужно знать перед началом

| Факт | Детали |
|---|---|
| **Версия** | `0.1.0-canary` — крайне нестабильная, только для ознакомления |
| **Обязательные ключи** | `TELEGRAM_BOT_TOKEN` + `GROQ_API_KEY` (проверка в `src/config.py`) |
| **Остальные ключи** | Опциональны — включают только соответствующие модели/функции |
| **Данные** | JSON-файлы в `data/` создаются автоматически при первом запуске |
| **Секреты** | Токены из старой истории **скомпрометированы** — получите новые (см. раздел «Безопасность») |
| **Порты** | Бот: long-polling (свободный порт). APAS Connect: **5000** (`127.0.0.1`). Mini App: 5000 (dev) |
| **ОС** | Бот — любая; APAS Connect Python — **Windows** (`winreg`, `tkinter`); Qt — Windows x64 |

### Что потребуется скачать/создать

| Ресурс | Где взять | Зачем |
|---|---|---|
| Токен Telegram-бота | [@BotFather](https://t.me/BotFather) | Обязателен |
| `GROQ_API_KEY` | [console.groq.com](https://console.groq.com/) | Обязателен (основной ИИ) |
| `GEMINI_API_KEY` | [aistudio.google.com](https://aistudio.google.com/) | Модели Gemini |
| Google Cloud проект | [console.cloud.google.com](https://console.cloud.google.com/) | Imagen (`/image`) |
| `YANDEX_API_KEY` | [console.yandex.cloud](https://console.yandex.cloud/) | YandexGPT |
| Яндекс Музыка токен | OAuth в профиле Яндекс | Режим «Алисы» |
| Python | [python.org](https://www.python.org/downloads/) | 3.10+ (рекомендуется 3.12/3.13) |

---

## 1. 🐍 Telegram-бот (за 10 минут)

### Шаг 1 — Клонировать

```bash
git clone https://github.com/pavelrakcheev/APAS-Telegram-Bot.git
cd APAS-Telegram-Bot
```

### Шаг 2 — Виртуальное окружение

```bash
python3 -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate          # Windows (cmd)
```

### Шаг 3 — Зависимости

```bash
pip install -r requirements.txt
```

> ⚠️ **Известная проблема v0.1:** в `requirements.txt` битая строка
> `google-cloud-aiplatform-` (без версии). Если `pip install` упадёт —
> удалите эту строку и поставьте явно:
> ```bash
> pip install "google-cloud-aiplatform>=1.90"
> ```

### Шаг 4 — Конфигурация

```bash
cp .env.example .env
```

Заполните `.env` (минимум — две строки):

```bash
TELEGRAM_BOT_TOKEN=1234567890:AAA...   # от @BotFather
GROQ_API_KEY=gsk_...                    # от console.groq.com

# Опционально:
# TELEGRAM_ID=ваш_id_для_админки
# ADMIN_PASSWORD=пароль_админа
# GEMINI_API_KEY=...
# YANDEX_API_KEY=...
# GOOGLE_CLOUD_PROJECT=...
# YANDEX_MUSIC_ADMIN_TOKEN=...
```

### Шаг 5 — Запуск

```bash
python main.py
```

Бот работает в режиме long-polling — внешний адрес и порт не нужны.
Ожидайте в консоли что-то вроде `Application started`.

### Альтернатива: запуск через Docker

Репозиторий содержит `Dockerfile`, `Mini App/Dockerfile` и
`docker-compose.yml` — бот и Mini App поднимаются одной командой:

```bash
cp .env.example .env        # впишите TELEGRAM_BOT_TOKEN и GROQ_API_KEY
docker compose up -d --build
```

- `bot` — работает с монтируемыми томами `./data` и `./Chats`;
- `mini-app` — доступен на `http://localhost:5000`, берёт данные из `./data`.

Остановка: `docker compose down`.

### Альтернатива: через Makefile

```bash
make setup      # venv + зависимости (фильтрует битую строку requirements)
make run        # python main.py
make test       # smoke-тест
make check      # проверка синтаксиса
make docker-up  # то же, что docker compose up -d --build
```

### Шаг 6 — Проверка

1. В Telegram найдите бота по имени из BotFather.
2. `/start` → пройдите регистрацию (простая или расширенная).
3. Отправьте любое сообщение — придёт ИИ-ответ через Groq
   (модель по умолчанию `openai/gpt-oss-120b`).

---

## 2. 📱 Mini App (ISS.ME)

Веб-профиль пользователя: Flask + HTML/JS, открывается кнопкой в боте.

### Локальный запуск

```bash
cd "Mini App"

# 1. Окружение
python3 -m venv .venv
source .venv/bin/activate

# 2. Зависимости
pip install -r requirements.txt

# 3. Данные пользователей (копия из бота!)
cp ../data/users_data.json users_data.json

# 4. Dev-сервер
python app.py        # → http://localhost:5000
```

### Деплой на Render.com (рекомендуется)

1. Аккаунт на [render.com](https://render.com).
2. **New Web Service** → укажите репозиторий с папкой `Mini App/`.
3. Параметры:
   - **Environment:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
4. После деплоя получите URL вида `https://your-app.onrender.com`.
5. Вставьте URL в кнопку WebApp бота (см. [Привязка](#-привязка-mini-app-к-боту)).

> ⚠️ Telegram открывает Web Apps **только по HTTPS**.

### Деплой на Heroku

В папке уже есть `Procfile` и `runtime.txt` (python-3.11.6):

```bash
cd "Mini App"
heroku create iss-me
git init && git add . && git commit -m "ISS.ME"
git push heroku main
```

> ⚠️ **Важно:** Mini App работает со **своей копией** `users_data.json`.
> В v0.1 она не синхронизируется с ботом автоматически — обновляйте вручную.

---

## 3. 💻 APAS Connect (Python)

Десктопный мост: показывает системную информацию ПК в боте по команде `/remote`.

> ⚠️ Только для **Windows** (используется `winreg`, `tkinter`).

### Установка и запуск

```bash
cd "APAS Connect"

# 1. Окружение
python3 -m venv .venv
source .venv/bin/activate

# 2. Зависимости
# ⚠️ В requirements.txt есть строка tkinter, которая ломает pip —
#    удалите её или ставьте пакеты явно:
pip install flask psutil requests pystray Pillow

# 3. Конфигурация
cp config.example.json config.json
#    при желании впишите bot_token (код его фактически не использует)

# 4. Запуск
python main.py
```

Программа свернётся в трей. Проверка API:

```bash
curl http://127.0.0.1:5000/ping
curl http://127.0.0.1:5000/system_info
```

### Сборка exe (Windows)

```bash
python build_exe.py        # → dist/APAS_Connect.exe (PyInstaller, onefile)
```

### Требование к размещению

Бот и APAS Connect должны работать **на одной машине** (или в одной сети) —
бот ходит на `http://localhost:5000` по команде `/remote` (`Commands/remote.py`).

---

## 4. 🖥 APAS Connect (Qt/C++)

Ремейк моста на Qt 6.9.3 / C++17 / MSVC 2022 (Windows x64).

### Сборка

```bash
cd "APAS Connect Qt"
cmake -S . -B build
cmake --build build --config Release
# → build/Release/APASConnectQt.exe
```

### Запуск

Запустите `APASConnectQt.exe` — окно с прогресс-барами CPU/RAM/диск,
кнопками «Get System Info», «Check API & Models», «Start Auto Update»
и трей-иконкой.

> ⚠️ **Известные баги v0.1** (см. [KNOWN-ISSUES.md](KNOWN-ISSUES.md) F10):
> проверка API идёт на порт 8080 вместо 5000; запускает отсутствующие
> `check_models.py` / `check_vertexai.py`; UI может фризиться до 40 с.

---

## 🔗 Привязка Mini App к боту

URL Mini App вставляется в кнопку WebApp в `Commands/profile.py`:

```python
from telegram import InlineKeyboardButton, WebAppInfo

keyboard = [[
    InlineKeyboardButton(
        "👤 Мой профиль",
        web_app=WebAppInfo(url="https://your-app.onrender.com")
    )
]]
```

После изменения — перезапустите бота.

---

## ✅ Проверка после установки

| Что | Как проверить | Ожидаемый результат |
|---|---|---|
| Бот жив | `/start` → регистрация | Приветствие, запись в `data/users_data.json` |
| ИИ работает | Обычное сообщение | Ответ модели Groq |
| Выбор моделей | `/models` | Список 18+ моделей |
| Профиль | `/profile` | Данные аккаунта ISS |
| Очки | `/points` | Баланс, история |
| ISS Play | `/games` | Регистрация игрового профиля |
| Blum | `/blum` | Приветствие психолога с фото |
| Alice | `/alice` | Режим YandexGPT + Музыка |
| Карты | `/maps` (геолокация) | Места рядом через Nominatim |
| Mini App | Кнопка WebApp в профиле | Страница ISS.ME по HTTPS |
| APAS Connect | `curl /ping`, `/remote` в боте | `{"status": "ok"}`, системные метрики |

---

## 🧯 Устранение неполадок

### `Missing required environment variables: ...`

`.env` не найден или пуст. Проверьте:
- файл называется именно `.env` и лежит в корне репозитория;
- в нём есть `TELEGRAM_BOT_TOKEN` и `GROQ_API_KEY`;
- бот запускается из корня (`python main.py`, не `python Commands/main.py`).

### Ошибка при `pip install -r requirements.txt`

Известная проблема v0.1 — битая строка `google-cloud-aiplatform-`.
Удалите её из файла и выполните:

```bash
pip install "google-cloud-aiplatform>=1.90"
pip install -r requirements.txt
```

### Бот запустился, но не отвечает

1. Проверьте токен в BotFather — он не должен начинаться со `your_`.
2. Модель по умолчанию отключена провайдером? Выберите другую: `/models`.
3. Groq-ключ активен: [console.groq.com](https://console.groq.com/) → API Keys.

### Mini App показывает «нет данных»

`users_data.json` не скопирован в папку Mini App, либо данные устарели:
```bash
cp ../data/users_data.json users_data.json   # из папки Mini App
```

### `/remote` не работает

1. APAS Connect запущен? `curl http://127.0.0.1:5000/ping`.
2. Бот и APAS Connect на одной машине? (localhost ≠ удалённый сервер).
3. Порт не занят другим процессом? (в v0.1 — всегда 5000).

### Модели Groq «не найдены» / «отключены»

Часть моделей (Kimi K2, Qwen3 32B, Llama 4, Llama 3.1/3.3, GPT OSS 20B)
депрецирована провайдерами в 2025–2026 гг. Выберите актуальную через
`/models` (например, `openai/gpt-oss-120b`).

---

## 🔐 Безопасность перед публичным запуском

> **Обязательный чек-лист.** Версия v0.1 содержит подтверждённые уязвимости —
> не запускайте её публично без исправлений.

1. **Ротация секретов.** Токены, фигурировавшие в исходной истории проекта,
   считаются скомпрометированными:
   - [@BotFather](https://t.me/BotFather) → `/revoke` → новый токен;
   - Groq/Gemini/Яндекс → удалить и создать новые API-ключи;
   - сменить `ADMIN_PASSWORD`;
   - удалить PFX-сертификаты из распространяемых материалов.
2. **Mini App (S2 — критично):**
   - закрыть `/api/debug` (сейчас отвечает без авторизации);
   - добавить проверку Telegram `initData` в `app.py`;
   - убрать `CORS(app)` / ограничить домены;
   - не доверять `user_id` из запроса — брать из initData.
3. **`/remote` (S4):** ограничить команду только администраторами.
4. **`/reports`:** починить маршрутизацию `report_` / `report_detail_`
   (сейчас IDOR скрыт ошибкой роутера).
5. **Секреты в git:** `.env`, `data/*.json`, `Chats/*` уже в `.gitignore` —
   перед push проверьте: `git status` не должен показывать эти файлы.
6. **Проверка:** после исправлений запустите повторный аудит
   (например, Codex Security / secret scan).

Подробности каждой проблемы: [KNOWN-ISSUES.md](KNOWN-ISSUES.md),
[AUDIT-01-deepseek.md](AUDIT-01-deepseek.md), [AUDIT-02-codex.md](AUDIT-02-codex.md).
