from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from shared import load_user_data, save_user_data, users_data, check_admin_access
import logging
import os
from src.config import ADMIN_PASSWORD


async def createpost_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Команда /createpost - начинает процесс создания поста для рассылки пользователям
    """
    user_id = update.effective_user.id

    # Проверка доступа администратора
    if not check_admin_access(user_id):
        await update.message.reply_text("❌ У вас нет доступа к этой команде.")
        return

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

    # Start post creation process
    user_data['post_creation_step'] = 'enter_text'
    text = "Этап 1/5\nВведите текст сообщения"
    await update.message.reply_text(text)
    save_user_data(context, user_id)


async def handle_post_setup_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает текстовые сообщения для создания поста
    """
    user_id = update.effective_user.id
    user_data = context.user_data
    user_message = update.message.text.strip()

    # Handle post creation steps
    post_step = user_data.get('post_creation_step')
    if post_step == 'enter_text':
        user_data['pending_post_text'] = user_message
        user_data['post_creation_step'] = 'confirm_text'

        text = f"""Этап 2/5
Ваше сообщение:
{user_message}

Что вы хотите сделать?"""

        keyboard = [
            [InlineKeyboardButton("Продолжить", callback_data='post_continue')],
            [InlineKeyboardButton("Редактировать", callback_data='post_edit')],
            [InlineKeyboardButton("Отмена", callback_data='post_cancel')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(text, reply_markup=reply_markup)
        save_user_data(context, user_id)

    elif post_step == 'enter_secret_phrase':
        if user_message.strip() == ADMIN_PASSWORD:
            user_data['post_creation_step'] = 'final_confirm'

            post_text = user_data.get('pending_post_text', '')
            post_category = user_data.get('pending_post_category', '')

            text = f"""Этап 5/5
Все готово! Можно опубликовывать пост

Текст: {post_text}
Категория: {post_category}"""

            keyboard = [
                [InlineKeyboardButton("Опубликовать сейчас", callback_data='post_publish')],
                [InlineKeyboardButton("Изменить категорию", callback_data='post_change_category')],
                [InlineKeyboardButton("Редактировать текст", callback_data='post_edit_text')],
                [InlineKeyboardButton("Отмена", callback_data='post_cancel')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(text, reply_markup=reply_markup)
        else:
            await update.message.reply_text("❌ Неверная секретная фраза. Попробуйте еще раз:")
        save_user_data(context, user_id)


async def handle_post_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает callback-запросы для создания поста
    """
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    user_data = context.user_data
    data = query.data

    # Handle post creation callbacks
    if data == 'post_continue':
        user_data['post_creation_step'] = 'select_category'

        text = "Этап 3/5\nВыберите категорию для поста:"

        keyboard = [
            [InlineKeyboardButton("Обновления", callback_data='post_cat_updates')],
            [InlineKeyboardButton("Изменения", callback_data='post_cat_changes')],
            [InlineKeyboardButton("Промо", callback_data='post_cat_promo')],
            [InlineKeyboardButton("Критические исправления", callback_data='post_cat_critical')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup)
        save_user_data(context, user_id)

    elif data == 'post_edit':
        user_data['post_creation_step'] = 'enter_text'
        text = "Этап 1/5\nВведите текст сообщения заново:"
        await query.edit_message_text(text)
        save_user_data(context, user_id)

    elif data == 'post_cancel':
        # Clear post creation data
        post_keys = [k for k in user_data.keys() if k.startswith('post_') or k.startswith('pending_post')]
        for key in post_keys:
            user_data.pop(key, None)

        text = "Создание поста отменено."
        await query.edit_message_text(text)
        save_user_data(context, user_id)

    elif data.startswith('post_cat_'):
        category = data.replace('post_cat_', '')
        category_names = {
            'updates': 'Обновления',
            'changes': 'Изменения',
            'promo': 'Промо',
            'critical': 'Критические исправления'
        }

        user_data['pending_post_category'] = category_names.get(category, category)
        user_data['post_creation_step'] = 'enter_secret_phrase'

        text = f"""Этап 4/5
Категория: {category_names.get(category, category)}

Для подтверждения введите секретную фразу:"""

        await query.edit_message_text(text)
        save_user_data(context, user_id)

    elif data == 'post_publish':
        # Publish the post to all subscribed users
        post_text = user_data.get('pending_post_text', '')
        post_category = user_data.get('pending_post_category', '')

        # Special handling for critical updates - send to ALL users
        if post_category == 'Критические исправления':
            published_count = 0
            for user_id_str, user_info in users_data.items():
                if user_info.get('setup_completed', False):
                    try:
                        await context.bot.send_message(
                            chat_id=int(user_id_str),
                            text=f"🚨 **{post_category}**\n\n{post_text}",
                            parse_mode=None  # Disable Markdown for critical updates
                        )
                        published_count += 1
                    except Exception as e:
                        logging.error(f"Failed to send post to user {user_id_str}: {e}")

            text = f"✅ Критическое обновление отправлено всем пользователям!\nОтправлено пользователям: {published_count}"
        else:
            # Determine which users to notify based on category
            category_flags = {
                'Обновления': 'updates_enabled',
                'Изменения': 'changes_enabled',
                'Промо': 'promo_enabled'
            }

            flag_to_check = category_flags.get(post_category, '')

            if flag_to_check:
                published_count = 0
                for user_id_str, user_info in users_data.items():
                    if user_info.get('setup_completed', False) and user_info.get(flag_to_check, True):
                        try:
                            await context.bot.send_message(
                                chat_id=int(user_id_str),
                                text=f"📢 **{post_category}**\n\n{post_text}",
                                parse_mode='Markdown'
                            )
                            published_count += 1
                        except Exception as e:
                            logging.error(f"Failed to send post to user {user_id_str}: {e}")

                text = f"✅ Пост опубликован!\nОтправлено пользователям: {published_count}"
            else:
                text = "❌ Ошибка: неизвестная категория поста"

        # Clear post creation data
        post_keys = [k for k in user_data.keys() if k.startswith('post_') or k.startswith('pending_post')]
        for key in post_keys:
            user_data.pop(key, None)

        await query.edit_message_text(text)
        save_user_data(context, user_id)

    elif data == 'post_change_category':
        user_data['post_creation_step'] = 'select_category'

        text = "Этап 3/5\nВыберите новую категорию для поста:"

        keyboard = [
            [InlineKeyboardButton("Обновления", callback_data='post_cat_updates')],
            [InlineKeyboardButton("Изменения", callback_data='post_cat_changes')],
            [InlineKeyboardButton("Промо", callback_data='post_cat_promo')],
            [InlineKeyboardButton("Критические исправления", callback_data='post_cat_critical')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup)
        save_user_data(context, user_id)

    elif data == 'post_edit_text':
        user_data['post_creation_step'] = 'enter_text'
        text = "Этап 1/5\nВведите новый текст сообщения:"
        await query.edit_message_text(text)
        save_user_data(context, user_id)