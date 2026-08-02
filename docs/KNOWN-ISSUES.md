# Known Issues & Limitations — v0.1.0-canary

This document catalogs all bugs, vulnerabilities, and limitations of the
first public release, identified during two independent audits:

- [Audit #1 — DeepSeek V4 Flash (Max) in OpenCode Desktop](AUDIT-01-deepseek.md)
- [Audit #2 — ChatGPT Codex (GPT-5.6 Sol High) + Codex Security](AUDIT-02-codex.md)

!!! info "Status"
    None of the issues listed below have been fixed in this version —
    the project is published "as is" for educational purposes.

---

## :material-shield-lock: Critical Security Issues

### S1. Secrets Considered Compromised

The development history contained real values:

- `.env`: `TELEGRAM_BOT_TOKEN`, `GROQ_API_KEY`, `GEMINI_API_KEY`,
  `YANDEX_API_KEY`, `YANDEX_MUSIC_ADMIN_TOKEN`, `TELEGRAM_ID`,
  `ADMIN_PASSWORD`, Google Cloud identifiers;
- `APAS Connect/config.json`: separate Telegram token (not used by code);
- `APAS Connect Qt/build/Release/APASConnectTestCert.pfx/.cer`:
  self-signed test certificate with private key (password in
  `APASConnectConfig.yml`).

All these files are **excluded** from v0.1 (`.gitignore`, template
`.env.example` / `config.example.json`), but:

!!! danger "Action Required"
    Revoke the bot token via @BotFather, reissue all API keys,
    change admin password, delete PFX from distributed materials.
    Check cloud upload history, archives, and backups.

### S2. Mini App Does Not Authenticate Users (Confirmed on Live Service)

- `Mini App/app.py`: `CORS(app)` open to all origins;
- Backend does not verify `Telegram.WebApp.initData` signature and trusts
  numeric `user_id` from client;
- `/api/debug` returns user_id list, file paths, and server directory
  contents — **accessible without authorization**;
- `POST /api/user-settings` — mass assignment: any fields (e.g.,
  `setup_completed`) can be written to any user;
- JSON writes without locks or atomic rename.

!!! danger "Verified"
    Live service check (Render) confirmed:
    `/api/debug` → 200 without auth; `Origin: https://attacker.example` →
    `Access-Control-Allow-Origin: https://attacker.example`.

### S3. IDOR in myreports.py

`handle_myreports_detail_callback` loads reports by `user_id` from
callback data without checking `query.from_user.id`. In v0.1 the
vulnerability is **hidden by a routing bug** (F1): callback
`myreports_detail_*` goes to the general handler and is silently ignored.

!!! warning "Post-Fix Risk"
    After fixing routing, IDOR becomes exploitable unless owner
    verification is added simultaneously.

### S4. `/remote` Accessible to All Users

`Commands/remote.py` does not check permissions: any user can request
system information of the bot's host machine (localhost:5000).
Additionally: Python Connect schemas (`ram_total_gb` etc.) don't match
what the bot expects (`ram_total`), so some fields show "Unknown".

### S5. Conditional RCE in Commands/generator.py

`generator.py` (not used by any handler but present in the repo)
contains a chain: path traversal via `app_name`, server-side `eval()`
in Python, client-side `eval()` in JS, stored XSS via `innerHTML`,
`app.run(debug=True, host='0.0.0.0')`.

!!! info "Not Exploitable in v0.1"
    Must be deleted or rewritten before enabling.

### S6. Data and Conversations Stored in Plaintext

- `Chats/<user_id>/chat.txt` — all dialogs in open form, no retention
  policy or expiration;
- Guest mode and `/blum` create false expectation of non-storage —
  guest messages and "psychologist" dialogs write to the same files;
- PII (name, age, city) is sent to external AI providers without
  separate consent.

### S7. "Profile Deletion" Does Not Delete Data

`Commands/profile.py` (`confirm_delete`) clears only `context.user_data`
and saves an empty object. Not deleted: user record, chats, reports,
points history, Alice state, ISS Play account, Mini App profile copy.
The user message about "complete and irreversible deletion" does not
match actual behavior.

### S8. Public Profile Enumeration

Deep-link `start=profile_<identifier>` (`Commands/start.py`) accepts both
username and numeric Telegram ID. A registered user can enumerate IDs to
obtain name, age, city, and registration date of other users. There is
no consent mechanism for profile publicity.

---

## :material-alert: Functional Issues

### F1. Report Callback Routing Broken

`main.py`:

- `data.startswith('report_')` (line 171) catches `report_detail_*`
  before it reaches `handle_report_detail_callback` (line 181) —
  detailed report viewing and admin status changes **are inaccessible**;
- `myreports_detail_*` goes to `handle_myreports_callback` where there
  is no matching branch (only `else: return`) — viewing your own report
  details is inaccessible.

### F2. `is_guest_mode()` Without Argument

In `Commands/reports.py` at lines 195, 539, and 616 the function is
called without the required `user_data` parameter → `TypeError` on
every admin reports panel callback.

### F3. `/image` Not Registered

`Commands/image.py` (`image_command`) is imported but `main.py` has no
`CommandHandler("image", ...)` — image generation is inaccessible from
the normal interface. Additionally: `image_edit` button not handled,
uses deprecated SDK (`google-generativeai`) and removed Vertex AI
generative modules.

### F4. Guest Callback Buttons

`Commands/guest.py`:

- `guest_back` calls `start_command` with callback `update` where
  `update.message is None`;
- `guest_commands` similarly calls a normal command handler.
  Expected `AttributeError` or reference to missing `message`.

### F5. Inaccessible UI Buttons

| Button | File | Status |
|---|---|---|
| `report_send_empty` ("Send report" without description) | report.py:189 | created, not handled |
| `blum_settings` ("Configure Blum") | blum.py | not handled |
| `image_edit` ("Edit") | image.py | not handled |
| `addpoints_confirm` | addpoints.py | dead branch (`pass`) |
| `blum_start_dialog` | blum.py | shows wrong text instead of dialog |

### F6. Alice AI Mode

- `alice_states.json` keys after reading are strings, some code looks
  for integer ID → state lost after restart;
- `/exit`, `/commands`, `/modes`, `/music`, `/yamusic` checked inside
  text handler but main handler excludes `filters.COMMAND`, and no
  separate `CommandHandler` registered;
- YandexGPT response sent with `parse_mode='Markdown'` without escaping
  — model may produce invalid markup;
- On API errors, fake "test" tracks are returned that look like real ones;
- "Music playback" returns track info but does not transmit audio;
- "Alice" is not the official Yandex Alice — it's YandexGPT with a
  system prompt.

### F7. Mini App Frontend

- `index.html:129`: `getElementById('issCity')` — element doesn't exist
  → JS error, city from profile not displayed;
- Backend sends date in `dd.mm.YYYY` format, frontend passes to
  `new Date()` → `Invalid Date`;
- Points balance hardcoded (`60`) in `index.html` and `points.html`;
- Weather completely fake (Moscow coordinates hardcoded);
- `tg.shareUrl` doesn't exist in official Telegram Mini Apps API
  (there are `shareMessage`, `shareToStory`, `openTelegramLink`).

### F8. Default Points Mismatch

`points` default: `60` in `profile.py` and Mini App, `0` in `points.py` /
`addpoints.py` — balance "jumps" depending on the screen.

### F9. Encoding & Debug

- 6 corrupted encoding characters (`�`) in `Commands/commands.py`,
  `Commands/reports.py` etc.;
- At least 32 `print` operators in production code, including
  `print("DEBUG: ...")` in `Commands/start.py`.

### F10. APAS Connect Qt

- API check on port **8080**, server listens on **5000** (MainWindow.cpp);
- Launches missing `check_models.py` / `check_vertexai.py`;
- `waitForFinished(10000)` ×4 in UI thread → window freezes up to ~40s;
- HTTP router uses `contains("GET /system_info")` — matches
  `/system_infoevil` too; no `Content-Length` or proper parser;
- CPU name hardcoded as `x64 Processor`;
- No `/ping` (unlike Python version).

### F11. APAS Connect Python

- `requirements.txt` contains `tkinter` (part of standard library,
  not installed via pip) — `pip install -r requirements.txt` will fail;
- `winreg` — strictly Windows-oriented;
- Token in `config.json` not used by code;
- `main_old.py` — stale copy with broken code (NameError on closing
  startup window);
- Test `test_api.py` launches GUI application — not isolated.

### F12. Performance & Reliability

- Gemini and Yandex called synchronously inside `async def` — block
  event loop; `requests.post` to Yandex without timeout;
- Maps: synchronous HTTP requests and sequential `sleep(1.1)` inside
  async handler;
- Groq: `edit_text` on every fragment — flood limit risk and 4096
  character limit exceeded;
- No request limits, prompt length restriction, quota/cost control,
  content moderation;
- No `Application.add_error_handler`;
- Model dialog context not passed: each request = system prompt +
  current message; `Chats/` not used as model memory.

---

## :material-information: Architectural Limitations

### A1. JSON Stores Without Protection

All JSON files: relative paths (depend on working directory), no file
locking, write directly to main file, concurrent handlers may lose
changes, corrupted JSON silently becomes `{}`, no schema, migrations,
backup, or format versioning.

### A2. Component Inconsistency

- Mini App works with its own **stale copy** of `users_data.json`
  (4 records vs 11 in `data/`) and can overwrite changes;
- Python and Qt versions of Connect return **different JSON structures**;
- APAS Connect should be accessible on the bot process localhost, not
  the user's;
- Three implementations of `users_data` access: `shared.py`, `arc_maps.py`,
  `Mini App/app.py`.

### A3. Code Duplication

- `load/save_reports` — 3 copies (report.py, myreports.py, reports.py);
- `load/save_points_transactions` — 2 copies (addpoints.py, points.py);
- Notification toggle logic — 2 full copies (notifications.py, settings.py);
- Profile render — 4 copies inside profile.py;
- `TempUpdate` wrappers — 2 copies (guest.py, start.py);
- `Modes/Alice/Commands/{commands,modes,exit}.py` — dead duplicates of
  functions from alice.py; `Modes/Alice/yamusic.py` — dead duplicate of
  current `Commands/yamusic.py`;
- Admin check duplicated locally in acc_stat.py.

### A4. Unused Code

- `Commands/generator.py` (625 lines) — never called;
- `guest_mode_check` decorator in guest.py — never applied;
- `handle_guest_command` — dead code;
- `Commands/image.py` — command not registered (F3);
- `main_old.py` (see F11).

### A5. Dependency Currency

- `python-telegram-bot 22.5` — lags behind current (22.8+) and Bot API
  by several releases (no `sendMessageDraft`, Rich Messages, etc.);
- `google-generativeai 0.8.5` — EOL 30.11.2025, migrate to `google-genai`;
- Vertex AI SDK — generative modules removed after 24.06.2026;
- `groq 0.33.0` → current is 1.x;
- Some Groq/Gemini models disabled or scheduled for disabling;
- README claims Python 3.7+, actually requires 3.10+;
- `requirements.txt` contains broken line `google-cloud-aiplatform-`
  without version (CRLF, no trailing newline);
- No lock files or CI.

### A6. Missing Infrastructure

- No tests, CI, monitoring, global error handler;
- No `setMyCommands` (command menu not synchronized);
- Only `run_polling()`, no webhook or `allowed_updates` filter;
- No dependency version pinning.

---

## Sources

- [Audit #1: DeepSeek V4 Flash (Max) in OpenCode Desktop](AUDIT-01-deepseek.md)
- [Audit #2: ChatGPT Codex (GPT-5.6 Sol High) + Codex Security](AUDIT-02-codex.md)
- [Project README](https://github.com/pavelrakcheev/APAS-Telegram-Bot/blob/main/README.md)
