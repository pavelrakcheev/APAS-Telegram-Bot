# Development

Guide for developers who want to contribute to APAS.

---

## Quick Start

### Via Dev Container (Recommended)

1. Install [VS Code](https://code.visualstudio.com/) and [Dev Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
2. Open the project folder in VS Code
3. Click "Reopen in Container" when the notification appears
4. All dependencies install automatically

### Manual Setup

```bash
# Clone the repository
git clone https://github.com/pavelrakcheev/APAS-Telegram-Bot.git
cd APAS-Telegram-Bot

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your keys

# Install pre-commit hooks
pre-commit install
```

---

## Project Structure

```
Bot/
├── main.py              # Entry point, command router
├── shared.py            # Shared utilities
├── src/config.py        # Configuration loader
├── Commands/            # Command modules (22 modules)
├── Models/              # AI providers (groq, gemini, yandex)
├── Modes/Alice/         # Alice AI mode
├── Modules/             # Geoservices (maps, weather)
├── Mini App/            # Flask web application
├── APAS Connect/        # Python desktop bridge
├── APAS Connect Qt/     # Qt/C++ remake
├── tests/               # Tests
└── docs/                # Documentation
```

---

## Testing

### Run All Tests

```bash
pytest
```

### With Coverage

```bash
pytest --cov=Models --cov-report=html
# Open htmlcov/index.html in browser
```

### Smoke Test Only

```bash
python tests/smoke_test.py
```

---

## Linting & Formatting

### Ruff (Linter + Formatter)

```bash
# Check
ruff check .

# Auto-fix
ruff check --fix .

# Format
ruff format .
```

### Pre-commit

```bash
# Install
pre-commit install

# Run on all files
pre-commit run --all-files
```

---

## Adding a New AI Model

### 1. Create Module in `Models/`

```python
# Models/new_provider.py
from src.config import NEW_PROVIDER_API_KEY

NEW_MODELS = {
    'new_model_key': {
        'name': 'New Model Name',
        'description': 'Model description',
        'provider': 'new_provider',
        'model_id': 'model-id-123',
        'category': 'new_category'
    }
}

async def generate_new_response(model_config, system_prompt, user_message):
    """Generate response via new provider."""
    try:
        # API call implementation
        return "Response text"
    except Exception as e:
        raise Exception(f"Error with {model_config['name']}: {str(e)}")
```

### 2. Register in `Commands/models.py`

```python
from Models.new_provider import NEW_MODELS, generate_new_response

# Add to MODELS dict:
MODELS.update(NEW_MODELS)
```

### 3. Add Tests

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
        # Test with mock
        pass
```

---

## CI/CD

### What's Checked in CI

| Check | Description |
|---|---|
| Secret scan | gitleaks searches for secrets |
| Forbidden files | No .env, keys, PII |
| Lint (ruff) | Code style, errors |
| Python syntax | Compile all .py files |
| Tests | Unit tests with coverage |
| pip-audit | Dependency vulnerabilities |
| Markdown links | Link validation |

### Automatic Deployment

On tag `v*`, the `release.yml` workflow:
1. Builds Windows exe (APAS Connect)
2. Creates GitHub Release with assets

---

## Conventions

### Code

- Python 3.10+
- 4 spaces (no tabs)
- Type hints welcome
- Ruff for linting and formatting

### Commits

[Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add new /xyz command
fix: fix bug in Reports
docs: update README
test: add tests for Models
```

### Branches

- `main` — protected, no force push
- Feature branches: `feature/description`
- Bug fixes: `fix/description`

---

## Useful Commands

```bash
# Tests
pytest                          # All tests
pytest tests/test_models/       # Only model tests
pytest -x                       # Stop on first failure

# Linting
ruff check .                    # Check
ruff format .                   # Format

# Build
python -m compileall .          # Compile all .py
make docker-up                  # Docker build

# Run
python main.py                  # Launch bot
make run                        # Via Makefile
```

---

## Issues & Questions

1. Check [KNOWN-ISSUES.md](KNOWN-ISSUES.md)
2. Search [Issues](https://github.com/pavelrakcheev/APAS-Telegram-Bot/issues)
3. Create a new Issue with labels `bug` or `enhancement`
