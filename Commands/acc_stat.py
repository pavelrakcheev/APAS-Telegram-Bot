from telegram import Update
from telegram.ext import ContextTypes
from shared import load_user_data


async def acc_stat_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Команда /acc_stat - показывает статус учетной записи и права доступа пользователя
    """
    user_id = update.effective_user.id

    # Load user data from persistent storage
    load_user_data(context, user_id)

    user_data = context.user_data

    # Check if user is in guest mode
    from Commands.guest import is_guest_mode, guest_restricted_message
    if is_guest_mode(user_data):
        await guest_restricted_message(update, context)
        return

    # Check if user is configured
    if not user_data.get('setup_completed', False):
        await update.message.reply_text("Сначала настройте свой профиль с помощью команды /start")
        return

    # Get Telegram username and user ID
    telegram_username = update.effective_user.username
    user_id = update.effective_user.id
    display_name = f"@{telegram_username}" if telegram_username else f"ID: {user_id}"

    # Check admin status based on Telegram username OR user ID
    if telegram_username == 'rakcheev_me' or user_id == 349746155:
        status = "Админ. Полный доступ."
    else:
        status = "Обычный пользователь. Нет административных прав."

    text = ("Статус учетной записи\n"
            f"{display_name}\n"
            f"{status}")

    await update.message.reply_text(text)