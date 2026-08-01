from telegram import Update
from telegram.ext import ContextTypes
from shared import users_data, format_registration_date, load_user_data


async def iss_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # Load user data from persistent storage
    load_user_data(context, user_id)

    user_data = context.user_data

    # Check if user is in guest mode
    from Commands.guest import is_guest_mode, guest_restricted_message
    if is_guest_mode(user_data):
        await guest_restricted_message(update, context)
        return

    # Count registered users
    registered_users = 0
    latest_user = None
    latest_timestamp = 0

    for user_id, user_data in users_data.items():
        if user_data.get('setup_completed', False):
            registered_users += 1

            # Find the latest registered user by timestamp
            reg_date_str = user_data.get('registration_date', '')
            try:
                timestamp = int(reg_date_str)
                if timestamp > latest_timestamp:
                    latest_timestamp = timestamp
                    latest_user = user_data
            except (ValueError, TypeError):
                continue  # Skip invalid timestamps

    # Format latest user info
    if latest_user:
        name = latest_user.get('name', 'Неизвестно')
        username = latest_user.get('username', '')
        latest_user_display = f"{name} @{username}" if username else name
    else:
        latest_user_display = "Нет зарегистрированных пользователей"

    text = ("Intelligence Social System - ISS\n"
            f"Количество пользователей: {registered_users}\n"
            f"Новый пользователь: {latest_user_display}")

    await update.message.reply_text(text)