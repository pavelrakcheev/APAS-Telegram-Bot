from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from shared import load_user_data, save_user_data


async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Команда /settings - показывает параметры бота и настройки стриминга
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

    streaming_enabled = user_data.get('streaming_enabled', True)

    text = ("Параметры бота\n"
            f"Генерация текста в реальном времени ({'включено' if streaming_enabled else 'выключено'})\n\n"
            "⚠️ В данный момент стриминг генерации сообщений работает нестабильно и значительно уменьшает скорость ответов.\n\n"
            "📝 При включенном стриминге статус 'печатает' не показывается.\n"
            "📝 При выключенном стриминге показывается статус 'печатает'.")

    keyboard = [
        [InlineKeyboardButton(f"{'Выключить' if streaming_enabled else 'Включить'} генерацию текста в реальном времени", callback_data='toggle_streaming')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, reply_markup=reply_markup)


async def handle_settings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает callback-запросы для настроек бота
    """
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id

    # Load user data from persistent storage
    load_user_data(context, user_id)

    user_data = context.user_data
    data = query.data

    if data in ['toggle_updates', 'toggle_changes', 'toggle_promo', 'toggle_all', 'toggle_streaming']:
        # Existing toggle logic
        if data == 'toggle_updates':
            user_data['updates_enabled'] = not user_data.get('updates_enabled', True)
        elif data == 'toggle_changes':
            user_data['changes_enabled'] = not user_data.get('changes_enabled', True)
        elif data == 'toggle_promo':
            user_data['promo_enabled'] = not user_data.get('promo_enabled', True)
        elif data == 'toggle_all':
            # Check current state - if all are enabled, disable all; if any are disabled, enable all
            current_updates = user_data.get('updates_enabled', True)
            current_changes = user_data.get('changes_enabled', True)
            current_promo = user_data.get('promo_enabled', True)

            all_enabled = current_updates and current_changes and current_promo
            if all_enabled:
                # Disable all
                user_data['updates_enabled'] = False
                user_data['changes_enabled'] = False
                user_data['promo_enabled'] = False
            else:
                # Enable all
                user_data['updates_enabled'] = True
                user_data['changes_enabled'] = True
                user_data['promo_enabled'] = True
        elif data == 'toggle_streaming':
            user_data['streaming_enabled'] = not user_data.get('streaming_enabled', True)

        # Save user data after changes
        save_user_data(context, user_id)

        # Check if this is a settings callback or notifications callback
        if data == 'toggle_streaming':
            # Update settings message
            streaming_enabled = user_data.get('streaming_enabled', True)

            text = ("Параметры бота\n"
                    f"Генерация текста в реальном времени ({'включено' if streaming_enabled else 'выключено'})\n\n"
                    "⚠️ В данный момент стриминг генерации сообщений работает нестабильно и значительно уменьшает скорость ответов.\n\n"
                    "📝 При включенном стриминге статус 'печатает' не показывается.\n"
                    "📝 При выключенном стриминге показывается статус 'печатает'.")

            keyboard = [
                [InlineKeyboardButton(f"{'Выключить' if streaming_enabled else 'Включить'} генерацию текста в реальном времени", callback_data='toggle_streaming')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(text=text, reply_markup=reply_markup)
        else:
            # Update notifications message
            updates_enabled = user_data.get('updates_enabled', True)
            changes_enabled = user_data.get('changes_enabled', True)
            promo_enabled = user_data.get('promo_enabled', True)

            # Check if all notifications are enabled or disabled
            all_enabled = updates_enabled and changes_enabled and promo_enabled

            text = ("Настройки уведомлений\n"
                    f"Получение уведомлений о новых функциях и версиях ({'включено' if updates_enabled else 'выключено'})\n"
                    f"Уведомления о внутренних изменениях ({'включено' if changes_enabled else 'выключено'})\n"
                    f"Промо-сообщения ({'включено' if promo_enabled else 'выключено'})")

            keyboard = [
                [InlineKeyboardButton(f"{'Отключить' if updates_enabled else 'Включить'} уведомления об обновлениях", callback_data='toggle_updates')],
                [InlineKeyboardButton(f"{'Отключить' if changes_enabled else 'Включить'} уведомления об изменениях", callback_data='toggle_changes')],
                [InlineKeyboardButton(f"{'Отключить' if promo_enabled else 'Включить'} промо сообщения", callback_data='toggle_promo')],
                [InlineKeyboardButton(f"{'Выключить все' if all_enabled else 'Включить все'}", callback_data='toggle_all')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(text=text, reply_markup=reply_markup)