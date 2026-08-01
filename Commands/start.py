import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from shared import load_user_data, save_user_data, find_user_id_by_username
from Commands.profile import show_shared_profile


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # Load user data from persistent storage
    load_user_data(context, user_id)

    user_data = context.user_data

    # Check for deep link parameters
    args = context.args
    if args and args[0].startswith('profile_'):
        # Handle profile sharing link
        target_identifier = args[0].replace('profile_', '')

        # Try to find user by username first, then by ID
        target_user_id = find_user_id_by_username(target_identifier)
        if target_user_id is None:
            # If not found as username, treat as user_id
            target_user_id = target_identifier

        await show_shared_profile(update, context, target_user_id)
        return

    # Check if user is already configured
    if user_data.get('setup_completed', False):
        await update.message.reply_text("Вы уже настроены! Можете начинать общение или использовать /settings для изменения настроек.")
        return

    text = ("Привет! Этот бот - полигон для разработки системы APAS, здесь ты общаешься с AI ассистентом в режиме разработки и можешь увидеть как развивается экосистема ИИ сервисов. Для начала нам нужно познакомиться, выбери один из двух видов настройки:")

    keyboard = [
        [InlineKeyboardButton("Простая настройка", callback_data='setup_simple')],
        [InlineKeyboardButton("Расширенная настройка", callback_data='setup_advanced')],
        [InlineKeyboardButton("Гостевой режим", callback_data='guest_mode')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, reply_markup=reply_markup)


async def handle_setup_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # Load user data from persistent storage
    load_user_data(context, user_id)
    
    user_data = context.user_data
    setup_step = user_data.get('setup_step')
    user_message = update.message.text.strip()

    if setup_step == 'simple_name':
        user_data['name'] = user_message
        user_data['setup_step'] = 'simple_notifications'

        text = f"Этап 2/3\nПриятно познакомиться {user_message}! Какие уведомления ты хочешь получать?"
        keyboard = [
            [InlineKeyboardButton("Получать все", callback_data='notifications_all')],
            [InlineKeyboardButton("Обновления системы", callback_data='notifications_updates')],
            [InlineKeyboardButton("Внутренние изменения", callback_data='notifications_changes')],
            [InlineKeyboardButton("Промо сообщения", callback_data='notifications_promo')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(text, reply_markup=reply_markup)
        save_user_data(context, user_id)

    elif setup_step == 'advanced_name':
        user_data['name'] = user_message
        user_data['setup_step'] = 'advanced_age'

        text = f"Этап 2/5\nПриятно познакомиться {user_message}! Сколько тебе лет?"
        await update.message.reply_text(text)
        save_user_data(context, user_id)

    elif setup_step == 'advanced_age':
        try:
            age = int(user_message)
            if age < 18:
                text = f"К сожалению системой APAS можно пользоваться только с 18 лет. Вы уверены что вам {age}?"
                keyboard = [
                    [InlineKeyboardButton("Изменить возраст", callback_data='change_age')],
                    [InlineKeyboardButton("Сообщить о проблеме", callback_data='report_age_issue')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(text, reply_markup=reply_markup)
            else:
                user_data['age'] = age
                user_data['setup_step'] = 'advanced_city'
                text = "Этап 3/5\nСупер! Из какого вы города?"
                await update.message.reply_text(text)
                save_user_data(context, user_id)
        except ValueError:
            await update.message.reply_text("Пожалуйста, введите возраст цифрами (например: 25)")

    elif setup_step == 'advanced_city':
        user_data['pending_city'] = user_message
        text = f"Вы из {user_message}?"
        keyboard = [
            [InlineKeyboardButton("Верно", callback_data='city_confirm')],
            [InlineKeyboardButton("Нет", callback_data='city_change')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(text, reply_markup=reply_markup)
        save_user_data(context, user_id)


async def handle_start_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id

    # Load user data from persistent storage
    load_user_data(context, user_id)

    user_data = context.user_data
    data = query.data

    print(f"DEBUG: handle_start_callback for user {user_id}, data: {data}, current setup_step: {user_data.get('setup_step')}")

    if data == 'setup_simple':
        user_data['setup_step'] = 'simple_name'
        text = "Этап 1/3\nКак вас зовут?"
        await query.edit_message_text(text)
        save_user_data(context, user_id)

    elif data == 'setup_advanced':
        user_data['setup_step'] = 'advanced_name'
        text = "Этап 1/5\nКак вас зовут?"
        await query.edit_message_text(text)
        save_user_data(context, user_id)

    elif data.startswith('notifications_'):
        if data == 'notifications_all':
            user_data['updates_enabled'] = True
            user_data['changes_enabled'] = True
            user_data['promo_enabled'] = True
        elif data == 'notifications_updates':
            user_data['updates_enabled'] = True
            user_data['changes_enabled'] = False
            user_data['promo_enabled'] = False
        elif data == 'notifications_changes':
            user_data['updates_enabled'] = False
            user_data['changes_enabled'] = True
            user_data['promo_enabled'] = False
        elif data == 'notifications_promo':
            user_data['updates_enabled'] = False
            user_data['changes_enabled'] = False
            user_data['promo_enabled'] = True

        # Check if this is simple or advanced setup completion
        if user_data.get('setup_step') == 'simple_notifications':
            user_data['setup_step'] = 'simple_complete'
            text = "Этап 3/3\nНастройка завершена! Теперь вы можете начать общение с AI ассистентом."
        elif user_data.get('setup_step') == 'advanced_notifications':
            user_data['setup_step'] = 'advanced_complete'
            text = "Этап 5/5\nНастройка завершена! Теперь вы можете начать общение с AI ассистентом."
        else:
            text = "Настройки уведомлений обновлены."

        keyboard = [
            [InlineKeyboardButton("Начать разговор", callback_data='start_chat')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup)
        save_user_data(context, user_id)

    elif data == 'change_age':
        user_data['setup_step'] = 'advanced_age'
        text = "Введите ваш возраст цифрами:"
        await query.edit_message_text(text)
        save_user_data(context, user_id)

    elif data == 'report_age_issue':
        text = ("Для сообщения о проблеме с возрастным ограничением напишите @rakcheev_me с описанием ситуации.")
        await query.edit_message_text(text)

    elif data == 'city_confirm':
        user_data['city'] = user_data.get('pending_city', '')
        user_data.pop('pending_city', None)
        user_data['setup_step'] = 'advanced_notifications'

        text = "Этап 4/5\nКакие уведомления вы хотите получать?"
        keyboard = [
            [InlineKeyboardButton("Получать все", callback_data='notifications_all')],
            [InlineKeyboardButton("Обновления системы", callback_data='notifications_updates')],
            [InlineKeyboardButton("Внутренние изменения", callback_data='notifications_changes')],
            [InlineKeyboardButton("Промо сообщения", callback_data='notifications_promo')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup)
        save_user_data(context, user_id)

    elif data == 'city_change':
        user_data['setup_step'] = 'advanced_city'
        text = "Из какого вы города?"
        await query.edit_message_text(text)
        save_user_data(context, user_id)

    elif data == 'location_confirm':
        # Save location coordinates as city (for demo purposes)
        temp_location = user_data.get('temp_location', {})
        if temp_location:
            user_data['city'] = f"Координаты: {temp_location['lat']:.4f}, {temp_location['lon']:.4f}"
            user_data.pop('temp_location', None)
        user_data['setup_step'] = 'advanced_notifications'

        text = "Этап 4/5\nКакие уведомления вы хотите получать?"
        keyboard = [
            [InlineKeyboardButton("Получать все", callback_data='notifications_all')],
            [InlineKeyboardButton("Обновления системы", callback_data='notifications_updates')],
            [InlineKeyboardButton("Внутренние изменения", callback_data='notifications_changes')],
            [InlineKeyboardButton("Промо сообщения", callback_data='notifications_promo')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup)
        save_user_data(context, user_id)

    elif data == 'location_text':
        user_data['setup_step'] = 'advanced_city'
        text = "Из какого вы города?"
        await query.edit_message_text(text)
        save_user_data(context, user_id)

    elif data == 'start_chat':
        user_data['setup_completed'] = True
        user_data['registration_date'] = str(int(time.time()))  # Use timestamp for proper ordering
        user_data.pop('setup_step', None)
        user_data.pop('guest_mode', None)  # Remove guest mode flag upon registration
        text = "Отлично! Теперь вы можете общаться с AI ассистентом. Просто напишите сообщение!"
        await query.edit_message_text(text)
        save_user_data(context, user_id)

    elif data == 'guest_mode':
        # Переход в гостевой режим
        from Commands.guest import guest_command
        # Создам временный update для guest_command
        class TempUpdate:
            def __init__(self, original_update):
                self.message = original_update.callback_query.message
                self.effective_user = original_update.effective_user
                self.effective_chat = original_update.effective_chat

        temp_update = TempUpdate(update)
        await guest_command(temp_update, context)