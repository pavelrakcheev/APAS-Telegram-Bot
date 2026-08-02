# APAS — Adaptive Analytic Predictive System

---

## Statistics

<div class="apas-stats">
  <div class="apas-stat">
    <div class="number">22</div>
    <div class="label">Commands</div>
  </div>
  <div class="apas-stat">
    <div class="number">18+</div>
    <div class="label">AI Models</div>
  </div>
  <div class="apas-stat">
    <div class="number">5</div>
    <div class="label">Subsystems</div>
  </div>
  <div class="apas-stat">
    <div class="number">9 089</div>
    <div class="label">Lines of Code</div>
  </div>
</div>

---

## Ecosystem

<div class="apas-ecosystem">
  <div class="apas-eco-card">
    <div class="header">
      <h3>ISS</h3>
      <span class="apas-status apas-status--stable">Working</span>
    </div>
    <div class="body">
      Unified user account system. Profiles, registration, user search,
      friend requests, public profiles with deep-link sharing.
    </div>
    <div class="footer">
      <span class="tag">Profiles</span>
      <span class="tag">Search</span>
      <span class="tag">Deep-links</span>
    </div>
  </div>

  <div class="apas-eco-card">
    <div class="header">
      <h3>ISS Play</h3>
      <span class="apas-status apas-status--stable">Working</span>
    </div>
    <div class="body">
      Gaming profile subsystem. 3-step registration, AI-powered nickname
      generation via Groq, linked to ISS account.
    </div>
    <div class="footer">
      <span class="tag">Nicknames</span>
      <span class="tag">Groq AI</span>
      <span class="tag">Linked</span>
    </div>
  </div>

  <div class="apas-eco-card">
    <div class="header">
      <h3>ISS Points</h3>
      <span class="apas-status apas-status--stable">Working</span>
    </div>
    <div class="body">
      Internal currency system. Admin-driven point allocation,
      transaction history with pagination, balance tracking.
    </div>
    <div class="footer">
      <span class="tag">Currency</span>
      <span class="tag">History</span>
      <span class="tag">Admin</span>
    </div>
  </div>

  <div class="apas-eco-card">
    <div class="header">
      <h3>ISS.ME</h3>
      <span class="apas-status apas-status--danger">Security Issues</span>
    </div>
    <div class="body">
      Web profile via Telegram Mini App. Flask backend, dark-themed UI,
      points display, settings. Deployed on Render.
    </div>
    <div class="footer">
      <span class="tag">Flask</span>
      <span class="tag">Mini App</span>
      <span class="tag">Render</span>
    </div>
  </div>

  <div class="apas-eco-card">
    <div class="header">
      <h3>Blum</h3>
      <span class="apas-status apas-status--stable">Working</span>
    </div>
    <div class="body">
      Psychological support character. Time-of-day greetings, photo,
      dialog mode (stub). Named after the developer's cat.
    </div>
    <div class="footer">
      <span class="tag">Psychologist</span>
      <span class="tag">Greeting</span>
      <span class="tag">Photo</span>
    </div>
  </div>

  <div class="apas-eco-card">
    <div class="header">
      <h3>Alice AI Mode</h3>
      <span class="apas-status apas-status--beta">Beta</span>
    </div>
    <div class="body">
      YandexGPT-powered assistant with two tiers (Lite/Pro),
      Yandex Music integration, conversation history, mode switching.
    </div>
    <div class="footer">
      <span class="tag">YandexGPT</span>
      <span class="tag">Music</span>
      <span class="tag">2 Models</span>
    </div>
  </div>

  <div class="apas-eco-card">
    <div class="header">
      <h3>One Core API</h3>
      <span class="apas-status apas-status--alpha">Alpha</span>
    </div>
    <div class="body">
      Multi-platform core. Telegram + VK integration (alpha).
      Core commands work cross-platform via python-vk-api.
    </div>
    <div class="footer">
      <span class="tag">Telegram</span>
      <span class="tag">VK</span>
      <span class="tag">Cross-platform</span>
    </div>
  </div>
</div>

---

## Capabilities

<div class="apas-features">
  <div class="apas-feature">
    <span class="icon">:material-robot:</span>
    <h3>Multi-Model AI</h3>
    <p>
      18+ models across three providers: Groq (GPT OSS, Qwen, Llama),
      Google Gemini (2.0/2.5), and YandexGPT (4/5/5.1).
    </p>
  </div>
  <div class="apas-feature">
    <span class="icon">:material-lightning-bolt:</span>
    <h3>Streaming Responses</h3>
    <p>
      Real-time answer generation via Groq streaming.
      Message is edited fragment by fragment as the AI generates.
    </p>
  </div>
  <div class="apas-feature">
    <span class="icon">:material-map-marker:</span>
    <h3>Geoservices</h3>
    <p>
      Arc Maps — nearby place search via OpenStreetMap Nominatim,
      category filters, AI location analysis, taxi links.
    </p>
  </div>
  <div class="apas-feature">
    <span class="icon">:material-music:</span>
    <h3>Yandex Music</h3>
    <p>
      Search tracks, charts, playlists, "My Wave" rotor station,
      likes — all via the yandex-music library.
    </p>
  </div>
  <div class="apas-feature">
    <span class="icon">:material-microphone:</span>
    <h3>Voice Input</h3>
    <p>
      Speech recognition for hands-free interaction.
      Send voice messages and get AI-generated responses.
    </p>
  </div>
  <div class="apas-feature">
    <span class="icon">:material-monitor:</span>
    <h3>Desktop Bridge</h3>
    <p>
      APAS Connect — system monitoring (CPU, RAM, disk, battery)
      exposed via HTTP for remote queries from the bot.
    </p>
  </div>
</div>

---

## Documentation

<div class="grid cards" markdown>

-   :material-cog:{ .lg .middle } **Installation & Setup**

    ---

    Step-by-step guide for all components: bot, Mini App,
    APAS Connect, Docker, Makefile.

    [:octicons-arrow-right-24: Setup](SETUP.md)

-   :material-domain:{ .lg .middle } **Architecture**

    ---

    System diagrams, data flows, storage schema,
    component interaction, target architecture.

    [:octicons-arrow-right-24: Architecture](ARCHITECTURE.md)

-   :material-bug:{ .lg .middle } **Known Issues**

    ---

    S1–S8, F1–F12, A1–A6 — all bugs, vulnerabilities,
    and limitations documented for v0.1.

    [:octicons-arrow-right-24: Known Issues](KNOWN-ISSUES.md)

-   :material-shield-search:{ .lg .middle } **Security Audits**

    ---

    Two independent audits: DeepSeek V4 Flash and
    Codex Security (GPT-5.6 Sol High).

    [:octicons-arrow-right-24: Audit #1](AUDIT-01-deepseek.md) · [:octicons-arrow-right-24: Audit #2](AUDIT-02-codex.md)

-   :material-camera:{ .lg .middle } **Gallery**

    ---

    Screenshots and videos of the APAS ecosystem
    in action: AI streaming, maps, Alice mode, VK.

    [:octicons-arrow-right-24: Gallery](gallery.md)

-   :material-shield-lock:{ .lg .middle } **Security Policy**

    ---

    How to report vulnerabilities, secret rotation
    checklist, known exposure timeline.

    [:octicons-arrow-right-24: SECURITY](https://github.com/pavelrakcheev/APAS-Telegram-Bot/blob/main/SECURITY.md)

-   :material-account-group:{ .lg .middle } **Contributing**

    ---

    Contribution guidelines, issue/PR templates,
    conventional commits, branch strategy.

    [:octicons-arrow-right-24: CONTRIBUTING](https://github.com/pavelrakcheev/APAS-Telegram-Bot/blob/main/CONTRIBUTING.md)

-   :material-tools:{ .lg .middle } **Development**

    ---

    Dev Container setup, testing, linting, CI/CD,
    adding new AI models, project conventions.

    [:octicons-arrow-right-24: Development](DEVELOPMENT.md)

</div>

---

## Live Bot

<div style="text-align: center; margin: 2rem 0;">
  <a href="https://t.me/Intelligence_playground_bot" target="_blank" style="display: inline-flex; align-items: center; gap: 0.5rem; padding: 0.75rem 1.5rem; background: #0088cc; color: #fff; border-radius: 8px; text-decoration: none; font-weight: 600;">
    :fontawesome-brands-telegram: Try @Intelligence_playground_bot
  </a>
</div>

Try: `/start` &middot; `/alice` &middot; `/blum` &middot; `/games` &middot; `/models`

Mini App: [iss-app-for-telegram-bot.onrender.com](https://iss-app-for-telegram-bot.onrender.com)

---

## Technology Stack

<div class="apas-tech-stack">
  <span class="apas-tech">:simple-python: Python 3.10+</span>
  <span class="apas-tech">:simple-telegram: Telegram Bot API</span>
  <span class="apas-tech">:simple-flask: Flask 3.1</span>
  <span class="apas-tech">:simple-groq: Groq SDK</span>
  <span class="apas-tech">:simple-google: Gemini</span>
  <span class="apas-tech">:material-alpha-y-circle: YandexGPT</span>
  <span class="apas-tech">:simple-docker: Docker</span>
  <span class="apas-tech">:material-language-python: pytest</span>
  <span class="apas-tech">:simple-githubactions: GitHub Actions</span>
</div>
