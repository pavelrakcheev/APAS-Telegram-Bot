# APAS — Документация

**Адаптивная Аналитическая Предиктивная Система** — экспериментальная экосистема вокруг Telegram-бота с мультимодельным ИИ.

> ⚠️ Версия `0.1.0-canary` — крайне нестабильная, только для ознакомления.

---

## Быстрый старт

```bash
git clone https://github.com/pavelrakcheev/APAS-Telegram-Bot.git
cd APAS-Telegram-Bot
python3 -m venv .venv && source .venv/bin/activate
cp .env.example .env            # впишите TELEGRAM_BOT_TOKEN и GROQ_API_KEY
pip install -r requirements.txt
python main.py
```

> Нужны только два ключа: токен бота от [@BotFather](https://t.me/BotFather) и `GROQ_API_KEY` от [console.groq.com](https://console.groq.com/).

---

## Экосистема

| Подсистема | Описание | Статус |
|---|---|---|
| **ISS** | Единый аккаунт пользователя, профили, поиск | 🟡 Работает |
| **ISS Play** | Игровой профиль, никнеймы через Groq | 🟡 Работает |
| **ISS Points** | Внутренняя валюта, начисление админом | 🟢 Работает |
| **ISS.ME** | Веб-профиль (Flask, Telegram Mini App) | 🟠 Опасно |
| **Blum** | Психологическая поддержка | 🟡 Работает |
| **Alice AI Mode** | ИИ-ассистент + Яндекс Музыка | 🟡 Работает |
| **One Core API** | Мультиплатформенное ядро (концепт) | 🔴 Концепт |

---

## Документация

<div class="grid cards" markdown>

-   :material-cog:{ .lg .middle } __Установка и запуск__

    ---

    Пошаговая инструкция для всех компонентов: бот, Mini App, APAS Connect, Docker.

    [:octicons-arrow-right-24: SETUP](SETUP.md)

-   :material-domain:{ .lg .middle } __Архитектура__

    ---

    Схемы, потоки данных, хранилища, ключевые особенности.

    [:octicons-arrow-right-24: ARCHITECTURE](ARCHITECTURE.md)

-   :material-bug:{ .lg .middle } __Известные проблемы__

    ---

    S1–S8, F1–F12, A1–A6 — все баги и ограничения v0.1.

    [:octicons-arrow-right-24: KNOWN-ISSUES](KNOWN-ISSUES.md)

-   :material-shield-search:{ .lg .middle } __Аудит безопасности__

    ---

    Два независимых аудита: DeepSeek + Codex Security.

    [:octicons-arrow-right-24: Аудит №1](AUDIT-01-deepseek.md) · [:octicons-arrow-right-24: Аудит №2](AUDIT-02-codex.md)

-   :material-shield-lock:{ .lg .middle } __Политика безопасности__

    ---

    Как сообщать об уязвимостях, что делать с секретами.

    [:octicons-arrow-right-24: SECURITY](https://github.com/pavelrakcheev/APAS-Telegram-Bot/blob/main/SECURITY.md)

-   :material-account-group:{ .lg .middle } __Участие__

    ---

    Правила контрибуций, шаблоны Issue/PR.

    [:octicons-arrow-right-24: CONTRIBUTING](https://github.com/pavelrakcheev/APAS-Telegram-Bot/blob/main/CONTRIBUTING.md)

</div>

---

## Живой бот

[@Intelligence_playground_bot](https://t.me/Intelligence_playground_bot) — попробуйте `/start`, `/alice`, `/blum`, `/games`.

Mini App: [iss-app-for-telegram-bot.onrender.com](https://iss-app-for-telegram-bot.onrender.com)
