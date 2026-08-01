from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from shared import load_users_data, save_users_data, load_user_data, save_user_data, reload_users_data, check_admin_access
import json
import os
from dotenv import load_dotenv

load_dotenv()

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

def get_user_selection_text_and_keyboard():
    """Generate text and keyboard for user selection"""
    # Load all users data
    users_data = load_users_data()

    # Get users with setup completed
    active_users = []
    for uid_str, user_data in users_data.items():
        if user_data.get('setup_completed', False):
            active_users.append({
                'user_id': int(uid_str),
                'name': user_data.get('name', 'Unknown'),
                'username': user_data.get('username', 'unknown'),
                'points': user_data.get('points', 0)
            })

    # Sort by points descending and take first 5
    active_users.sort(key=lambda x: x['points'], reverse=True)
    display_users = active_users[:5]

    if not display_users:
        return "❌ Нет активных пользователей для начисления баллов.", None

    text = "🏆 Выбор пользователя:\n\n"
    keyboard = []

    for i, user in enumerate(display_users, 1):
        text += f"{i}. {user['name']}, @{user['username']} ({user['points']} Points)\n"

        keyboard.append([InlineKeyboardButton(str(i), callback_data=f'addpoints_select_{user["user_id"]}')])

    text += "\nИли введите username ISS для поиска:"
    keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data='addpoints_cancel')])

    reply_markup = InlineKeyboardMarkup(keyboard)
    return text, reply_markup


async def addpoints_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Команда /addpoints - админская команда для начисления баллов пользователям
    """
    user_id = update.effective_user.id

    # Load user data from persistent storage
    load_user_data(context, user_id)

    user_data = context.user_data

    # Check if user is admin
    if not check_admin_access(user_id):
        await update.message.reply_text("❌ У вас нет доступа к этой команде.")
        return

    # Check if user is in guest mode
    from Commands.guest import is_guest_mode, guest_restricted_message
    if is_guest_mode(user_data):
        await guest_restricted_message(update, context)
        return

    text, reply_markup = get_user_selection_text_and_keyboard()
    if reply_markup is None:
        await update.message.reply_text(text)
        return

    sent_message = await update.message.reply_text(text, reply_markup=reply_markup)
    
    # Store command message info for potential deletion on cancel
    context.user_data['addpoints_command_chat_id'] = update.effective_chat.id
    context.user_data['addpoints_command_message_id'] = update.message.message_id


async def handle_addpoints_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает callback-запросы для начисления баллов
    """
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id

    # Check if user is admin
    if not check_admin_access(user_id):
        await query.answer("❌ Нет доступа")
        return

    data = query.data

    if data == 'addpoints_cancel':
        # Delete bot message
        await query.delete_message()
        
        # Delete user's command message if stored
        command_chat_id = context.user_data.get('addpoints_command_chat_id')
        command_message_id = context.user_data.get('addpoints_command_message_id')
        if command_chat_id and command_message_id:
            try:
                await context.bot.delete_message(
                    chat_id=command_chat_id,
                    message_id=command_message_id
                )
            except Exception as e:
                print(f"Failed to delete command message: {e}")
            
            # Clear stored message info
            context.user_data.pop('addpoints_command_chat_id', None)
            context.user_data.pop('addpoints_command_message_id', None)
        
        return

    elif data.startswith('addpoints_select_'):
        selected_user_id = int(data.split('_')[2])

        # Load user data
        users_data = load_users_data()
        user_data = users_data.get(str(selected_user_id))

        if not user_data:
            await query.edit_message_text("❌ Пользователь не найден.")
            return

        name = user_data.get('name', 'Unknown')
        username = user_data.get('username', 'unknown')
        points = user_data.get('points', 0)

        text = f"{name}, @{username}\n{points} Points\n\nВведите сумму начисления баллов:"

        keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data='addpoints_back')]]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup)

        # Store selected user for next step
        context.user_data['addpoints_selected_user'] = selected_user_id

    elif data == 'addpoints_back':
        # Back to user selection
        text, reply_markup = get_user_selection_text_and_keyboard()
        if reply_markup is None:
            await query.edit_message_text(text)
        else:
            await query.edit_message_text(text, reply_markup=reply_markup)

    elif data == 'addpoints_confirm':
        # This will be handled in message handler
        pass

    elif data.startswith('addpoints_notification_'):
        # Handle notification response
        action = data.split('_')[2]
        if action == 'close':
            await query.delete_message()


async def handle_addpoints_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает текстовые сообщения для начисления баллов
    """
    user_id = update.effective_user.id

    # Check if user is admin
    if not check_admin_access(user_id):
        return

    user_data = context.user_data
    message_text = update.message.text.strip()

    # Check if we're in addpoints flow
    selected_user_id = user_data.get('addpoints_selected_user')

    if selected_user_id:
        # Try to parse amount
        try:
            amount = int(message_text)
            if amount <= 0:
                await update.message.reply_text("❌ Сумма должна быть положительным числом.")
                return
        except ValueError:
            await update.message.reply_text("❌ Введите корректную сумму (целое число).")
            return

        # Load users data
        users_data = load_users_data()
        target_user_data = users_data.get(str(selected_user_id))

        if not target_user_data:
            await update.message.reply_text("❌ Пользователь не найден.")
            return

        # Add points
        current_points = target_user_data.get('points', 0)
        new_points = current_points + amount
        target_user_data['points'] = new_points

        # Add to transactions file
        import time
        transactions = load_points_transactions()
        user_id_str = str(selected_user_id)
        
        if user_id_str not in transactions:
            transactions[user_id_str] = []
        
        transaction_entry = {
            'timestamp': int(time.time()),
            'amount': amount,
            'admin_id': user_id,
            'admin_name': user_data.get('name', 'Admin'),
            'admin_username': user_data.get('username', 'admin')
        }
        transactions[user_id_str].append(transaction_entry)
        save_points_transactions(transactions)

        # Save users data
        save_users_data(users_data)
        reload_users_data()

        name = target_user_data.get('name', 'Unknown')
        username = target_user_data.get('username', 'unknown')

        # Send confirmation to admin
        text = f"Пользователю {name} успешно начислено {amount} Points"
        keyboard = [[InlineKeyboardButton("❌ Закрыть", callback_data='addpoints_cancel')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(text, reply_markup=reply_markup)

        # Send notification to user
        try:
            await context.bot.send_message(
                chat_id=selected_user_id,
                text=f"Вам начислено {amount} Points!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🏆 Перейти в Points", callback_data='points_history')],
                    [InlineKeyboardButton("❌ Закрыть", callback_data='addpoints_notification_close')]
                ])
            )
        except Exception as e:
            print(f"Failed to send notification to user {selected_user_id}: {e}")

        # Clear state
        user_data.pop('addpoints_selected_user', None)
        user_data.pop('addpoints_command_chat_id', None)
        user_data.pop('addpoints_command_message_id', None)

    elif message_text.startswith('@'):
        # Search by username
        username = message_text[1:]  # Remove @

        users_data = load_users_data()
        found_user = None

        for uid_str, u_data in users_data.items():
            if u_data.get('username') == username and u_data.get('setup_completed', False):
                found_user = {
                    'user_id': int(uid_str),
                    'name': u_data.get('name', 'Unknown'),
                    'username': username,
                    'points': u_data.get('points', 0)
                }
                break

        if found_user:
            name = found_user['name']
            username = found_user['username']
            points = found_user['points']

            text = f"{name}, @{username}\n{points} Points\n\nВведите сумму начисления баллов:"

            keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data='addpoints_back')]]

            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(text, reply_markup=reply_markup)

            # Store selected user
            user_data['addpoints_selected_user'] = found_user['user_id']
        else:
            await update.message.reply_text("❌ Пользователь с таким username не найден или не завершен setup.")