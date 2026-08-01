from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from shared import load_user_data
import datetime
import json
import os

POINTS_TRANSACTIONS_FILE = 'data/points_transactions.json'

def load_points_transactions():
    """Load points transactions from file"""
    if os.path.exists(POINTS_TRANSACTIONS_FILE):
        try:
            with open(POINTS_TRANSACTIONS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_points_transactions(transactions):
    """Save points transactions to file"""
    try:
        with open(POINTS_TRANSACTIONS_FILE, 'w', encoding='utf-8') as f:
            json.dump(transactions, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving points transactions: {e}")

async def show_points_history(query, context, user_data, page=None):
    """
    Show points history with pagination
    """
    user_id_str = str(query.from_user.id)
    
    # Load transactions from separate file
    transactions = load_points_transactions()
    history = transactions.get(user_id_str, [])
    history.sort(key=lambda x: x['timestamp'], reverse=True)  # Newest first
    
    if page is None:
        page = context.user_data.get('points_history_page', 0)
    
    per_page = 5
    total_pages = (len(history) + per_page - 1) // per_page
    
    if page >= total_pages:
        page = max(0, total_pages - 1)
    context.user_data['points_history_page'] = page
    
    start_idx = page * per_page
    end_idx = min(start_idx + per_page, len(history))
    current_history = history[start_idx:end_idx]
    
    text = "📊 История накоплений\n\n"
    
    if not history:
        text += "Здесь сейчас пусто :("
    else:
        for i, entry in enumerate(current_history, 1):
            dt = datetime.datetime.fromtimestamp(entry['timestamp'])
            day_name = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'][dt.weekday()]
            month_name = ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек'][dt.month - 1]
            date_str = f"{day_name}, {month_name}, {dt.day}"
            
            admin_name = entry.get('admin_name', 'Admin')
            admin_username = entry.get('admin_username', 'admin')
            amount = entry['amount']
            
            text += f"{i + start_idx}. {date_str}\n{admin_name}, @{admin_username}\n+{amount} Points\n\n"
    
    keyboard = []
    
    # Navigation buttons if more than one page
    if total_pages > 1:
        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton("⬅️", callback_data='points_history_prev'))
        
        if page < total_pages - 1:
            nav_buttons.append(InlineKeyboardButton("➡️", callback_data='points_history_next'))
        
        if nav_buttons:
            keyboard.append(nav_buttons)
    
    keyboard.append([
        InlineKeyboardButton("🔄 Обновить", callback_data='points_history_refresh'),
        InlineKeyboardButton("🔙 Назад к баллам", callback_data='back_to_points')
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    try:
        await query.edit_message_text(text, reply_markup=reply_markup)
    except Exception as e:
        # Ignore "Message is not modified" errors
        if "not modified" not in str(e).lower():
            raise


async def points_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Команда /points - показывает информацию о баллах пользователя
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

    # Get points (from user_data, default 0)
    points = user_data.get('points', 0)

    text = (f"🏆 Ваши баллы в системе ISS\n\n"
            f"💰 Текущий баланс: {points} Points\n\n"
            f"💡 Баллы можно заработать, активно используя систему ISS и выполняя различные задания.")

    keyboard = [
        [InlineKeyboardButton("💰 Заработать больше", callback_data='earn_more_points')],
        [InlineKeyboardButton("📊 История накоплений", callback_data='points_history')]
    ]

    # Only add "Back to profile" button if user came from profile
    if user_data.get('came_from_profile', False):
        keyboard.append([InlineKeyboardButton("🔙 Вернуться к профилю", callback_data='back_to_profile')])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, reply_markup=reply_markup)


async def handle_points_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает callback-запросы для баллов
    """
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    
    # Load user data
    load_user_data(context, user_id)
    
    user_data = context.user_data
    data = query.data

    if data == 'points_main':
        # Show main points menu
        user_data = context.user_data
        points = user_data.get('points', 0)

        text = (f"🏆 Ваши баллы в системе ISS\n\n"
                f"💰 Текущий баланс: {points} Points\n\n"
                f"💡 Баллы можно заработать, активно используя систему ISS и выполняя различные задания.")

        keyboard = [
            [InlineKeyboardButton("💰 Заработать больше", callback_data='earn_more_points')],
            [InlineKeyboardButton("📊 История накоплений", callback_data='points_history')]
        ]

        # Only add "Back to profile" button if user came from profile
        if user_data.get('came_from_profile', False):
            keyboard.append([InlineKeyboardButton("🔙 Вернуться к профилю", callback_data='back_to_profile')])

        reply_markup = InlineKeyboardMarkup(keyboard)
        try:
            await query.edit_message_text(text, reply_markup=reply_markup)
        except Exception as e:
            # Ignore "Message is not modified" errors
            if "not modified" not in str(e).lower():
                raise

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
        try:
            await query.edit_message_text(text, reply_markup=reply_markup)
        except Exception as e:
            # Ignore "Message is not modified" errors
            if "not modified" not in str(e).lower():
                raise

    elif data == 'points_history':
        # Show points history with pagination
        await show_points_history(query, context, user_data)

    elif data == 'points_history_prev':
        page = context.user_data.get('points_history_page', 0)
        page = max(0, page - 1)
        await show_points_history(query, context, user_data, page)

    elif data == 'points_history_next':
        user_id_str = str(update.effective_user.id)
        transactions = load_points_transactions()
        history = transactions.get(user_id_str, [])
        per_page = 5
        total_pages = (len(history) + per_page - 1) // per_page
        page = context.user_data.get('points_history_page', 0)
        page = min(total_pages - 1, page + 1)
        await show_points_history(query, context, user_data, page)

    elif data == 'points_history_refresh':
        # Refresh history - just reload the same page
        await show_points_history(query, context, user_data)

    elif data == 'back_to_points':
        # Return to points view
        user_data = context.user_data
        points = user_data.get('points', 0)

        text = (f"🏆 Ваши баллы в системе ISS\n\n"
                f"💰 Текущий баланс: {points} Points\n\n"
                f"💡 Баллы можно заработать, активно используя систему ISS и выполняя различные задания.")

        keyboard = [
            [InlineKeyboardButton("💰 Заработать больше", callback_data='earn_more_points')],
            [InlineKeyboardButton("📊 История накоплений", callback_data='points_history')]
        ]

        # Only add "Back to profile" button if user came from profile
        if user_data.get('came_from_profile', False):
            keyboard.append([InlineKeyboardButton("🔙 Вернуться к профилю", callback_data='back_to_profile')])

        reply_markup = InlineKeyboardMarkup(keyboard)
        try:
            await query.edit_message_text(text, reply_markup=reply_markup)
        except Exception as e:
            # Ignore "Message is not modified" errors
            if "not modified" not in str(e).lower():
                raise