# Installation & Setup

!!! warning "v0.1.0-canary"
    This is an experimental version. Before running, read
    [KNOWN-ISSUES](KNOWN-ISSUES.md) and both security audits
    ([AUDIT-01](AUDIT-01-deepseek.md), [AUDIT-02](AUDIT-02-codex.md)).
    The version contains documented vulnerabilities and is **not**
    intended for production.

---

## Prerequisites

| Requirement | Details |
|---|---|
| **Version** | `0.1.0-canary` — extremely unstable, for learning only |
| **Required keys** | `TELEGRAM_BOT_TOKEN` + `GROQ_API_KEY` (validated in `src/config.py`) |
| **Optional keys** | Enable corresponding models/features only |
| **Data** | JSON files in `data/` are created automatically on first run |
| **Secrets** | Tokens from old history are **compromised** — get new ones (see Security) |
| **Ports** | Bot: long-polling (free port). APAS Connect: **5000** (`127.0.0.1`). Mini App: 5000 (dev) |
| **OS** | Bot: any; APAS Connect Python: **Windows** (`winreg`, `tkinter`); Qt: Windows x64 |

### API Keys Needed

| Resource | Where to get | Purpose |
|---|---|---|
| Telegram Bot Token | [@BotFather](https://t.me/BotFather) | Required |
| `GROQ_API_KEY` | [console.groq.com](https://console.groq.com/) | Required (primary AI) |
| `GEMINI_API_KEY` | [aistudio.google.com](https://aistudio.google.com/) | Gemini models |
| Google Cloud project | [console.cloud.google.com](https://console.cloud.google.com/) | Imagen (`/image`) |
| `YANDEX_API_KEY` | [console.yandex.cloud](https://console.yandex.cloud/) | YandexGPT |
| Yandex Music token | OAuth in Yandex profile | Alice AI Mode |
| Python | [python.org](https://www.python.org/downloads/) | 3.10+ (recommended 3.12/3.13) |

---

## 1. Telegram Bot (10 minutes)

### Step 1 — Clone

```bash
git clone https://github.com/pavelrakcheev/APAS-Telegram-Bot.git
cd APAS-Telegram-Bot
```

### Step 2 — Virtual Environment

=== "macOS / Linux"

    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

=== "Windows (cmd)"

    ```cmd
    python3 -m venv .venv
    .venv\Scripts\activate
    ```

=== "Windows (PowerShell)"

    ```powershell
    python3 -m venv .venv
    .venv\Scripts\Activate.ps1
    ```

### Step 3 — Dependencies

```bash
pip install -r requirements.txt
```

!!! danger "Known Issue v0.1"
    `requirements.txt` contains a broken line `google-cloud-aiplatform-`
    (without version). If `pip install` fails, remove that line and
    install manually:
    ```bash
    pip install "google-cloud-aiplatform>=1.90"
    ```

### Step 4 — Configuration

```bash
cp .env.example .env
```

Fill in `.env` (minimum — two lines):

```bash
TELEGRAM_BOT_TOKEN=1234567890:AAA...   # from @BotFather
GROQ_API_KEY=gsk_...                    # from console.groq.com

# Optional:
# TELEGRAM_ID=your_id_for_admin
# ADMIN_PASSWORD=admin_password
# GEMINI_API_KEY=...
# YANDEX_API_KEY=...
# GOOGLE_CLOUD_PROJECT=...
# YANDEX_MUSIC_ADMIN_TOKEN=...
```

### Step 5 — Run

```bash
python main.py
```

The bot runs in long-polling mode — no external address or port needed.
Expect something like `Application started` in the console.

### Alternative: Docker

```bash
cp .env.example .env        # fill in TELEGRAM_BOT_TOKEN and GROQ_API_KEY
docker compose up -d --build
```

- `bot` — runs with mounted volumes `./data` and `./Chats`;
- `mini-app` — available at `http://localhost:5000`, reads from `./data`.

Stop: `docker compose down`.

### Alternative: Makefile

```bash
make setup      # venv + deps (filters broken requirements line)
make run        # python main.py
make test       # smoke test
make check      # syntax check
make docker-up  # same as docker compose up -d --build
```

### Step 6 — Verify

| What | How to check | Expected result |
|---|---|---|
| Bot alive | `/start` → registration | Greeting, entry in `data/users_data.json` |
| AI works | Any message | Response from Groq model |
| Model selection | `/models` | List of 18+ models |
| Profile | `/profile` | ISS account data |
| Points | `/points` | Balance, history |
| ISS Play | `/games` | Gaming profile registration |
| Blum | `/blum` | Psychologist greeting with photo |
| Alice | `/alice` | YandexGPT + Music mode |
| Maps | `/maps` (geolocation) | Nearby places via Nominatim |
| Mini App | WebApp button in profile | ISS.ME page over HTTPS |
| APAS Connect | `curl /ping`, `/remote` in bot | `{"status": "ok"}`, system metrics |

---

## 2. Mini App (ISS.ME)

Web user profile: Flask + HTML/JS, opened via button in the bot.

### Local Run

```bash
cd "Mini App"

# 1. Environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Dependencies
pip install -r requirements.txt

# 3. User data (copy from bot!)
cp ../data/users_data.json users_data.json

# 4. Dev server
python app.py        # → http://localhost:5000
```

### Deploy to Render (Recommended)

1. Account on [render.com](https://render.com).
2. **New Web Service** → point to the repo with `Mini App/` folder.
3. Settings:
    - **Environment:** Python 3
    - **Build Command:** `pip install -r requirements.txt`
    - **Start Command:** `gunicorn app:app`
4. After deploy, get URL like `https://your-app.onrender.com`.
5. Paste URL into the bot's WebApp button (see [Linking](#linking-mini-app-to-bot)).

!!! info "HTTPS Required"
    Telegram opens Web Apps **only over HTTPS**.

### Deploy to Heroku

The folder already contains `Procfile` and `runtime.txt` (python-3.11.6):

```bash
cd "Mini App"
heroku create iss-me
git init && git add . && git commit -m "ISS.ME"
git push heroku main
```

!!! warning "Data Sync"
    Mini App works with its **own copy** of `users_data.json`.
    In v0.1 it does not sync with the bot automatically — update manually.

---

## 3. APAS Connect (Python)

Desktop bridge: shows system information in the bot via `/remote`.

!!! warning "Windows Only"
    Uses `winreg` and `tkinter` — Windows only.

### Install & Run

```bash
cd "APAS Connect"

# 1. Environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Dependencies
# ⚠️ requirements.txt has a tkinter line that breaks pip —
#    remove it or install packages explicitly:
pip install flask psutil requests pystray Pillow

# 3. Configuration
cp config.example.json config.json

# 4. Run
python main.py
```

The program minimizes to the system tray. API check:

```bash
curl http://127.0.0.1:5000/ping
curl http://127.0.0.1:5000/system_info
```

### Build exe (Windows)

```bash
python build_exe.py        # → dist/APAS_Connect.exe (PyInstaller, onefile)
```

### Placement Requirement

Bot and APAS Connect must run **on the same machine** (or network) —
the bot hits `http://localhost:5000` on `/remote` (`Commands/remote.py`).

---

## 4. APAS Connect (Qt/C++)

Remake of the bridge on Qt 6.9.3 / C++17 / MSVC 2022 (Windows x64).

### Build

```bash
cd "APAS Connect Qt"
cmake -S . -B build
cmake --build build --config Release
# → build/Release/APASConnectQt.exe
```

### Run

Launch `APASConnectQt.exe` — window with CPU/RAM/disk progress bars,
"Get System Info", "Check API & Models", "Start Auto Update" buttons
and a tray icon.

!!! danger "Known Bugs (F10)"
    API check hits port 8080 instead of 5000; launches missing
    `check_models.py` / `check_vertexai.py`; UI may freeze up to 40s.
    See [KNOWN-ISSUES: F10](KNOWN-ISSUES.md#f10-apas-connect-qt).

---

## Linking Mini App to Bot

The Mini App URL is set in the WebApp button in `Commands/profile.py`:

```python
from telegram import InlineKeyboardButton, WebAppInfo

keyboard = [[
    InlineKeyboardButton(
        "My Profile",
        web_app=WebAppInfo(url="https://your-app.onrender.com")
    )
]]
```

After changes — restart the bot.

---

## Troubleshooting

### `Missing required environment variables: ...`

`.env` not found or empty. Check:

- File is named exactly `.env` and in the repository root;
- Contains `TELEGRAM_BOT_TOKEN` and `GROQ_API_KEY`;
- Bot is launched from root (`python main.py`, not `python Commands/main.py`).

### Error on `pip install -r requirements.txt`

Known issue v0.1 — broken line `google-cloud-aiplatform-`.
Remove it from the file and run:

```bash
pip install "google-cloud-aiplatform>=1.90"
pip install -r requirements.txt
```

### Bot starts but doesn't respond

1. Check the token in BotFather — it should not start with `your_`.
2. Default model disabled by provider? Select another: `/models`.
3. Groq key is active: [console.groq.com](https://console.groq.com/) → API Keys.

### Mini App shows "no data"

`users_data.json` not copied to Mini App folder, or data is stale:

```bash
cp ../data/users_data.json users_data.json   # from Mini App folder
```

### `/remote` doesn't work

1. APAS Connect is running? `curl http://127.0.0.1:5000/ping`.
2. Bot and APAS Connect on the same machine? (localhost ≠ remote server).
3. Port not occupied by another process? (always 5000 in v0.1).

### Groq models "not found" / "disabled"

Some models (Kimi K2, Qwen3 32B, Llama 4, Llama 3.1/3.3, GPT OSS 20B)
were deprecated by providers in 2025–2026. Select a current one via
`/models` (e.g., `openai/gpt-oss-120b`).

---

## Security Checklist

!!! danger "Mandatory"
    v0.1 contains confirmed vulnerabilities — do not run publicly
    without fixes.

1. **Rotate secrets.** Tokens from the old history are compromised:
    - [@BotFather](https://t.me/BotFather) → `/revoke` → new token;
    - Groq/Gemini/Yandex → delete and create new API keys;
    - Change `ADMIN_PASSWORD`;
    - Delete PFX certificates from distributed materials.

2. **Mini App (S2 — critical):**
    - Close `/api/debug` (currently responds without auth);
    - Add Telegram `initData` verification in `app.py`;
    - Remove `CORS(app)` / restrict domains;
    - Don't trust `user_id` from requests — extract from initData.

3. **`/remote` (S4):** restrict command to admins only.

4. **`/reports`:** fix `report_` / `report_detail_` routing
    (IDOR hidden by router bug).

5. **Secrets in git:** `.env`, `data/*.json`, `Chats/*` are in `.gitignore` —
    before push: `git status` should not show these files.

6. **Verify:** after fixes, run a re-audit
    (e.g., Codex Security / secret scan).

Details: [KNOWN-ISSUES.md](KNOWN-ISSUES.md),
[AUDIT-01](AUDIT-01-deepseek.md), [AUDIT-02](AUDIT-02-codex.md).
