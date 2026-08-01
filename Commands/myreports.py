import os
import json
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

async def myreports_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /myreports command - show user's own reports"""
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

    # Load all reports and filter by user
    all_reports = load_reports()
    user_reports = [r for r in all_reports if r.get('user_id') == user_id]

    if not user_reports:
        text = """📋 **Мои отчеты о проблемах**

У вас пока нет отправленных отчетов о проблемах.

💡 Если у вас возникли проблемы с ботом, используйте команду /report для создания отчета."""
        await update.message.reply_text(text)
        return

    # Calculate statistics
    total_reports = len(user_reports)
    resolved_reports = len([r for r in user_reports if r.get('status') == 'resolved'])
    in_progress_reports = len([r for r in user_reports if r.get('status') == 'in_progress'])
    new_reports = len([r for r in user_reports if r.get('status') == 'new'])
    rejected_reports = len([r for r in user_reports if r.get('status') == 'rejected'])

    text = f"""📋 **Мои отчеты о проблемах**

📊 **Статистика:**
• Всего отправлено: {total_reports}
• Решено: {resolved_reports}
• В работе: {in_progress_reports}
• В ожидании: {new_reports}
• Отклонено: {rejected_reports}

Выберите статус для просмотра:"""

    keyboard = []
    if new_reports > 0:
        keyboard.append([InlineKeyboardButton(f"🆕 В ожидании ({new_reports})", callback_data='myreports_show_new')])
    if in_progress_reports > 0:
        keyboard.append([InlineKeyboardButton(f"⏳ В работе ({in_progress_reports})", callback_data='myreports_show_in_progress')])
    if resolved_reports > 0:
        keyboard.append([InlineKeyboardButton(f"✅ Решенные ({resolved_reports})", callback_data='myreports_show_resolved')])
    if rejected_reports > 0:
        keyboard.append([InlineKeyboardButton(f"❌ Отклоненные ({rejected_reports})", callback_data='myreports_show_rejected')])

    keyboard.append([InlineKeyboardButton("📋 Все отчеты", callback_data='myreports_show_all')])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, reply_markup=reply_markup)

async def handle_myreports_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle myreports callback queries"""
    query = update.callback_query
    user_id = query.from_user.id

    await query.answer()
    data = query.data

    # Load user's reports
    all_reports = load_reports()
    user_reports = [r for r in all_reports if r.get('user_id') == user_id]

    if data == 'myreports_show_new':
        filtered_reports = [r for r in user_reports if r.get('status') == 'new']
        title = "🆕 Отчеты в ожидании"
    elif data == 'myreports_show_in_progress':
        filtered_reports = [r for r in user_reports if r.get('status') == 'in_progress']
        title = "⏳ Отчеты в работе"
    elif data == 'myreports_show_resolved':
        filtered_reports = [r for r in user_reports if r.get('status') == 'resolved']
        title = "✅ Решенные отчеты"
    elif data == 'myreports_show_rejected':
        filtered_reports = [r for r in user_reports if r.get('status') == 'rejected']
        title = "❌ Отклоненные отчеты"
    elif data == 'myreports_show_all':
        filtered_reports = user_reports
        title = "📋 Все мои отчеты"
    elif data == 'myreports_back':
        # Back to main myreports menu - recreate the main menu
        user_reports = [r for r in all_reports if r.get('user_id') == user_id]

        if not user_reports:
            text = """📋 **Мои отчеты о проблемах**

У вас пока нет отправленных отчетов о проблемах.

💡 Если у вас возникли проблемы с ботом, используйте команду /report для создания отчета."""
            await query.edit_message_text(text)
            return

        # Calculate statistics
        total_reports = len(user_reports)
        resolved_reports = len([r for r in user_reports if r.get('status') == 'resolved'])
        in_progress_reports = len([r for r in user_reports if r.get('status') == 'in_progress'])
        new_reports = len([r for r in user_reports if r.get('status') == 'new'])
        rejected_reports = len([r for r in user_reports if r.get('status') == 'rejected'])

        text = f"""📋 **Мои отчеты о проблемах**

📊 **Статистика:**
• Всего отправлено: {total_reports}
• Решено: {resolved_reports}
• В работе: {in_progress_reports}
• В ожидании: {new_reports}
• Отклонено: {rejected_reports}

Выберите статус для просмотра:"""

        keyboard = []
        if new_reports > 0:
            keyboard.append([InlineKeyboardButton(f"🆕 В ожидании ({new_reports})", callback_data='myreports_show_new')])
        if in_progress_reports > 0:
            keyboard.append([InlineKeyboardButton(f"⏳ В работе ({in_progress_reports})", callback_data='myreports_show_in_progress')])
        if resolved_reports > 0:
            keyboard.append([InlineKeyboardButton(f"✅ Решенные ({resolved_reports})", callback_data='myreports_show_resolved')])
        if rejected_reports > 0:
            keyboard.append([InlineKeyboardButton(f"❌ Отклоненные ({rejected_reports})", callback_data='myreports_show_rejected')])

        keyboard.append([InlineKeyboardButton("📋 Все отчеты", callback_data='myreports_show_all')])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup)
        return
    else:
        return

    if not filtered_reports:
        await query.edit_message_text(f"{title}\n\nНет отчетов в этой категории.")
        return

    # Sort reports by timestamp (newest first)
    filtered_reports.sort(key=lambda x: x.get('timestamp', ''), reverse=True)

    # Show reports list (limit to last 10)
    text = f"{title}\n\n"
    keyboard = []

    for i, report in enumerate(filtered_reports[:10], 1):
        timestamp = datetime.fromisoformat(report.get('timestamp', datetime.now().isoformat()))
        time_str = timestamp.strftime('%d.%m %H:%M')

        status_emoji = {
            'new': '🆕',
            'in_progress': '⏳',
            'resolved': '✅',
            'rejected': '❌'
        }.get(report.get('status'), '❓')

        # Truncate issue text if too long
        issue_text = report.get('issue', 'Не указано')
        if len(issue_text) > 30:
            issue_text = issue_text[:27] + "..."

        text += f"{i}. {status_emoji} {issue_text}\n"
        text += f"   📂 {report.get('category', 'Не указано')} | ⏰ {time_str}\n\n"

        # Add button to view details
        keyboard.append([InlineKeyboardButton(
            f"📋 {i}. {issue_text[:20]}...",
            callback_data=f'myreports_detail_{user_id}_{timestamp.strftime("%Y%m%d%H%M%S")}'
        )])

    if len(filtered_reports) > 10:
        text += f"⚠️ Показано 10 последних отчетов из {len(filtered_reports)}"

    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data='myreports_back')])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup)

    # Store current filter for back navigation
    context.user_data['myreports_filter'] = data

async def handle_myreports_detail_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle viewing report details for user"""
    query = update.callback_query
    user_id = query.from_user.id

    await query.answer()
    data = query.data

    if data.startswith('myreports_detail_'):
        # Parse user_id and timestamp
        parts = data.replace('myreports_detail_', '').split('_')
        if len(parts) >= 2:
            report_user_id = int(parts[0])
            timestamp_str = parts[1]

            # Load reports for the specific user
            all_reports = load_reports()
            user_reports = [r for r in all_reports if r.get('user_id') == report_user_id]

            target_report = None
            for report in user_reports:
                if datetime.fromisoformat(report.get('timestamp', '')).strftime("%Y%m%d%H%M%S") == timestamp_str:
                    target_report = report
                    break

        if target_report:
            timestamp = datetime.fromisoformat(target_report.get('timestamp', datetime.now().isoformat()))

            status_text = {
                'new': '🆕 В ожидании',
                'in_progress': '⏳ В работе',
                'resolved': '✅ Решен',
                'rejected': '❌ Отклонен'
            }.get(target_report.get('status'), '❓ Неизвестен')

            text = f"""📋 **Детали отчета**

📂 **Категория:** {target_report.get('category', 'Не указано')}
❗ **Проблема:** {target_report.get('issue', 'Не указано')}

📝 **Описание:**
{target_report.get('description', 'Не указано')}

⏰ **Отправлено:** {timestamp.strftime('%Y-%m-%d %H:%M:%S')}
📊 **Статус:** {status_text}"""

            keyboard = [[InlineKeyboardButton("⬅️ Назад к списку", callback_data=context.user_data.get('myreports_filter', 'myreports_show_all'))]]

            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(text, reply_markup=reply_markup)
        else:
            await query.edit_message_text("❌ Отчет не найден.")