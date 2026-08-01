import os
import json
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

# File to store reports
REPORTS_FILE = 'data/reports.json'

def load_reports():
    """Load reports from file"""
    if os.path.exists(REPORTS_FILE):
        try:
            with open(REPORTS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def save_reports(reports):
    """Save reports to file"""
    try:
        with open(REPORTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(reports, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error(f"Error saving reports: {e}")

async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /report command"""
    user_id = update.effective_user.id

    # Load user data from persistent storage
    from shared import load_user_data
    load_user_data(context, user_id)

    user_data = context.user_data

    # Check if user is in guest mode
    from Commands.guest import is_guest_mode, guest_restricted_message
    if is_guest_mode(user_data):
        await guest_restricted_message(update, context)
        return

    text = """Ой, а что случилось? Давайте разберемся с этим!

Выберите категорию:"""

    keyboard = [
        [InlineKeyboardButton("Генерация текста", callback_data='report_text_generation')],
        [InlineKeyboardButton("Профиль", callback_data='report_profile')],
        [InlineKeyboardButton("Arc Maps", callback_data='report_arc_maps')],
        [InlineKeyboardButton("Arc Weather", callback_data='report_arc_weather')],
        [InlineKeyboardButton("Другое", callback_data='report_other')],
        [InlineKeyboardButton("Отмена", callback_data='report_cancel')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(text, reply_markup=reply_markup)

async def handle_report_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle report callback queries"""
    query = update.callback_query
    await query.answer()

    data = query.data
    user_id = query.from_user.id
    user_data = context.user_data

    if data == 'report_cancel':
        await query.edit_message_text("Отчет отменен.")
        return

    elif data == 'report_text_generation':
        text = "Выберите тип проблемы с генерацией текста:"
        keyboard = [
            [InlineKeyboardButton("Скорость ответов", callback_data='report_issue_text_speed')],
            [InlineKeyboardButton("Качество ответов", callback_data='report_issue_text_quality')],
            [InlineKeyboardButton("Неверная информация", callback_data='report_issue_text_wrong_info')],
            [InlineKeyboardButton("Описать проблему", callback_data='report_issue_text_describe')],
            [InlineKeyboardButton("Назад", callback_data='report_back_main')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup)

    elif data == 'report_profile':
        text = "Выберите тип проблемы с профилем:"
        keyboard = [
            [InlineKeyboardButton("Удалить аккаунт", callback_data='report_issue_profile_delete')],
            [InlineKeyboardButton("Описать проблему", callback_data='report_issue_profile_describe')],
            [InlineKeyboardButton("Назад", callback_data='report_back_main')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup)

    elif data == 'report_arc_maps':
        text = "Выберите тип проблемы с Arc Maps:"
        keyboard = [
            [InlineKeyboardButton("Проблема с местоположением", callback_data='report_issue_maps_location')],
            [InlineKeyboardButton("Неверные места рядом", callback_data='report_issue_maps_places')],
            [InlineKeyboardButton("Долгая загрузка", callback_data='report_issue_maps_loading')],
            [InlineKeyboardButton("Описать проблему", callback_data='report_issue_maps_describe')],
            [InlineKeyboardButton("Назад", callback_data='report_back_main')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup)

    elif data == 'report_arc_weather':
        text = "Выберите тип проблемы с Arc Weather:"
        keyboard = [
            [InlineKeyboardButton("Неверная погода", callback_data='report_issue_weather_wrong')],
            [InlineKeyboardButton("Описать проблему", callback_data='report_issue_weather_describe')],
            [InlineKeyboardButton("Назад", callback_data='report_back_main')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup)

    elif data == 'report_other':
        user_data['report_category'] = 'other'
        user_data['report_issue'] = 'Описать проблему'
        user_data['report_step'] = 'describe'
        text = """Опишите вашу проблему подробно.

📝 Описание:"""
        await query.edit_message_text(text)

    elif data == 'report_send':
        # Send report with description
        category = user_data.get('report_category', 'other')
        issue = user_data.get('report_issue', 'Описание проблемы')
        description = user_data.get('report_description', '')
        
        await save_report(update, context, category, issue, description)
        
        # Clear report state
        user_data.pop('report_step', None)
        user_data.pop('report_category', None)
        user_data.pop('report_issue', None)
        user_data.pop('report_description', None)
        
        await query.edit_message_text("Спасибо за отчет! Мы рассмотрим вашу проблему и свяжемся с вами при необходимости.")

    elif data == 'report_back_main':
        text = """Ой, а что случилось? Давайте разберемся с этим!

Выберите категорию:"""
        keyboard = [
            [InlineKeyboardButton("Генерация текста", callback_data='report_text_generation')],
            [InlineKeyboardButton("Профиль", callback_data='report_profile')],
            [InlineKeyboardButton("Arc Maps", callback_data='report_arc_maps')],
            [InlineKeyboardButton("Arc Weather", callback_data='report_arc_weather')],
            [InlineKeyboardButton("Другое", callback_data='report_other')],
            [InlineKeyboardButton("Отмена", callback_data='report_cancel')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup)

    elif data.startswith('report_issue_'):
        # Handle specific issue selection
        issue_type = data.replace('report_issue_', '')

        # Map issue types to categories and descriptions
        issue_mapping = {
            'text_speed': ('text_generation', 'Скорость ответов'),
            'text_quality': ('text_generation', 'Качество ответов'),
            'text_wrong_info': ('text_generation', 'Неверная информация'),
            'text_describe': ('text_generation', 'Описать проблему'),
            'profile_delete': ('profile', 'Удалить аккаунт'),
            'profile_describe': ('profile', 'Описать проблему'),
            'maps_location': ('arc_maps', 'Проблема с местоположением'),
            'maps_places': ('arc_maps', 'Неверные места рядом'),
            'maps_loading': ('arc_maps', 'Долгая загрузка'),
            'maps_describe': ('arc_maps', 'Описать проблему'),
            'weather_wrong': ('arc_weather', 'Неверная погода'),
            'weather_describe': ('arc_weather', 'Описать проблему')
        }

        if issue_type in issue_mapping:
            category, description = issue_mapping[issue_type]
            user_data['report_category'] = category
            user_data['report_issue'] = description

            if 'describe' in issue_type:
                # Need user to describe the problem
                user_data['report_step'] = 'describe'
                text = f"""Опишите проблему более подробно. Вы можете оставить описание пустым, нажав на кнопку "Отправить".

📝 Описание:"""
                keyboard = [[InlineKeyboardButton("📤 Отправить отчет", callback_data='report_send_empty')]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(text, reply_markup=reply_markup)
            else:
                # Predefined issue - save report immediately
                await save_report(update, context, category, description, "")
                text = f"Спасибо за отчет! Мы рассмотрим проблему с {description.lower()} и свяжемся с вами при необходимости."
                await query.edit_message_text(text)

async def save_report(update: Update, context: ContextTypes.DEFAULT_TYPE, category, issue, description):
    """Save a report to the reports file"""
    user = update.effective_user
    user_id = user.id
    username = user.username or "No username"
    first_name = user.first_name or ""
    last_name = user.last_name or ""
    full_name = f"{first_name} {last_name}".strip()

    report = {
        'user_id': user_id,
        'username': username,
        'full_name': full_name,
        'category': category,
        'issue': issue,
        'description': description,
        'timestamp': datetime.now().isoformat(),
        'status': 'new'
    }

    reports = load_reports()
    reports.append(report)
    save_reports(reports)

    # Send notification to admin
    try:
        admin_id = 349746155  # @rakcheev_me
        admin_text = f"""🆘 Новый отчет о проблеме!

👤 Пользователь: {full_name} (@{username})
🆔 ID: {user_id}
📂 Категория: {category}
❗ Проблема: {issue}
📝 Описание: {description if description else 'Не указано'}
⏰ Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""

        # Create inline keyboard for admin actions
        keyboard = [
            [InlineKeyboardButton("🏷️ Пометить", callback_data=f'admin_report_mark_{user_id}_{report["timestamp"]}')],
            [InlineKeyboardButton("💬 Написать пользователю", url=f"tg://user?id={user_id}")],
            [InlineKeyboardButton("🙈 Скрыть", callback_data=f'admin_report_hide_{user_id}_{report["timestamp"]}')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await context.bot.send_message(chat_id=admin_id, text=admin_text, reply_markup=reply_markup)
    except Exception as e:
        logging.error(f"Failed to send admin notification: {e}")

async def handle_report_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages when user is describing a problem"""
    user_id = update.effective_user.id
    user_data = context.user_data

    if user_data.get('report_step') == 'describe':
        category = user_data.get('report_category', 'other')
        issue = user_data.get('report_issue', 'Описание проблемы')

        description = update.message.text
        user_data['report_description'] = description

        # Show send button
        keyboard = [[InlineKeyboardButton("📤 Отправить отчет", callback_data='report_send')]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            f"Вы описали проблему: \"{description}\"\n\nНажмите кнопку ниже, чтобы отправить отчет.",
            reply_markup=reply_markup
        )