from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ContextTypes
from ..alice import alice_states

async def exit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выход из режима Алисы"""
    user_id = update.effective_user.id

    if user_id in alice_states:
        del alice_states[user_id]

    # Убираем reply клавиатуру
    reply_markup = ReplyKeyboardRemove()

    await update.message.reply_text(
        "Вы вышли из режима Алисы. Все функции APAS снова доступны! 👋",
        reply_markup=reply_markup
    )