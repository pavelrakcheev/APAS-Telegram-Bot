"""Структурный smoke-тест APAS.

Не требует сети и реальных ключей. Проверяет:
1. синтаксис всех Python-файлов (всегда);
2. загрузку конфигурации с тестовыми ключами (если установлены зависимости);
3. импорт ключевых модулей (если установлены зависимости).
"""

import importlib
import os
import pathlib
import py_compile
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

# Тестовые ключи (не реальные, только чтобы пройти валидацию src/config.py)
os.environ["TELEGRAM_BOT_TOKEN"] = "123456789:TEST_DUMMY_TOKEN"
os.environ["GROQ_API_KEY"] = "gsk_TEST_DUMMY_KEY"

EXCLUDED_DIRS = {".venv", ".git", "__pycache__", "build", "dist", "node_modules"}

KEY_MODULES = [
    "shared",
    "Commands.start",
    "Commands.profile",
    "Commands.points",
    "Commands.games",
    "Commands.blum",
    "Commands.iss",
    "Commands.about",
    "Commands.acc_stat",
]


def test_compile_all() -> int:
    """Компилирует все .py вне исключённых каталогов."""
    failed = []
    count = 0
    for py in sorted(ROOT.rglob("*.py")):
        if any(part in EXCLUDED_DIRS for part in py.parts):
            continue
        if py.name == "smoke_test.py":
            continue
        count += 1
        try:
            py_compile.compile(str(py), doraise=True)
        except Exception as exc:  # noqa: BLE001
            failed.append(f"  {py.relative_to(ROOT)}: {exc}")
    if failed:
        print("FAIL compile:")
        print("\n".join(failed))
        sys.exit(1)
    print(f"OK: {count} файлов компилируются")
    return count


def test_imports() -> None:
    """Импортирует ключевые модули (только если установлены зависимости)."""
    try:
        import groq  # noqa: F401
        import telegram  # noqa: F401
    except ImportError:
        print("SKIP imports: зависимости не установлены (сделайте `make setup`)")
        return

    from src.config import REQUIRED_KEYS

    assert REQUIRED_KEYS == ["TELEGRAM_BOT_TOKEN", "GROQ_API_KEY"], REQUIRED_KEYS

    failed = []
    for module in KEY_MODULES:
        try:
            importlib.import_module(module)
        except Exception as exc:  # noqa: BLE001
            failed.append(f"  {module}: {exc}")
    if failed:
        print("FAIL imports:")
        print("\n".join(failed))
        sys.exit(1)
    print(f"OK imports: {', '.join(KEY_MODULES)}")


if __name__ == "__main__":
    test_compile_all()
    test_imports()
    print("Smoke test passed.")
