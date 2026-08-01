from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from telegram.ext import ContextTypes
from shared import load_user_data, save_user_data, users_data, format_registration_date, is_username_available, find_user_id_by_username
import re


async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Команда /profile - показывает профиль пользователя
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

    name = user_data.get('name', 'Не указано')
    age = user_data.get('age', 'Не указано')
    city = user_data.get('city', 'Не указано')
    reg_date_raw = user_data.get('registration_date', 'Не указано')
    reg_date = format_registration_date(reg_date_raw) if reg_date_raw != 'Не указано' else 'Не указано'
    username = user_data.get('username', '')
    points = user_data.get('points', 60)

    name_display = f"{name} @{username}" if username else name

    text = ("Ваш профиль в APAS\n"
            f"Имя: {name_display}\n"
            f"Возраст: {age}\n"
            f"Город: {city}\n"
            f"Дата регистрации: {reg_date}\n"
            f"🏆 Баллы: {points} Points")

    # Add ISS Play info if linked
    if user_data.get('iss_play_linked'):
        iss_nickname = user_data.get('iss_play_nickname', '')
        text += f"\n🎮 ISS Play: #{iss_nickname}"

    # Build keyboard based on whether user has username
    keyboard = [
        [InlineKeyboardButton("Редактировать", callback_data='edit_profile')],
    ]

    # Only add "Set username" button if user doesn't have one
    if not username:
        keyboard.append([InlineKeyboardButton("Задать юзернейм", callback_data='set_username')])

    keyboard.extend([
        [InlineKeyboardButton("🏆 Просмотр Points", callback_data='view_points')],
        [InlineKeyboardButton("👤 Открыть в Mini App", web_app=WebAppInfo(url="https://iss-app-for-telegram-bot.onrender.com"))],
        [InlineKeyboardButton("Поделиться профилем", callback_data='share_profile')],
        [InlineKeyboardButton("Удалить профиль", callback_data='delete_profile')]
    ])

    # Add ISS Play button if linked
    if user_data.get('iss_play_linked'):
        keyboard.insert(1, [InlineKeyboardButton("🎮 Мой ISS Play", callback_data='my_iss_play')])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, reply_markup=reply_markup)


async def show_shared_profile(update: Update, context: ContextTypes.DEFAULT_TYPE, target_user_id: str):
    """
    Показывает профиль другого пользователя
    """
    # Check if target user exists and is registered
    if target_user_id not in users_data:
        text = "Пользователь не найден в системе ISS."
        await update.message.reply_text(text)
        return

    target_user_data = users_data[target_user_id]
    if not target_user_data.get('setup_completed', False):
        text = "Пользователь не завершили настройку профиля."
        await update.message.reply_text(text)
        return

    # Get current user data to check if they can view full profile
    current_user_id = update.effective_user.id
    current_user_data = context.user_data

    # Only show full profile if current user is registered
    if not current_user_data.get('setup_completed', False):
        text = ("Профиль ISS\n"
                f"Имя: [Данные пользователя {target_user_id}]\n"
                f"Возраст: [Защищено]\n"
                f"Город: [Защищено]\n"
                f"Дата регистрации: [Данные недоступны]\n\n"
                "Для просмотра полного профиля необходимо быть зарегистрированным пользователем системы ISS и иметь соответствующие права доступа.")

        keyboard = [
            [InlineKeyboardButton("Написать сообщение через APAS", callback_data=f'message_user_{target_user_id}')],
            [InlineKeyboardButton("Добавить в друзья", callback_data=f'add_friend_{target_user_id}')],
            [InlineKeyboardButton("Вернуться к настройке", callback_data='setup_simple')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(text, reply_markup=reply_markup)
        return

    # Show full profile for registered users
    name = target_user_data.get('name', 'Не указано')
    age = target_user_data.get('age', 'Не указано')
    city = target_user_data.get('city', 'Не указано')
    reg_date_raw = target_user_data.get('registration_date', 'Не указано')
    reg_date = format_registration_date(reg_date_raw) if reg_date_raw != 'Не указано' else 'Не указано'
    username = target_user_data.get('username', '')

    name_display = f"{name} @{username}" if username else name

    text = ("Профиль пользователя ISS\n"
            f"Имя: {name_display}\n"
            f"Возраст: {age}\n"
            f"Город: {city}\n"
            f"Дата регистрации: {reg_date}")

    keyboard = [
        [InlineKeyboardButton("Написать сообщение через APAS", callback_data=f'message_user_{target_user_id}')],
        [InlineKeyboardButton("Добавить в друзья", callback_data=f'add_friend_{target_user_id}')],
        [InlineKeyboardButton("Вернуться к профилю", callback_data='back_to_profile')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, reply_markup=reply_markup)


async def handle_profile_setup_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает текстовые сообщения для редактирования профиля
    """
    user_id = update.effective_user.id
    user_data = context.user_data
    user_message = update.message.text.strip()

    if user_data.get('setup_step') == 'edit_name':
        user_data['name'] = user_message
        user_data.pop('setup_step', None)
        user_data.pop('editing_profile', None)

        text = f"Имя успешно изменено на {user_message}!"
        keyboard = [
            [InlineKeyboardButton("Вернуться к профилю", callback_data='back_to_profile')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(text, reply_markup=reply_markup)
        save_user_data(context, user_id)

    elif user_data.get('setup_step') == 'edit_age':
        try:
            age = int(user_message)
            if age < 18:
                text = f"К сожалению системой APAS можно пользоваться только с 18 лет. Вы уверены что вам {age}?"
                keyboard = [
                    [InlineKeyboardButton("Изменить возраст", callback_data='change_age_edit')],
                    [InlineKeyboardButton("Сообщить о проблеме", callback_data='report_age_issue')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(text, reply_markup=reply_markup)
            else:
                user_data['age'] = age
                user_data.pop('setup_step', None)
                user_data.pop('editing_profile', None)

                text = f"Возраст успешно изменен на {age}!"
                keyboard = [
                    [InlineKeyboardButton("Вернуться к профилю", callback_data='back_to_profile')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(text, reply_markup=reply_markup)
                save_user_data(context, user_id)
        except ValueError:
            await update.message.reply_text("Пожалуйста, введите возраст цифрами (например: 25)")

    elif user_data.get('setup_step') == 'edit_city':
        user_data['pending_city'] = user_message
        text = f"Подтвердите новый город: {user_message}?"
        keyboard = [
            [InlineKeyboardButton("Верно", callback_data='confirm_city_edit')],
            [InlineKeyboardButton("Изменить", callback_data='change_city_edit')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(text, reply_markup=reply_markup)
        save_user_data(context, user_id)

    elif user_data.get('setup_step') == 'set_username':
        username = user_message.strip()

        if len(username) < 5:
            await update.message.reply_text("Юзернейм должен содержать минимум 5 символов. Попробуйте еще раз:")
            return

        # Validate username format
        if not re.match(r'^[a-zA-Z0-9_.]+$', username):
            await update.message.reply_text("Юзернейм может содержать только латинские буквы, цифры, нижние подчеркивания и точки. Попробуйте еще раз:")
            return

        # Check if username is already taken
        if not is_username_available(username, user_id):
            await update.message.reply_text("Этот юзернейм уже занят. Придумайте другой.")
            return

        # Username is available, set it
        user_data['username'] = username
        user_data.pop('setup_step', None)

        text = f"Юзернейм @{username} успешно установлен!"
        keyboard = [
            [InlineKeyboardButton("Вернуться к профилю", callback_data='back_to_profile')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(text, reply_markup=reply_markup)
        save_user_data(context, user_id)

    elif user_data.get('setup_step') == 'edit_username':
        username = user_message.strip()

        if len(username) < 5:
            await update.message.reply_text("Юзернейм должен содержать минимум 5 символов. Попробуйте еще раз:")
            return

        # Validate username format
        if not re.match(r'^[a-zA-Z0-9_.]+$', username):
            await update.message.reply_text("Юзернейм может содержать только латинские буквы, цифры, нижние подчеркивания и точки. Попробуйте еще раз:")
            return

        # Check if username is already taken (allow keeping current username)
        current_username = user_data.get('username', '')
        if username != current_username and not is_username_available(username, user_id):
            await update.message.reply_text("Этот юзернейм уже занят. Придумайте другой.")
            return

        # Username is available, set it
        user_data['username'] = username
        user_data.pop('setup_step', None)
        user_data.pop('editing_profile', None)

        text = f"Юзернейм успешно изменен на @{username}!"
        keyboard = [
            [InlineKeyboardButton("Вернуться к профилю", callback_data='back_to_profile')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(text, reply_markup=reply_markup)
        save_user_data(context, user_id)


async def handle_profile_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает callback-запросы для профиля
    """
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    user_data = context.user_data
    data = query.data

    if data == 'edit_profile':
        # Start profile editing process
        user_data['editing_profile'] = True
        text = ("Редактирование профиля\n"
                "Выберите, что хотите изменить:")
        keyboard = [
            [InlineKeyboardButton("Имя", callback_data='edit_name')],
            [InlineKeyboardButton("Возраст", callback_data='edit_age')],
            [InlineKeyboardButton("Город", callback_data='edit_city')],
            [InlineKeyboardButton("Юзернейм", callback_data='edit_username')],
            [InlineKeyboardButton("Отмена", callback_data='cancel_edit')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup)
        save_user_data(context, user_id)

    elif data == 'set_username':
        text = ("Придумайте свой юзернейм чтобы вас проще было найти. Взаимодействовать с вашим профилем могут только зарегистрированные пользователи в ISS.\n"
                "Длина юзернейма должна быть от 5 символов.")
        await query.edit_message_text(text)
        user_data['setup_step'] = 'set_username'
        save_user_data(context, user_id)

    elif data == 'share_profile':
        username = user_data.get('username', '')
        if not username:
            text = ("У вас не установлен юзернейм. Сначала установите юзернейм, чтобы поделиться профилем.")
            keyboard = [
                [InlineKeyboardButton("Задать юзернейм", callback_data='set_username')],
                [InlineKeyboardButton("Вернуться к профилю", callback_data='back_to_profile')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(text, reply_markup=reply_markup)
            return

        bot_username = "Intelligence_playground_bot"  # Замените на реальный username бота
        profile_link = f"https://t.me/{bot_username}?start=profile_{username}"

        text = ("Ваша ссылка профиля:\n"
                f"{profile_link}\n\n"
                "Только пользователи в системе ISS могут просматривать ваш профиль.")
        await query.edit_message_text(text)

    elif data == 'delete_profile':
        text = ("⚠️ Вы уверены, что хотите удалить свой профиль?\n\n"
                "Это действие нельзя отменить. Все ваши данные будут удалены навсегда.")
        keyboard = [
            [InlineKeyboardButton("❌ Да, удалить профиль", callback_data='confirm_delete')],
            [InlineKeyboardButton("🔙 Отмена", callback_data='cancel_delete')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup)

    elif data == 'confirm_delete':
        # Clear all user data
        user_data.clear()
        text = ("Профиль удален.\n"
                "Для повторной настройки используйте команду /start")
        await query.edit_message_text(text)
        save_user_data(context, user_id)

    elif data == 'cancel_delete':
        # Return to profile view
        name = user_data.get('name', 'Не указано')
        age = user_data.get('age', 'Не указано')
        city = user_data.get('city', 'Не указано')
        reg_date_raw = user_data.get('registration_date', 'Не указано')
        reg_date = format_registration_date(reg_date_raw) if reg_date_raw != 'Не указано' else 'Не указано'
        username = user_data.get('username', '')

        name_display = f"{name} @{username}" if username else name

        text = ("Ваш профиль в APAS\n"
                f"Имя: {name_display}\n"
                f"Возраст: {age}\n"
                f"Город: {city}\n"
                f"Дата регистрации: {reg_date}")

        # Build keyboard based on whether user has username
        keyboard = [
            [InlineKeyboardButton("Редактировать", callback_data='edit_profile')],
        ]

        # Only add "Set username" button if user doesn't have one
        if not username:
            keyboard.append([InlineKeyboardButton("Задать юзернейм", callback_data='set_username')])

        keyboard.extend([
            [InlineKeyboardButton("Поделиться профилем", callback_data='share_profile')],
            [InlineKeyboardButton("Удалить профиль", callback_data='delete_profile')]
        ])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup)

    elif data == 'edit_name':
        user_data['setup_step'] = 'edit_name'
        text = f"Текущее имя: {user_data.get('name', 'Не указано')}\nВведите новое имя:"
        await query.edit_message_text(text)
        save_user_data(context, user_id)

    elif data == 'edit_age':
        user_data['setup_step'] = 'edit_age'
        text = f"Текущий возраст: {user_data.get('age', 'Не указано')}\nВведите новый возраст:"
        await query.edit_message_text(text)
        save_user_data(context, user_id)

    elif data == 'edit_city':
        user_data['setup_step'] = 'edit_city'
        text = f"Текущий город: {user_data.get('city', 'Не указано')}\nВведите новый город:"
        await query.edit_message_text(text)
        save_user_data(context, user_id)

    elif data == 'edit_username':
        user_data['setup_step'] = 'edit_username'
        current_username = user_data.get('username', 'Не установлен')
        text = f"Текущий юзернейм: @{current_username}\nВведите новый юзернейм (минимум 5 символов):"
        await query.edit_message_text(text)
        save_user_data(context, user_id)

    elif data == 'cancel_edit':
        # Return to profile view
        name = user_data.get('name', 'Не указано')
        age = user_data.get('age', 'Не указано')
        city = user_data.get('city', 'Не указано')
        reg_date_raw = user_data.get('registration_date', 'Не указано')
        reg_date = format_registration_date(reg_date_raw) if reg_date_raw != 'Не указано' else 'Не указано'
        username = user_data.get('username', '')

        name_display = f"{name} @{username}" if username else name

        text = ("Ваш профиль в APAS\n"
                f"Имя: {name_display}\n"
                f"Возраст: {age}\n"
                f"Город: {city}\n"
                f"Дата регистрации: {reg_date}")

        # Build keyboard based on whether user has username
        keyboard = [
            [InlineKeyboardButton("Редактировать", callback_data='edit_profile')],
        ]

        # Only add "Set username" button if user doesn't have one
        if not username:
            keyboard.append([InlineKeyboardButton("Задать юзернейм", callback_data='set_username')])

        keyboard.extend([
            [InlineKeyboardButton("Поделиться профилем", callback_data='share_profile')],
            [InlineKeyboardButton("Удалить профиль", callback_data='delete_profile')]
        ])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup)

    elif data == 'change_age_edit':
        user_data['setup_step'] = 'edit_age'
        text = "Введите новый возраст цифрами:"
        await query.edit_message_text(text)
        save_user_data(context, user_id)

    elif data == 'confirm_city_edit':
        user_data['city'] = user_data.get('pending_city', '')
        user_data.pop('pending_city', None)
        user_data.pop('setup_step', None)
        user_data.pop('editing_profile', None)

        text = f"Город успешно изменен на {user_data['city']}!"
        keyboard = [
            [InlineKeyboardButton("Вернуться к профилю", callback_data='back_to_profile')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup)
        save_user_data(context, user_id)

    elif data == 'confirm_location_edit':
        # Save location coordinates as city for profile editing
        temp_location = user_data.get('temp_location', {})
        if temp_location:
            user_data['city'] = f"Координаты: {temp_location['lat']:.4f}, {temp_location['lon']:.4f}"
            user_data.pop('temp_location', None)
        user_data.pop('setup_step', None)
        user_data.pop('editing_profile', None)

        text = f"Город успешно изменен!"
        keyboard = [
            [InlineKeyboardButton("Вернуться к профилю", callback_data='back_to_profile')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup)
        save_user_data(context, user_id)

    elif data == 'change_city_edit':
        user_data['setup_step'] = 'edit_city'
        text = "Введите новый город:"
        await query.edit_message_text(text)
        save_user_data(context, user_id)

    elif data == 'change_location_edit':
        user_data['setup_step'] = 'edit_city'
        text = "Отправьте новую геопозицию или введите город текстом:"
        await query.edit_message_text(text)
        save_user_data(context, user_id)

    elif data == 'back_to_profile':
        # Return to profile view
        name = user_data.get('name', 'Не указано')
        age = user_data.get('age', 'Не указано')
        city = user_data.get('city', 'Не указано')
        reg_date_raw = user_data.get('registration_date', 'Не указано')
        reg_date = format_registration_date(reg_date_raw) if reg_date_raw != 'Не указано' else 'Не указано'
        username = user_data.get('username', '')
        points = user_data.get('points', 60)

        name_display = f"{name} @{username}" if username else name

        text = ("Ваш профиль в APAS\n"
                f"Имя: {name_display}\n"
                f"Возраст: {age}\n"
                f"Город: {city}\n"
                f"Дата регистрации: {reg_date}\n"
                f"🏆 Баллы: {points} Points")

        # Build keyboard based on whether user has username
        keyboard = [
            [InlineKeyboardButton("Редактировать", callback_data='edit_profile')],
        ]

        # Only add "Set username" button if user doesn't have one
        if not username:
            keyboard.append([InlineKeyboardButton("Задать юзернейм", callback_data='set_username')])

        keyboard.extend([
            [InlineKeyboardButton("🏆 Просмотр Points", callback_data='view_points')],
            [InlineKeyboardButton("👤 Открыть в Mini App", web_app=WebAppInfo(url="https://iss-app-for-telegram-bot.onrender.com"))],
            [InlineKeyboardButton("Поделиться профилем", callback_data='share_profile')],
            [InlineKeyboardButton("Удалить профиль", callback_data='delete_profile')]
        ])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup)

    elif data == 'view_points':
        # Show points information directly
        points = user_data.get('points', 60)

        text = (f"🏆 Ваши баллы в системе ISS\n\n"
                f"💰 Текущий баланс: {points} Points\n\n"
                f"💡 Баллы можно заработать, активно используя систему ISS и выполняя различные задания.")

        keyboard = [
            [InlineKeyboardButton("💰 Заработать больше", callback_data='earn_more_points')],
            [InlineKeyboardButton("📊 История накоплений", callback_data='points_history')],
            [InlineKeyboardButton("🔙 Вернуться к профилю", callback_data='back_to_profile')]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup)
        # Mark that user came from profile
        user_data['came_from_profile'] = True
        save_user_data(context, user_id)
        return

    elif data == 'earn_more_points':
        text = ("💰 Как заработать больше баллов?\n\n"
                "🎯 Выполняйте ежедневные задания\n"
                "💬 Активно общайтесь с системой ISS\n"
                "📝 Создавайте полезные посты\n"
                "⭐ Участвуйте в специальных акциях\n\n"
                "🚧 Функция заработка баллов находится в разработке!")

        keyboard = [
            [InlineKeyboardButton("🔙 Назад к баллам", callback_data='back_to_points')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup)

    elif data == 'back_to_points':
        # Return to points view
        points = user_data.get('points', 60)

        text = (f"🏆 Ваши баллы в системе ISS\n\n"
                f"� Текущий баланс: {points} Points\n\n"
                f"💡 Баллы можно заработать, активно используя систему ISS и выполняя различные задания.")

        keyboard = [
            [InlineKeyboardButton("� Заработать больше", callback_data='earn_more_points')],
            [InlineKeyboardButton("📊 История накоплений", callback_data='points_history')],
            [InlineKeyboardButton("🔙 Вернуться к профилю", callback_data='back_to_profile')]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup)

    elif data.startswith('message_user_'):
        target_user_id = data.replace('message_user_', '')
        text = f"Функция отправки сообщения пользователю {target_user_id} будет реализована в будущих обновлениях системы ISS."
        await query.edit_message_text(text)

    elif data == 'my_iss_play':
        # Show ISS Play profile
        from shared import iss_play_accounts
        iss_account = iss_play_accounts.get(str(user_id), {})
        nickname = iss_account.get('nickname', '')
        created_at = iss_account.get('created_at', 0)
        linked = iss_account.get('linked_to_iss', False)
        
        created_date = format_registration_date(str(created_at)) if created_at else 'Неизвестно'
        
        text = (f"🎮 Ваш профиль ISS Play\n\n"
                f"Никнейм: #{nickname}\n"
                f"Дата создания: {created_date}\n"
                f"Связан с ISS: {'Да' if linked else 'Нет'}\n\n"
                f"🎯 Достижения: В разработке\n"
                f"🏆 Рейтинг: В разработке")
        
        keyboard = [
            [InlineKeyboardButton("🎮 Играть", callback_data='games_back_to_main')],
            [InlineKeyboardButton("🔙 Вернуться к профилю", callback_data='back_to_profile')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup)