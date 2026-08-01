from telegram import Update
from telegram.ext import ContextTypes

async def commands_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать доступные команды в режиме Алисы"""
    commands_text = """📋 **Команды режима Алисы:**

• `/commands` — показать этот список команд
• `/modes` — информация о доступных режимах Алисы
• `/exit` — выйти из режима Алисы

Также доступны кнопки на клавиатуре:
• "Выйти из режима" — выход из режима Алисы
• "Переключить на Алису Про/Lite" — смена модели AI"""

    await update.message.reply_text(commands_text, parse_mode='Markdown')