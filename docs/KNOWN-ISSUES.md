# Известные проблемы и ограничения — v0.1.0-canary

> Этот документ фиксирует все баги, уязвимости и ограничения первой публичной
> версии, выявленные в ходе двух независимых аудитов:
>
> - [Аудит №1 — DeepSeek V4 Flash (Max) в OpenCode Desktop](AUDIT-01-deepseek.md)
> - [Аудит №2 — ChatGPT Codex (GPT-5.6 Sol High) + Codex Security](AUDIT-02-codex.md)
>
> Ни одна из перечисленных ниже проблем в этой версии **не исправлена** —
> проект публикуется «как есть» в учебных целях.

---

## 🔴 Критические проблемы безопасности

### S1. Секреты считаются скомпрометированными

В истории разработки существовали реальные значения:

- `.env`: `TELEGRAM_BOT_TOKEN`, `GROQ_API_KEY`, `GEMINI_API_KEY`,
  `YANDEX_API_KEY`, `YANDEX_MUSIC_ADMIN_TOKEN`, `TELEGRAM_ID`,
  `ADMIN_PASSWORD`, идентификаторы Google Cloud;
- `APAS Connect/config.json`: отдельный Telegram-токен (кодом не используется);
- `APAS Connect Qt/build/Release/APASConnectTestCert.pfx/.cer`: самоподписанный
  тестовый сертификат с приватным ключом (пароль — в `APASConnectConfig.yml`).

Из репозитория v0.1 все эти файлы **исключены** (`.gitignore`, шаблоны
`.env.example` / `config.example.json`), но:

> **Необходимо:** отозвать токен бота через @BotFather, перевыпустить все
> API-ключи, сменить пароль администратора, удалить PFX из распространяемых
> материалов. Проверить историю облачных загрузок, архивов и бэкапов.

### S2. Mini App не аутентифицирует пользователей (подтверждено на живом сервисе)

- `Mini App/app.py`: `CORS(app)` открыт для всех доменов;
- backend не проверяет подпись `Telegram.WebApp.initData` и доверяет
  числовому `user_id` от клиента;
- `/api/debug` отдаёт список `user_id`, пути файлов и содержимое каталога
  сервера — **доступно без авторизации**;
- `POST /api/user-settings` — mass assignment: можно записать произвольные
  поля (например, `setup_completed`) любому пользователю;
- запись JSON без блокировок и атомарного переименования.

Проверка опубликованного сервиса (Render) подтвердила:
`/api/debug` → 200 без авторизации; `Origin: https://attacker.example` →
`Access-Control-Allow-Origin: https://attacker.example`.

### S3. IDOR в myreports.py

`handle_myreports_detail_callback` загружает отчёты по `user_id` из
callback-данных без проверки `query.from_user.id`. В v0.1 уязвимость
**скрыта ошибкой маршрутизации** (см. F1): callback `myreports_detail_*`
уходит в общий обработчик и молча игнорируется. **После исправления
маршрутизации IDOR станет достижимым, если одновременно не добавить
проверку владельца.**

### S4. `/remote` доступен всем пользователям

`Commands/remote.py` не проверяет права: любой пользователь может запросить
системную информацию хост-машины бота (localhost:5000). Дополнительно:
schemas Python-версии Connect (`ram_total_gb` и т.д.) не совпадают с тем,
что ожидает бот (`ram_total`), поэтому часть полей отображается как
«Неизвестно».

### S5. Условная RCE в Commands/generator.py

`generator.py` (не используется ни одним обработчиком, но присутствует в
репозитории) содержит цепочку: path traversal через `app_name`, серверный
`eval()` в Python, клиентский `eval()` в JS, stored XSS через `innerHTML`,
`app.run(debug=True, host='0.0.0.0')`. **Не является достижимой поверхностью
атаки в v0.1, но должен быть удалён или переписан до включения.**

### S6. Данные и переписки сохраняются открытым текстом

- `Chats/<user_id>/chat.txt` — все диалоги в открытом виде, без срока
  хранения и retention-политики;
- гостевой режим и `/blum` создают ложное ожидание несохранения переписок —
  гостевые сообщения и диалоги «психолога» пишутся в те же файлы;
- PII профиля (имя, возраст, город) передаётся внешним ИИ-провайдерам
  без отдельного согласия.

### S7. «Удаление профиля» не удаляет данные

`Commands/profile.py` (`confirm_delete`) очищает только `context.user_data`
и сохраняет пустой объект. Не удаляются: запись пользователя, чаты, отчёты,
история очков, состояние Alice, ISS Play-аккаунт, копия профиля Mini App.
Сообщение пользователю о «полном и необратимом удалении» не соответствует
фактическому поведению.

### S8. Перебор публичных профилей

Deep-link `start=profile_<identifier>` (`Commands/start.py`) принимает и
username, и числовой Telegram ID. Зарегистрированный пользователь может
перебором ID получать имя, возраст, город и дату регистрации других
пользователей. Механизма согласия на публичность профиля нет.

---

## 🟠 Функциональные ошибки

### F1. Сломана маршрутизация callback системы отчётов

`main.py`:
- `data.startswith('report_')` (стр. 171) перехватывает `report_detail_*`
  раньше, чем тот попадает в `handle_report_detail_callback` (стр. 181) —
  детальный просмотр и смена статусов отчётов администратором **недоступны**;
- `myreports_detail_*` уходит в `handle_myreports_callback`, где нет
  соответствующей ветки (есть только `else: return`) — просмотр деталей
  своих отчётов недоступен.

### F2. `is_guest_mode()` без аргумента

В `Commands/reports.py` на строках 195, 539 и 616 функция вызывается без
обязательного параметра `user_data` → `TypeError` при каждом callback
админ-панели отчётов.

### F3. `/image` не зарегистрирована

`Commands/image.py` (`image_command`) импортирован, но в `main.py` нет
`CommandHandler("image", ...)` — генерация изображений недоступна из
нормального интерфейса. Дополнительно: кнопка `image_edit` не обрабатывается,
используется deprecated SDK (`google-generativeai`) и удалённые из
поддерживаемого Vertex AI SDK генеративные модули.

### F4. Гостевые callback-кнопки

`Commands/guest.py`:
- `guest_back` вызывает `start_command` с callback-`update`, у которого
  `update.message is None`;
- `guest_commands` аналогично вызывает обработчик обычной команды.
Ожидаемы `AttributeError` или обращение к отсутствующему `message`.

### F5. Недоступные кнопки интерфейса

| Кнопка | Файл | Статус |
|---|---|---|
| `report_send_empty` («Отправить отчёт» без описания) | report.py:189 | создаётся, не обрабатывается |
| `blum_settings` («Настроить Блюм») | blum.py | не обрабатывается |
| `image_edit` («Редактировать») | image.py | не обрабатывается |
| `addpoints_confirm` | addpoints.py | мёртвая ветка (`pass`) |
| `blum_start_dialog` | blum.py | показывает чужой текст вместо диалога |

### F6. Режим «Алисы»

- ключи `alice_states.json` после чтения — строки, часть кода ищет целочисленный
  ID → состояние теряется после перезапуска;
- `/exit`, `/commands`, `/modes`, `/music`, `/yamusic` проверяются внутри
  текстового обработчика, но основной handler исключает `filters.COMMAND`,
  а отдельные `CommandHandler` не зарегистрированы;
- ответ YandexGPT отправляется с `parse_mode='Markdown'` без экранирования —
  модель может сформировать невалидную разметку;
- при ошибках API возвращаются тестовые «фейковые» треки, внешне похожие
  на реальные;
- «воспроизведение музыки» возвращает сведения о треке, но не передаёт аудио;
- «Алиса» — это не официальная Яндекс.Алиса, а YandexGPT с системным промптом.

### F7. Mini App frontend

- `index.html:129`: `getElementById('issCity')` — элемента нет → JS-ошибка,
  город из профиля не отображается;
- backend отдаёт дату в формате `dd.mm.YYYY`, frontend передаёт её в
  `new Date()` → `Invalid Date`;
- баланс очков захардкожен (`60`) в `index.html` и `points.html`;
- погода полностью фиктивна (координаты Москвы захардкожены);
- `tg.shareUrl` отсутствует в официальном Telegram Mini Apps API (есть
  `shareMessage`, `shareToStory`, `openTelegramLink`).

### F8. Расхождение дефолтов очков

`points` по умолчанию: `60` в `profile.py` и Mini App, `0` в `points.py` /
`addpoints.py` — баланс «прыгает» в зависимости от экрана.

### F9. Кодировка и отладка

- 6 символов повреждённой кодировки (`�`) в `Commands/commands.py`,
  `Commands/reports.py` и др.;
- не менее 32 операторов `print` в production-коде, включая
  `print("DEBUG: ...")` в `Commands/start.py`.

### F10. APAS Connect Qt

- проверка API на порту **8080**, сервер слушает **5000** (MainWindow.cpp);
- запуск отсутствующих `check_models.py` / `check_vertexai.py`;
- `waitForFinished(10000)` ×4 в UI-потоке → зависание окна до ~40 сек;
- HTTP-роутер использует `contains("GET /system_info")` — совпадёт и с
  `/system_infoevil`; нет `Content-Length` и полноценного парсера;
- название процессора захардкожено как `x64 Processor`;
- нет `/ping` (в отличие от Python-версии).

### F11. APAS Connect Python

- `requirements.txt` содержит `tkinter` (часть стандартной библиотеки,
  не устанавливается через pip) — `pip install -r requirements.txt` упадёт;
- `winreg` — строго Windows-ориентировано;
- токен в `config.json` кодом не используется;
- `main_old.py` — устаревшая копия со сломанным кодом (NameError при
  закрытии стартового окна);
- тест `test_api.py` запускает GUI-приложение — не изолированный тест.

### F12. Производительность и надёжность

- Gemini и Yandex вызываются синхронно внутри `async def` — блокируют
  event loop; `requests.post` к Yandex без timeout;
- карты: синхронные HTTP-запросы и последовательные `sleep(1.1)` внутри
  async-обработчика;
- Groq: `edit_text` на каждый фрагмент — риск flood limits и превышения
  лимита 4096 символов;
- нет лимитов запросов, ограничения длины промпта, quota/cost control,
  content moderation;
- нет `Application.add_error_handler`;
- контекст диалога модели не передаётся: каждый запрос = системный промпт
  + текущее сообщение; `Chats/` не используется как память модели.

---

## 🟡 Архитектурные ограничения

### A1. JSON-хранилища без защиты

Все JSON-файлы: относительные пути (зависят от рабочей директории), нет
file lock, запись напрямую в основной файл, параллельные обработчики могут
потерять изменения, повреждённый JSON молча превращается в `{}`, нет схем,
миграций, резервных копий и версионирования формата.

### A2. Несогласованность компонентов

- Mini App работает со своей **устаревшей копией** `users_data.json`
  (4 записи против 11 в `data/`) и может затирать изменения;
- Python- и Qt-версии Connect возвращают **разные структуры JSON**;
- APAS Connect должен быть доступен на localhost процесса бота, а не
  пользователя;
- три реализации работы с `users_data`: `shared.py`, `arc_maps.py`,
  `Mini App/app.py`.

### A3. Дублирование кода

- `load/save_reports` — 3 копии (report.py, myreports.py, reports.py);
- `load/save_points_transactions` — 2 копии (addpoints.py, points.py);
- логика тумблеров уведомлений — 2 полные копии (notifications.py,
  settings.py);
- рендер профиля — 4 копии внутри profile.py;
- обёртки `TempUpdate` — 2 копии (guest.py, start.py);
- `Modes/Alice/Commands/{commands,modes,exit}.py` — мёртвые дубликаты
  функций из alice.py; `Modes/Alice/yamusic.py` — мёртвый дубликат
  актуального `Commands/yamusic.py`;
- admin-проверка дублируется локально в acc_stat.py.

### A4. Неиспользуемый код

- `Commands/generator.py` (625 строк) — нигде не вызывается;
- декоратор `guest_mode_check` в guest.py — не применяется;
- `handle_guest_command` — мёртвый код;
- `Commands/image.py` — команда не зарегистрирована (см. F3);
- `main_old.py` (см. F11).

### A5. Актуальность зависимостей

- `python-telegram-bot 22.5` — отстаёт от актуальной версии (22.8+) и Bot API
  на несколько релизов (нет `sendMessageDraft`, Rich Messages и др.);
- `google-generativeai 0.8.5` — EOL 30.11.2025, миграция на `google-genai`;
- Vertex AI SDK — генеративные модули удалены после 24.06.2026;
- `groq 0.33.0` → актуальная 1.x;
- часть моделей Groq/Gemini отключена или запланирована к отключению;
- README заявляет Python 3.7+, фактически требуются 3.10+;
- `requirements.txt` содержит битую строку `google-cloud-aiplatform-`
  без версии (CRLF, без перевода строки в конце файла);
- отсутствуют lock-файлы и CI.

### A6. Отсутствующая инфраструктура

- нет тестов, CI, мониторинга, глобального error handler;
- нет `setMyCommands` (командное меню не синхронизировано);
- только `run_polling()`, без webhook и фильтра `allowed_updates`;
- нет блокировки версий зависимостей.

---

## 🧾 Источники

- [Аудит №1: DeepSeek V4 Flash (Max) в OpenCode Desktop](AUDIT-01-deepseek.md)
- [Аудит №2: ChatGPT Codex (GPT-5.6 Sol High) + Codex Security](AUDIT-02-codex.md)
- [README проекта](https://github.com/pavelrakcheev/APAS-Telegram-Bot/blob/main/README.md)
