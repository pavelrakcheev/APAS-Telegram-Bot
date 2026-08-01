from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import functools

from shared import load_user_data, save_user_data


def guest_mode_check(allowed_commands=None):
    """Декоратор для проверки гостевого режима"""
    if allowed_commands is None:
        allowed_commands = ['/about', '/commands', '/signup', '/start', '/guest']
    
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            user_id = update.effective_user.id
            load_user_data(context, user_id)
            user_data = context.user_data
            
            if is_guest_mode(user_data):
                # Получить имя команды из update
                command = update.message.text.split()[0] if update.message and update.message.text else ''
                if command not in allowed_commands:
                    await guest_restricted_message(update, context)
                    return
            return await func(update, context, *args, **kwargs)
        return wrapper
    return decorator


async def signup_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /signup для создания профиля"""
    # Просто перенаправляем на /start
    from Commands.start import start_command
    await start_command(update, context)


async def guest_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /guest для входа в гостевой режим"""
    user_id = update.effective_user.id

    # Load user data from persistent storage
    load_user_data(context, user_id)

    user_data = context.user_data

    # Устанавливаем флаг гостевого режима
    user_data['guest_mode'] = True
    save_user_data(context, user_id)

    text = ("Вы в режиме гостя!\n"
            "- В данном режиме ваши данные не сохраняются.\n"
            "- ИИ работает в ограниченном режиме\n"
            "- Доступ к ISS отсутствует\n\n"
            "Доступные команды:\n"
            "/about - Описание бота\n"
            "/commands - Список всех команд\n"
            "/signup - Создание профиля\n\n"
            "Вы можете ознакомиться с функциями системы и общением с ИИ, затем при желании создать учетную запись ISS через команду /signup")

    keyboard = [
        [InlineKeyboardButton("Начать", callback_data='guest_start')],
        [InlineKeyboardButton("Назад", callback_data='guest_back')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, reply_markup=reply_markup)


async def handle_guest_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка callback'ов гостевого режима"""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id

    # Load user data from persistent storage
    load_user_data(context, user_id)

    user_data = context.user_data
    data = query.data

    if data == 'guest_start':
        # Начать гостевой режим - показать доступные команды
        text = ("Гостевой режим активирован!\n\n"
                "Теперь вы можете использовать:\n"
                "/about - Описание бота\n"
                "/commands - Список всех команд\n\n"
                "Для создания профиля ISS используйте /signup")

        keyboard = [
            [InlineKeyboardButton("Показать команды", callback_data='guest_commands')],
            [InlineKeyboardButton("Создать профиль", callback_data='guest_signup')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup)

    elif data == 'guest_back':
        # Вернуться к /start
        from Commands.start import start_command
        await start_command(update, context)

    elif data == 'guest_commands':
        # Показать список команд
        from Commands.commands import commands_command
        await commands_command(update, context)

    elif data == 'guest_signup':
        # Начать регистрацию - перейти к /start
        from Commands.start import start_command
        # Создам временный update для start_command
        class TempUpdate:
            def __init__(self, original_update):
                self.callback_query = None
                self.message = original_update.callback_query.message
                self.effective_user = original_update.effective_user
                self.effective_chat = original_update.effective_chat

        temp_update = TempUpdate(update)
        await start_command(temp_update, context)


def is_guest_mode(user_data):
    """Проверка, находится ли пользователь в гостевом режиме"""
    return user_data.get('guest_mode', False)


async def guest_restricted_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сообщение для ограниченного доступа в гостевом режиме"""
    text = ("Чтобы воспользоваться данной командой требуется учетная запись ISS и регистрация профиля.\n"
            "Сейчас вы в гостевом режиме.")

    keyboard = [
        [InlineKeyboardButton("Создать профиль ISS", callback_data='guest_signup')],
        [InlineKeyboardButton("Назад", callback_data='guest_back')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, reply_markup=reply_markup)


async def handle_guest_command(update: Update, context: ContextTypes.DEFAULT_TYPE, command_name: str):
    """Обработка команд в гостевом режиме"""
    user_data = context.user_data
    
    # Разрешенные команды в гостевом режиме
    allowed_commands = ['/about', '/commands', '/signup', '/start', '/guest']
    
    if f'/{command_name}' in allowed_commands:
        # Разрешить команду
        return False  # False значит продолжить обработку обычным образом
    else:
        # Запретить команду и показать сообщение
        await guest_restricted_message(update, context)
        return True  # True значит остановить дальнейшую обработку