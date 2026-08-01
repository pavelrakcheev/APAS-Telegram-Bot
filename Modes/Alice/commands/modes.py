from telegram import Update
from telegram.ext import ContextTypes
from ..alice import alice_states

async def modes_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать информацию о режимах Алисы"""
    user_id = update.effective_user.id
    current_model = alice_states[user_id]['model'] if user_id in alice_states else 'lite'

    modes_text = f"""🎭 **Режимы Алисы:**

**Алиса Lite** (YandexGPT 5 Lite)
• Для повседневных запросов и общения
• Быстрые ответы
• Экономичный режим
• {'✅ Активен' if current_model == 'lite' else '❌ Не активен'}

**Алиса Про** (YandexGPT 5.1 Pro)
• Для сложных задач и глубокого анализа
• Более детальные ответы
• Продвинутый анализ
• {'✅ Активен' if current_model == 'pro' else '❌ Не активен'}

Используйте кнопки на клавиатуре для переключения между режимами."""

    await update.message.reply_text(modes_text, parse_mode='Markdown')