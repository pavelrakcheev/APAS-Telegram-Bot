# AGENTS.md — Полное техническое руководство для ИИ-агентов

## Что это за файл

Этот документ предназначен для LLM-агентов (ChatGPT, DeepSeek, Codex,
OpenCode, Copilot, Cursor и др.), работающих с кодовой базой APAS.
Он содержит **абсолютно всё** об архитектуре, структуре, багах, ограничениях
и conventions проекта, чтобы ИИ мог точно выполнять задачи.

---

## 1. Обзор проекта

**APAS** (Адаптивная Аналитическая Предиктивная Система) — экспериментальная
экосистема вокруг Telegram-бота с мультимодельным ИИ.

- **Версия:** 0.1.0-canary (первая публичная, крайне нестабильная)
- **Статус:** canary release, 26 задокументированных проблем
- **Лицензия:** MIT
- **Автор:** Pavel Rakcheev

### Ключевые факты
- Весь полезный Python-код: ~9 089 строк
- `Commands/`: ~5 200 строк (22 модуля)
- Callback-кнопки: ~60 типов в `main.py`
- ИИ-модели: 18+ (Groq/Gemini/YandexGPT)
- JSON-хранилища: 5 файлов + журналы `Chats/`

---

## 2. Архитектура

### Точка входа
`main.py` — единый роутер всех команд и callback-кнопок (60+ типов).
Бот запускается через `run_polling()` (long-polling, без webhook).

### Центральная функция
`generate_ai_response(user_id, message, model, ...)` — диспетчер ИИ,
вызывает модули из `Models/` в зависимости от выбранной модели.

### Модули ИИ (`Models/`)
| Модуль | Провайдер | Модели | Стриминг |
|---|---|---|---|
| `groq.py` | Groq SDK 0.33 | GPT OSS 20B/120B, Kimi K2, Qwen3 32B, Llama 3.1/3.3/4 | ✅ |
| `gemini.py` | google-generativeai 0.8.5 | Gemini 2.0 Flash/Lite, 2.5 Flash/Pro | ❌ |
| `yandex.py` | requests (Yandex Cloud API) | YandexGPT 4 Lite, 5 Lite, 5 Pro, 5.1 Pro | ❌ |

### Стриминг (только Groq)
`asyncio.Queue` + `run_in_executor` → ответ редактируется по фрагментам
(`editMessageText`). Риск flood limits и превышения 4096 символов.

### Хранилища (`data/*.json`)
| Файл | Содержимое |
|---|---|
| `users_data.json` | Пользователи ISS: имя, возраст, город, username, очки, модель |
| `points_transactions.json` | История ISS Points |
| `reports.json` | Отчёты о проблемах |
| `iss_play_accounts.json` | Игровые аккаунты |
| `alice_states.json` | Состояния «Алисы» |

**Проблемы JSON (A1):** относительные пути, нет file lock, нет миграций,
параллельные записи могут потерять данные, повреждённый JSON → `{}`.

### Диалоги (`Chats/`)
`Chats/<user_id>/chat.txt` — все переписки открытым текстом без
retention-политики. **Не используются как контекст модели** — каждый
запрос = системный промпт + текущее сообщение.

---

## 3. Подсистемы экосистемы

### ISS — Intelligence Social System
- Единый аккаунт пользователя ( имя, возраст, город, username, очки)
- Регистрация: `/start` (простая 3 шага / расширенная 5 шагов)
- Профиль: `/profile`, deep-link `start=profile_<username>`
- Статистика: `/iss`
- **Заглушки:** «Написать сообщение», «Добавить в друзья»

### ISS Play — Игровой профиль
- `Commands/games.py` (205 строк)
- Регистрация 3 этапа, генерация никнеймов через Groq (`gpt-oss-120b`)
- Привязка к аккаунту ISS
- **Заглушки:** достижения, рейтинг, игры

### ISS Points — Внутренняя валюта
- `Commands/points.py`, `Commands/addpoints.py`
- Начисление администратором (`/addpoints`)
- История с пагинацией в `points_transactions.json`
- **Проблема:** дефолт `60` в профиле vs `0` в points.py (F8)

### ISS.ME — Mini App (Flask)
- `Mini App/app.py` (Flask 3.1.2)
- Деплой: Render (`https://iss-app-for-telegram-bot.onrender.com`)
- **КРИТИЧЕСКАЯ УЯЗВИМОСТЬ (S2):** нет проверки initData, `/api/debug`
  открыт, CORS для всех доменов, mass assignment
- Данные: копия `users_data.json` (устаревшая, 4 записи vs 11)

### Blum — Психолог
- `Commands/blum.py` (100 строк)
- Приветствие по времени суток (`get_blum_greeting()`)
- Фото `src/blum.jpg`
- **Заглушки:** настройка, диалог
- **Баг:** показывает чужой текст заглушки

### Alice AI Mode — ИИ-ассистент
- `Modes/Alice/alice.py` (376 строк)
- Две модели: YandexGPT 5 Lite / 5.1 Pro
- Состояние в `data/alice_states.json`
- **Баг F11:** ключи JSON строки, код ищет int → состояние теряется
- **Музыка:** `Modes/Alice/Commands/yamusic.py` (461 строка)
  - Яндекс Музыка через `yandex-music` 2.1.0
  - Музыкальные ключевые слова перехватываются до ИИ
  - **Нет воспроизведения** — только информация о треках
  - **Нет персональной «Моей волны»** без OAuth-токена

### One Core API — Alpha
- Мультиплатформенное ядро: Telegram + VK (alpha)
- VK-интеграция: `python-vk-api`, основные команды работают
- Скриншоты: `docs/media/images/APAS on VK (alpha test).jpg`
- **Проблема:** нет выделенного транспортного слоя, код адаптера не抽象изирован

### APAS Connect (Python)
- `APAS Connect/main.py` — Flask API + трей + tkinter
- Слушает `localhost:5000/system_info`
- **Проблемы:** `tkinter` в requirements.txt (F11), `main_old.py` мёртвый

### APAS Connect (Qt/C++)
- `APAS Connect Qt/` — Qt 6.9.3, C++17, MSVC 2022
- **Проблемы F10:** порт 8080 vs 5000, мёртвые скрипты, UI-фризы

---

## 4. Безопасность (S1–S8)

| ID | Проблема | Severity | Статус |
|---|---|---|---|
| S1 | Секреты скомпрометированы (токены, пароль, PFX) | 🔴 Critical | Требует ротации |
| S2 | Mini App: нет initData, `/api/debug` открыт, CORS | 🔴 Critical | Подтверждено live |
| S3 | IDOR в myreports | 🔴 Critical | Скрыто багом F1 |
| S4 | `/remote` без проверки прав | 🔴 Critical | Открыто |
| S5 | RCE в generator.py (eval + path traversal) | 🟠 High | Недостижимо |
| S6 | Переписки и PII открытым текстом | 🟠 High | Открыто |
| S7 | «Удаление профиля» не удаляет данные | 🟠 High | Открыто |
| S8 | Перебор публичных профилей по ID | 🟠 High | Открыто |

**Все секреты из репозитория исключены**, но требуют ротации.
Перед любым реальным запуском: отзовите токены, смените пароль,
удалите PFX.

---

## 5. Функциональные ошибки (F1–F12)

### F1. Сломана маршрутизация callback отчётов
- `report_detail_*` перехватывается `report_*` раньше (main.py:171)
- `myreports_detail_*` уходит в `handle_myreports_callback` без ветки
- **Влияние:** детальный просмотр и смена статусов недоступны

### F2. `is_guest_mode()` без аргумента
- `Commands/reports.py` строки 195, 539, 616 — `TypeError`

### F3. `/image` не зарегистрирована
- `Commands/image.py` импортирован, но нет `CommandHandler`
- Дополнительно: deprecated SDK, удалённые модули Vertex AI

### F4. Гостевые callback-кнопки
- `guest_back` вызывает `start_command` с `update.message is None`

### F5. Недоступные кнопки
- `report_send_empty`, `blum_settings`, `image_edit`,
  `addpoints_confirm` (pass), `blum_start_dialog`

### F6. Режим «Алисы»
- Ключи JSON строки → потеря состояния после рестарта
- Команды `/exit` и др. не зарегистрированы как CommandHandler
- `parse_mode='Markdown'` без экранирования → битая разметка
- Фейковые треки при ошибках API
- «Воспроизведение» не воспроизводит

### F7. Mini App frontend
- `getElementById('issCity')` — элемента нет → JS-ошибка
- Дата `dd.mm.YYYY` → `new Date()` → `Invalid Date`
- Баланс захардкожен `60`
- Погода — мок
- `tg.shareUrl` не существует в Mini Apps API

### F8. Расхождение дефолтов очков
- `60` в profile.py / Mini App, `0` в points.py / addpoints.py

### F9. Кодировка и отладка
- 6 символов `�` в Commands
- 32+ `print()` в production

### F10. APAS Connect Qt
- Порты: 8080 vs 5000
- Мёртвые скрипты check_models.py / check_vertexai.py
- UI-фризы ~40 сек
- Нет `/ping`

### F11. APAS Connect Python
- `tkinter` в requirements.txt → pip падает
- `main_old.py` — мёртвый код
- `winreg` — Windows-only

### F12. Производительность
- Gemini/Yandex синхронно в async → блокируют event loop
- `requests.post` к Yandex без timeout
- Groq: flood limits, лимит 4096 символов
- Нет error handler, лимитов, content moderation
- Контекст диалога не передаётся модели

---

## 6. Архитектурные ограничения (A1–A6)

### A1. JSON без защиты
Нет file lock, миграций, схем, резервных копий.

### A2. Несогласованность
- Mini App: устаревшая копия `users_data.json`
- Python- и Qt-версии Connect: разные JSON-схемы
- Три реализации работы с `users_data`

### A3. Дублирование кода
- `load/save_reports` — 3 копии
- `load/save_points_transactions` — 2 копии
- Тумблеры уведомлений — 2 копии
- Рендер профиля — 4 копии
- `Modes/Alice/Commands/{commands,modes,exit}.py` — мёртвые дубли

### A4. Неиспользуемый код
- `Commands/generator.py` (625 строк) — нигде не вызывается
- `decorator guest_mode_check` — не применяется
- `Commands/image.py` — не зарегистрирована

### A5. Зависимости
- `google-generativeai 0.8.5` — EOL 30.11.2025
- Vertex AI SDK — генеративные модули удалены после 24.06.2026
- `requirements.txt`: битая строка `google-cloud-aiplatform-`
- Python 3.7+ заявлен, фактически 3.10+

### A6. Инфраструктура
- ✅ Тесты: pytest, 39 тестов (Models, Commands, shared)
- ✅ CI: ruff lint, tests, coverage, pip-audit, secret scan
- Нет `setMyCommands`
- Только `run_polling()`

---

## 7. Структура файлов

```
Bot/
├── main.py                 # Роутер команд и 60+ callback
├── shared.py               # Утилиты: users_data, admin, ISS Play, промпты
├── requirements.txt        # ⚠️ содержит битую строку
├── .env.example            # Шаблон конфигурации
├── src/config.py           # Загрузка .env
├── src/blum.jpg            # Фото для /blum
├── Commands/               # 22 модуля команд (~5 200 строк)
│   ├── about.py, acc_stat.py, addpoints.py, blum.py, commands.py
│   ├── createpost.py, games.py, generator.py (⚠️ мёртвый)
│   ├── guest.py, image.py (⚠️ не зарегистрирована)
│   ├── iss.py, models.py, myreports.py, notifications.py
│   ├── points.py, profile.py, remote.py, report.py, reports.py
│   ├── settings.py, start.py, tools.py
├── Models/                 # ИИ-провайдеры
│   ├── groq.py, gemini.py, yandex.py
│   └── src/                # Логотипы моделей
├── Modes/Alice/            # Alice AI Mode
│   ├── alice.py            # Режим: диалог, 2 модели, состояние
│   ├── yamusic.py          # ⚠️ мёртвый дубликат
│   ├── src/Alice.png
│   └── Commands/
│       ├── yamusic.py      # Актуальная интеграция Яндекс Музыки (461 строка)
│       ├── commands.py, exit.py, modes.py  # ⚠️ дубли
├── Modules/
│   ├── arc_maps.py         # Карты (730 строк)
│   └── arc_weather.py      # Погода (мок)
├── Mini App/               # ISS.ME (Flask)
│   ├── app.py, index.html, points.html, settings.html
│   ├── styles.css, Procfile, runtime.txt, requirements.txt
│   └── src/                # SVG-иконки
├── APAS Connect/           # Python-мост
│   ├── main.py, main_old.py, build_exe.py
│   ├── config.example.json, test_api.py, src/
├── APAS Connect Qt/        # Qt/C++ ремейк
│   ├── CMakeLists.txt, main.cpp, MainWindow.cpp/.h
│   ├── HttpServer.cpp/.h, SystemMonitor.cpp/.h, TrayIcon.cpp/.h
├── data/                   # JSON (не публикуются)
├── Chats/                  # Журналы (не публикуются)
├── tests/               # Тесты
│   ├── smoke_test.py     # Структурный smoke-тест
│   ├── conftest.py       # Общие фикстуры
│   ├── test_shared.py    # Тесты shared.py
│   ├── test_models/      # Тесты моделей ИИ
│   └── test_commands/    # Тесты команд
├── .devcontainer/        # Dev Container для VS Code
├── .pre-commit-config.yaml  # Pre-commit hooks
├── pyproject.toml        # Конфигурация pytest, ruff, bandit
├── requirements-dev.txt  # Зависимости для разработки
├── assets/covers/          # Обложки экосистемы
├── assets/logos/           # Иконки инструментов (SVG)
├── docs/                   # Документация
├── .github/workflows/      # CI/CD
├── Dockerfile, docker-compose.yml, Makefile
├── LICENSE (MIT), README.md, SECURITY.md, CONTRIBUTING.md, CHANGELOG.md
```

---

## 8. Команды бота

| Команда | Доступ | Описание | Файл |
|---|---|---|---|
| `/start` | Все | Регистрация/приветствие | `start.py` |
| `/guest` | Все | Гостевой вход | `guest.py` |
| `/signup` | Гости | К регистрации | `guest.py` |
| `/commands` | Все | Список команд | `commands.py` |
| `/about` | Все | О системе | `about.py` |
| `/profile` | Пользователи | Профиль ISS | `profile.py` |
| `/points` | Пользователи | ISS Points | `points.py` |
| `/models` | Пользователи | Выбор ИИ-модели | `models.py` |
| `/settings` | Пользователи | Настройки | `settings.py` |
| `/notifications` | Пользователи | Рассылки | `notifications.py` |
| `/report` | Пользователи | Подать отчёт | `report.py` |
| `/myreports` | Пользователи | Мои отчёты | `myreports.py` |
| `/games` | Пользователи | ISS Play | `games.py` |
| `/blum` | Пользователи | Психолог | `blum.py` |
| `/alice` | Пользователи | Алиса (YandexGPT + Музыка) | `alice.py` |
| `/acc_stat` | Пользователи | Статус аккаунта | `acc_stat.py` |
| `/iss` | Пользователи | Статистика ISS | `iss.py` |
| `/remote` | Все ⚠️ | Инфо о ПК (без проверки прав!) | `remote.py` |
| `/reports` | Админ | Панель отчётов | `reports.py` |
| `/addpoints` | Админ | Начисление очков | `addpoints.py` |
| `/createpost` | Админ | Создание поста | `createpost.py` |
| `/tools` | Админ | Системные операции | `tools.py` |

---

## 9. Конфигурация (`.env`)

```bash
TELEGRAM_BOT_TOKEN=...     # ✅ Обязателен
GROQ_API_KEY=...           # ✅ Обязателен
GEMINI_API_KEY=...         # Опционально
GOOGLE_CLOUD_PROJECT=...   # Для Imagen
GOOGLE_CLOUD_LOCATION=us-central1
YANDEX_API_KEY=...         # Для YandexGPT
YANDEX_MUSIC_ADMIN_TOKEN=...  # Для Яндекс Музыки
TELEGRAM_ID=...            # ID администратора
ADMIN_PASSWORD=...         # Секретная фраза
```

Загрузка: `src/config.py` через `python-dotenv`.

---

## 10. ИИ-модели и их статус

### Актуальные (используются)
- `openai/gpt-oss-120b` — модель по умолчанию, стриминг ✅
- `openai/gpt-oss-20b` — быстрая модель
- `qwen-qwq-32b` — рассуждения
- `gemini-2.5-flash`, `gemini-2.5-pro` — Gemini
- `yandexgpt-5-lite`, `yandexgpt-5.1` — YandexGPT

### Депрецированы/отключены
- Groq: Kimi K2, Qwen3 32B, Llama 3.1/3.3/4 Maverick/Scout
- Gemini: 2.0 Flash Exp/Lite (отключены)
- YandexGPT 4 Lite (отсутствует в каталоге)

---

## 11. CI/CD

### `.github/workflows/ci.yml`
- Gitleaks secret scan ✅
- Forbidden files ✅
- Python compileall (43 файла) ✅
- pip-audit (informational, continue-on-error) ⚠️ 25 CVEs
- Markdown links (lychee) ✅

### `.github/workflows/pages.yml`
- MkDocs Material build
- GitHub Pages deploy

### `.github/workflows/release.yml`
- On tag `v*`: Windows exe build + GitHub Release

### Dependabot
- pip + github-actions обновления
- 3 PR (#1–#3) уже созданы

---

## 12. Docker

### Бот
```dockerfile
FROM python:3.12-slim
# Фильтрация битой строки requirements через grep
```

### Mini App
```dockerfile
FROM python:3.11-slim
```

### docker-compose.yml
```yaml
services:
  bot: ./Dockerfile
  mini-app: ./Mini App/Dockerfile
```

---

## 13. Makefile

```bash
make setup     # venv + pip install
make run       # python main.py
make test      # tests/smoke_test.py
make check     # python -m compileall
make docker-up # docker compose up -d --build
make clean     # удаление кеша
```

---

## 14. Правила работы (для ИИ-агентов)

### Чего НЕЛЬЗЯ удалять
- `generator.py`, `main_old.py`, `Modes/Alice/yamusic.py` (старая версия)
- `Modes/Alice/Commands/{commands,exit,modes}.py` (дубли, но часть кодовой базы)
- `Commands/image.py` (не зарегистрирована, но есть код)
- Любые файлы в `data/`, `Chats/`, `APAS Connect/`, `APAS Connect Qt/`

### Что можно чинить
- Баги F1–F12 (с осторожностью)
- Архитектурные проблемы A1–A6
- Добавление новых функций
- Рефакторинг (без удаления мёртвого кода — ограничение пользователя)

### conventions
- Python: 4 пробела, type hints желательны
- YAML: 2 пробела
- Коммиты: conventional commits
- Branch: `main` (protected, no force push)
- PR: через GitHub (protected branch)
- Лицензия: MIT

### requirements.txt
⚠️ Содержит битую строку `google-cloud-aiplatform-` без версии.
При установке фильтровать: `grep -v "google-cloud-aiplatform-$" requirements.txt | pip install -r /dev/stdin`

### Формат данных
- Все данные: JSON в `data/`
- Ключи пользователей: Telegram ID (int), но в JSON хранятся как строки
- Формат дат: varies (dd.mm.YYYY в Mini App, unix timestamps в остальном)

---

## 15. Известные паттерны

### Роутинг callback
`main.py` обрабатывает все callback через `button_callback`:
```python
if data.startswith('report_'):
    # обработка отчётов (но перехватывает report_detail_! — баг F1)
elif data.startswith('myreports_'):
    # обработка моих отчётов
# ... ~60 веток
```

### Загрузка данных
```python
import json
def load_data(filename):
    try:
        with open(f'data/{filename}', 'r') as f:
            return json.load(f)
    except:
        return {}
```

### Админ-проверка
```python
def is_admin(user_id):
    return str(user_id) == os.getenv('TELEGRAM_ID')
```

### ИИ-вызов
```python
from Models.groq import generate_groq_response
response = generate_groq_response(message, model, system_prompt, streaming)
```

---

## 16. Типичные ошибки при работе

1. **Забыть про битую строку** в requirements.txt → pip install падает
2. **Использовать int ключи** в JSON → Alice-состояние теряется (F6/F11)
3. **Не проверять `update.message is None`** → AttributeError в callback
4. **Забыть про дубли** функций → правка в одном месте, не в другом
5. **Вызывать `is_guest_mode()` без аргумента** → TypeError (F2)
6. **Использовать deprecated SDK** → google-generativeai, vertexai
7. **Игнорировать CORS/Auth** в Mini App → уязвимости (S2)
8. **Не фильтровать битую строку** при Docker/CI/Makefile сборке
