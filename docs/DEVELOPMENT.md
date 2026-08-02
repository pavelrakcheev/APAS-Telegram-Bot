# 🛠 Разработка APAS

Руководство для разработчиков, желающих внести вклад в проект.

---

## Быстрый старт

### Через Dev Container (рекомендуется)

1. Установите [VS Code](https://code.visualstudio.com/) и [Dev Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
2. Откройте папку проекта в VS Code
3. Нажмите "Reopen in Container" при появлении уведомления
4. Все зависимости установятся автоматически

### Ручная установка

```bash
# Клонируйте репозиторий
git clone https://github.com/pavelrakcheev/APAS-Telegram-Bot.git
cd APAS-Telegram-Bot

# Создайте виртуальное окружение
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate  # Windows

# Установите зависимости
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Настройте переменные окружения
cp .env.example .env
# Отредактируйте .env с вашими ключами

# Установите pre-commit hooks
pre-commit install
```

---

## Структура проекта

```
Bot/
├── main.py              # Точка входа, роутер команд
├── shared.py            # Общие утилиты
├── src/config.py        # Загрузка конфигурации
├── Commands/            # Модули команд (22 модуля)
├── Models/              # ИИ-провайдеры (groq, gemini, yandex)
├── Modes/Alice/         # Режим Alice AI
├── Modules/             # Геосервисы (maps, weather)
├── Mini App/            # Flask веб-приложение
├── APAS Connect/        # Python десктопный мост
├── APAS Connect Qt/     # Qt/C++ ремейк
├── tests/               # Тесты
└── docs/                # Документация
```

---

## Тестирование

### Запуск всех тестов

```bash
pytest
```

### С покрытием кода

```bash
pytest --cov=Models --cov-report=html
# Откройте htmlcov/index.html в браузере
```

### Только smoke-тест

```bash
python tests/smoke_test.py
```

---

## Линтинг и форматирование

### Ruff (линтер + форматер)

```bash
# Проверка
ruff check .

# Автоисправление
ruff check --fix .

# Форматирование
ruff format .
```

### Pre-commit

```bash
# Установка
pre-commit install

# Запуск на всех файлах
pre-commit run --all-files
```

---

## Добавление новой ИИ-модели

### 1. Создайте модуль в `Models/`

```python
# Models/new_provider.py
from src.config import NEW_PROVIDER_API_KEY

NEW_MODELS = {
    'new_model_key': {
        'name': 'New Model Name',
        'description': 'Описание модели',
        'provider': 'new_provider',
        'model_id': 'model-id-123',
        'category': 'new_category'
    }
}

async def generate_new_response(model_config, system_prompt, user_message):
    """Генерация ответа через новый провайдер."""
    try:
        # Реализация API вызова
        return "Response text"
    except Exception as e:
        raise Exception(f"Error with {model_config['name']}: {str(e)}")
```

### 2. Зарегистрируйте в `main.py`

```python
from Models.new_provider import NEW_MODELS, generate_new_response

# В словарь ALL_MODELS добавьте:
ALL_MODELS.update(NEW_MODELS)
```

### 3. Добавьте тесты

```python
# tests/test_models/test_new_provider.py
import pytest
from Models.new_provider import NEW_MODELS, generate_new_response

class TestNewProvider:
    def test_models_structure(self):
        assert isinstance(NEW_MODELS, dict)
        for key, config in NEW_MODELS.items():
            assert "name" in config
            assert "model_id" in config

    @pytest.mark.asyncio
    async def test_generate_response(self):
        # Тест с моком
        pass
```

---

## CI/CD

### Что проверяется в CI

| Проверка | Описание |
|----------|----------|
| Secret scan | gitleaks ищет секреты |
| Forbidden files | Нет .env, ключей, PII |
| Lint (ruff) | Стиль кода, ошибки |
| Python syntax | Компиляция всех .py |
| Tests | Unit-тесты с покрытием |
| pip-audit | Уязвимости зависимостей |
| Markdown links | Проверка ссылок |

### Автоматический деплой

При создании тега `v*` workflow `release.yml`:
1. Собирает Windows exe (APAS Connect)
2. Создаёт GitHub Release с ассетами

---

## Конвенции

### Код

- Python 3.10+
- 4 пробела (не табы)
- Type hints приветствуются
- Ruff для линтинга и форматирования

### Коммиты

[Conventional Commits](https://www.conventionalcommits.org/):

```
feat: добавить новую команду /xyz
fix: исправить баг в Reports
docs: обновить README
test: добавить тесты для Models
```

### Ветки

- `main` — защищённая, без force push
- Feature ветки: `feature/описание`
- Bug fix: `fix/описание`

---

## Полезные команды

```bash
# Тесты
pytest                          # Все тесты
pytest tests/test_models/       # Только тесты моделей
pytest -x                       # Остановка при первом падении

# Линтинг
ruff check .                    # Проверка
ruff format .                   # Форматирование

# Сборка
python -m compileall .          # Компиляция всех .py
make docker-up                  # Docker сборка

# Запуск
python main.py                  # Запуск бота
make run                        # Через Makefile
```

---

## Проблемы и вопросы

1. Проверьте [KNOWN-ISSUES.md](KNOWN-ISSUES.md)
2. Поищите в [Issues](https://github.com/pavelrakcheev/APAS-Telegram-Bot/issues)
3. Создайте новый Issue с标签ами `bug` или `enhancement`

---

<div align="right"><a href="#-разработка-apas">⬆️ Наверх</a></div>
