import os
import json
from datetime import datetime
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from shared import check_admin_access

# Admin user ID
ADMIN_ID = 349746155  # @rakcheev_me

# File to store reports
REPORTS_FILE = 'data/reports.json'

# File to store archived reports
ARCHIVE_FILE = 'archive.json'

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
        print(f"Error saving reports: {e}")

def load_archive():
    """Load archived reports from file"""
    if os.path.exists(ARCHIVE_FILE):
        try:
            with open(ARCHIVE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def save_archive(archive):
    """Save archived reports to file"""
    try:
        with open(ARCHIVE_FILE, 'w', encoding='utf-8') as f:
            json.dump(archive, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving archive: {e}")

async def show_reports_page(query, reports_list, page, context, is_archive=False):
    """Show paginated reports list"""
    reports_per_page = 5
    total_pages = (len(reports_list) + reports_per_page - 1) // reports_per_page
    
    if page < 0:
        page = 0
    if page >= total_pages:
        page = total_pages - 1
    
    start_idx = page * reports_per_page
    end_idx = min(start_idx + reports_per_page, len(reports_list))
    current_reports = reports_list[start_idx:end_idx]
    
    title = "📚 Архив отчетов" if is_archive else "📋 Все отчеты"
    text = f"{title}\n\n"
    
    keyboard = []
    
    for i, report in enumerate(current_reports, 1):
        timestamp = datetime.fromisoformat(report['timestamp'])
        time_str = timestamp.strftime('%d.%m %H:%M')
        
        # Show detailed info for each report
        category_display = {
            'text_generation': '💬 Генерация текста',
            'profile': '👤 Профиль',
            'arc_maps': '🗺️ Arc Maps',
            'arc_weather': '🌤️ Arc Weather',
            'other': '❓ Другое'
        }.get(report.get('category', 'other'), '❓ Другое')
        
        status_emoji = {
            'new': '🆕',
            'in_progress': '⏳',
            'resolved': '✅',
            'rejected': '❌'
        }.get(report.get('status'), '❓')
        
        text += f"{i}. {status_emoji} **{category_display}**\n"
        text += f"   📝 {report.get('issue', 'Не указано')}\n"
        text += f"   👤 {report['full_name']} (@{report['username']})\n"
        text += f"   ⏰ {time_str}\n\n"
        
        # Add button for this report
        timestamp_str = datetime.fromisoformat(report['timestamp']).strftime('%Y%m%d%H%M%S')
        callback_prefix = 'archive_detail' if is_archive else 'report_detail'
        keyboard.append([InlineKeyboardButton(
            f"📋 {i}. {report['full_name'][:15]}...",
            callback_data=f'{callback_prefix}_{report["user_id"]}_{timestamp_str}_all'
        )])
    
    # Navigation buttons
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f'page_{page-1}'))
    
    # Page indicator
    nav_buttons.append(InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data='page_current'))
    
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton("Вперед ➡️", callback_data=f'page_{page+1}'))
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    # Back button
    back_callback = 'reports_actions' if is_archive else 'reports_main'
    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data=back_callback)])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    # Store current page and data
    context.user_data['current_page'] = page
    context.user_data['viewing_archive'] = is_archive

async def reports_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /reports command - admin only"""
    user_id = update.effective_user.id

    # Load user data from persistent storage
    from shared import load_user_data
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

    reports = load_reports()

    if not reports:
        await update.message.reply_text("📋 Нет новых отчетов о проблемах.")
        return

    # Group reports by status
    new_reports = [r for r in reports if r.get('status') == 'new']
    in_progress_reports = [r for r in reports if r.get('status') == 'in_progress']
    resolved_reports = [r for r in reports if r.get('status') == 'resolved']
    rejected_reports = [r for r in reports if r.get('status') == 'rejected']

    text = f"""📊 **Панель управления отчетами**

📋 Всего отчетов: {len(reports)}
🆕 Новые: {len(new_reports)}
⏳ В работе: {len(in_progress_reports)}
✅ Решено: {len(resolved_reports)}
❌ Отклонено: {len(rejected_reports)}

Выберите действие:"""

    keyboard = [
        [InlineKeyboardButton("📋 Все отчеты", callback_data='reports_all')],
        [InlineKeyboardButton("📂 Категории", callback_data='reports_categories')],
        [InlineKeyboardButton("⚡ Действия", callback_data='reports_actions')],
        [InlineKeyboardButton("❌ Закрыть", callback_data='reports_close')]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_reports_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle reports callback queries - admin only"""
    query = update.callback_query
    user_id = query.from_user.id

    # Check admin access first
    if not check_admin_access(user_id):
        await query.answer("❌ Нет доступа")
        return

    # Check if bot is in guest mode
    from Commands.guest import is_guest_mode
    if is_guest_mode():
        await query.answer("❌ Бот в гостевом режиме")
        return

    await query.answer()
    data = query.data
    reports = load_reports()

    # print(f"DEBUG: Received callback data: {data}")  # Debug log

    # Actions menu handlers
    if data == 'reports_delete_all':
        if not reports:
            await query.edit_message_text("❌ Нет отчетов для удаления.")
            return
        # Clear all reports
        save_reports([])
        await query.edit_message_text("✅ Все отчеты успешно удалены.")
        return
    
    elif data == 'reports_archive_all':
        if not reports:
            await query.edit_message_text("❌ Нет отчетов для переноса в архив.")
            return
        # Move all reports to archive
        archive = load_archive()
        archive.extend(reports)
        save_archive(archive)
        save_reports([])
        await query.edit_message_text(f"✅ {len(reports)} отчетов перенесено в архив.")
        return
    
    elif data == 'reports_show_archive':
        archive = load_archive()
        if not archive:
            await query.edit_message_text("📚 Архив пуст.")
            return
        # Show archive with pagination
        context.user_data['current_page'] = 0
        context.user_data['viewing_archive'] = True
        await show_reports_page(query, archive, 0, context, is_archive=True)
        return

    # Main menu actions
    if data == 'reports_all':
        if not reports:
            await query.edit_message_text("📋 Нет отчетов для просмотра.")
            return
        # Show reports with pagination
        context.user_data['current_page'] = 0
        context.user_data['viewing_archive'] = False
        await show_reports_page(query, reports, 0, context, is_archive=False)
        return
    elif data == 'reports_categories':
        text = "Выберите папку или перейдите в нужную категорию:"
        keyboard = [
            [InlineKeyboardButton("🆕 Новые", callback_data='reports_show_new')],
            [InlineKeyboardButton("⏳ В работе", callback_data='reports_show_in_progress')],
            [InlineKeyboardButton("✅ Решено", callback_data='reports_show_resolved')],
            [InlineKeyboardButton("❌ Отклонено", callback_data='reports_show_rejected')],
            [InlineKeyboardButton("📂 Выбрать категорию", callback_data='reports_select_category')],
            [InlineKeyboardButton("⬅️ Назад", callback_data='reports_main')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup)
        return
    elif data == 'reports_actions':
        text = "⚡ **Действия с отчетами**\n\nВыберите действие:"
        keyboard = [
            [InlineKeyboardButton("🗑️ Удалить все отчеты", callback_data='reports_delete_all')],
            [InlineKeyboardButton("📦 Перенести все в архив", callback_data='reports_archive_all')],
            [InlineKeyboardButton("📚 Архив отчетов", callback_data='reports_show_archive')],
            [InlineKeyboardButton("⬅️ Назад", callback_data='reports_main')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        return
    elif data == 'reports_close':
        await query.delete_message()
        return
    elif data == 'reports_main':
        # Back to main menu
        text = "📊 **Панель управления отчетами**\n\nВыберите действие:"
        keyboard = [
            [InlineKeyboardButton("📋 Все отчеты", callback_data='reports_all')],
            [InlineKeyboardButton("📂 Категории", callback_data='reports_categories')],
            [InlineKeyboardButton("⚡ Действия", callback_data='reports_actions')],
            [InlineKeyboardButton("❌ Закрыть", callback_data='reports_close')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        return
    elif data == 'reports_select_category':
        text = "Выберите категорию:"
        keyboard = [
            [InlineKeyboardButton("💬 Генерация текста", callback_data='reports_category_text_generation')],
            [InlineKeyboardButton("👤 Профиль", callback_data='reports_category_profile')],
            [InlineKeyboardButton("🗺️ Arc Maps", callback_data='reports_category_arc_maps')],
            [InlineKeyboardButton("🌤️ Arc Weather", callback_data='reports_category_arc_weather')],
            [InlineKeyboardButton("❓ Другое", callback_data='reports_category_other')],
            [InlineKeyboardButton("⬅️ Назад", callback_data='reports_categories')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup)
        return
    elif data.startswith('reports_category_'):
        category = data.replace('reports_category_', '').replace('_', ' ')
        if category == 'text generation':
            category = 'text_generation'
        elif category == 'arc maps':
            category = 'arc_maps'
        elif category == 'arc weather':
            category = 'arc_weather'
        
        filtered_reports = [r for r in reports if r.get('category') == category]
        if not filtered_reports:
            text = "Здесь пока пусто, и слава богу! 🎉"
            keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data='reports_select_category')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(text, reply_markup=reply_markup)
            return
        title = f"📂 Отчеты категории: {category.replace('_', ' ').title()}"
    elif data == 'reports_show_new':
        filtered_reports = [r for r in reports if r.get('status') == 'new']
        title = "🆕 Новые отчеты"
    elif data == 'reports_show_in_progress':
        filtered_reports = [r for r in reports if r.get('status') == 'in_progress']
        title = "⏳ Отчеты в работе"
    elif data == 'reports_show_resolved':
        filtered_reports = [r for r in reports if r.get('status') == 'resolved']
        title = "✅ Решенные отчеты"
    elif data == 'reports_show_rejected':
        filtered_reports = [r for r in reports if r.get('status') == 'rejected']
        title = "❌ Отклоненные отчеты"
    elif data == 'reports_show_all':
        filtered_reports = reports
        title = "📋 Все отчеты"
    elif data == 'reports_back':
        # Back to appropriate menu based on current filter
        current_filter = context.user_data.get('reports_filter', '')
        if current_filter.startswith('reports_category_'):
            # Came from category selection - go back to categories menu
            text = "Выберите папку или перейдите в нужную категорию:"
            keyboard = [
                [InlineKeyboardButton("🆕 Новые", callback_data='reports_show_new')],
                [InlineKeyboardButton("⏳ В работе", callback_data='reports_show_in_progress')],
                [InlineKeyboardButton("✅ Решено", callback_data='reports_show_resolved')],
                [InlineKeyboardButton("❌ Отклонено", callback_data='reports_show_rejected')],
                [InlineKeyboardButton("📂 Выбрать категорию", callback_data='reports_select_category')],
                [InlineKeyboardButton("⬅️ Назад", callback_data='reports_main')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(text, reply_markup=reply_markup)
        else:
            # Default back to main menu
            text = "📊 **Панель управления отчетами**\n\nВыберите действие:"
            keyboard = [
                [InlineKeyboardButton("📋 Все отчеты", callback_data='reports_all')],
                [InlineKeyboardButton("📂 Категории", callback_data='reports_categories')],
                [InlineKeyboardButton("⚡ Действия", callback_data='reports_actions')],
                [InlineKeyboardButton("❌ Закрыть", callback_data='reports_close')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        return
    elif data.startswith('admin_report_mark_'):
        # Show status change buttons for admin notification
        parts = data.split('_')
        if len(parts) >= 5:
            report_user_id = int(parts[3])
            timestamp_str = parts[4]
            
            reports = load_reports()
            target_report = None
            
            for report in reports:
                if (report['user_id'] == report_user_id and 
                    report['timestamp'] == timestamp_str):
                    target_report = report
                    break
            
            if target_report:
                # Show status change buttons with new text
                text = "Выберите действие:"
                keyboard = [
                    [InlineKeyboardButton("⏳ Взять в работу", callback_data=f'admin_status_{report_user_id}_{timestamp_str}_in_progress')],
                    [InlineKeyboardButton("✅ Отметить решенным", callback_data=f'admin_status_{report_user_id}_{timestamp_str}_resolved')],
                    [InlineKeyboardButton("❌ Отклонить", callback_data=f'admin_status_{report_user_id}_{timestamp_str}_rejected')],
                    [InlineKeyboardButton("⬅️ Назад", callback_data=f'admin_back_{report_user_id}_{timestamp_str}')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(text, reply_markup=reply_markup)
            else:
                await query.answer("❌ Отчет не найден")
        return
    
    elif data.startswith('admin_status_'):
        # Change status from admin notification
        parts = data.split('_')
        if len(parts) >= 5:
            report_user_id = int(parts[2])
            timestamp_str = parts[3]
            new_status = parts[4]
            
            reports = load_reports()
            for report in reports:
                if (report['user_id'] == report_user_id and 
                    report['timestamp'] == timestamp_str):
                    report['status'] = new_status
                    break
            
            save_reports(reports)
            
            status_text = {
                'in_progress': 'взята в работу',
                'resolved': 'отмечена решенной',
                'rejected': 'отклонена'
            }.get(new_status, 'обновлена')
            
            await query.edit_message_text(f"✅ Статус отчета {status_text}.")
        return
    
    elif data.startswith('admin_back_'):
        # Back to original admin notification
        parts = data.split('_')
        if len(parts) >= 4:
            report_user_id = int(parts[2])
            timestamp_str = parts[3]
            
            reports = load_reports()
            target_report = None
            
            for report in reports:
                if (report['user_id'] == report_user_id and 
                    report['timestamp'] == timestamp_str):
                    target_report = report
                    break
            
            if target_report:
                # Recreate original admin notification
                admin_text = f"""🆘 Новый отчет о проблеме!

👤 Пользователь: {target_report['full_name']} (@{target_report['username']})
🆔 ID: {target_report['user_id']}
📂 Категория: {target_report['category']}
❗ Проблема: {target_report['issue']}
📝 Описание: {target_report.get('description', 'Не указано')}
⏰ Время: {datetime.fromisoformat(target_report['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}"""

                keyboard = [
                    [InlineKeyboardButton("🏷️ Пометить", callback_data=f'admin_report_mark_{report_user_id}_{timestamp_str}')],
                    [InlineKeyboardButton("💬 Написать пользователю", url=f"tg://user?id={target_report['user_id']}")],
                    [InlineKeyboardButton("🙈 Скрыть", callback_data=f'admin_report_hide_{report_user_id}_{timestamp_str}')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(admin_text, reply_markup=reply_markup)
        return
    
    elif data.startswith('admin_report_hide_'):
        # Hide/delete admin notification message
        parts = data.split('_')
        if len(parts) >= 5:
            report_user_id = int(parts[3])
            timestamp_str = parts[4]
            
            # Just delete the message - report stays in system
            await query.delete_message()
        return
    else:
        return

    # Handle pagination
    if data.startswith('page_'):
        if data == 'page_current':
            return  # Do nothing for current page indicator
        
        try:
            new_page = int(data.split('_')[1])
        except (IndexError, ValueError):
            return
        
        is_archive = context.user_data.get('viewing_archive', False)
        reports_list = load_archive() if is_archive else load_reports()
        
        await show_reports_page(query, reports_list, new_page, context, is_archive=is_archive)
        return

    # Handle archive details
    if data.startswith('archive_detail_'):
        archive = load_archive()
        await handle_archive_detail_callback(query, data, archive, context)
        return

    if not filtered_reports:
        await query.edit_message_text(f"{title}\n\nНет отчетов в этой категории.")
        return

    # Show reports list (old logic for filtered views)
    text = f"{title}\n\n"
    keyboard = []

    for i, report in enumerate(filtered_reports[-10:], 1):  # Show last 10 reports
        timestamp = datetime.fromisoformat(report['timestamp'])
        time_str = timestamp.strftime('%d.%m %H:%M')

        status_emoji = {
            'new': '🆕',
            'in_progress': '⏳',
            'resolved': '✅',
            'rejected': '❌'
        }.get(report.get('status'), '❓')

        text += f"{i}. {status_emoji} {report['full_name']} (@{report['username']}) - {report['category']}\n"
        text += f"   ⏰ {time_str} | ❗ {report['issue']}\n\n"

        # Add button to view details - use user_id and timestamp for unique identification
        filter_code = data.replace('reports_show_', '').replace('reports_category_', '').replace('_', '')
        timestamp_str = datetime.fromisoformat(report['timestamp']).strftime('%Y%m%d%H%M%S')
        keyboard.append([InlineKeyboardButton(
            f"📋 {i}. {report['full_name'][:15]}...",
            callback_data=f'report_detail_{report["user_id"]}_{timestamp_str}_{filter_code}'
        )])

    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data='reports_back')])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup)

    # Store current filter for back navigation
    context.user_data['reports_filter'] = data

async def handle_archive_detail_callback(query, data, archive, context):
    """Handle viewing archive report details - admin only"""
    user_id = query.from_user.id

    # Check admin access first
    if not check_admin_access(user_id):
        await query.answer("❌ Нет доступа")
        return

    # Check if bot is in guest mode
    from Commands.guest import is_guest_mode
    if is_guest_mode():
        await query.answer("❌ Бот в гостевом режиме")
        return

    await query.answer()

    if data.startswith('archive_detail_'):
        # Parse report identifier
        parts = data.split('_')
        if len(parts) >= 5:
            report_user_id = int(parts[2])
            timestamp_str = parts[3]
            filter_code = '_'.join(parts[4:])  # Join remaining parts as filter_code

            target_report = None

            for report in archive:
                if (report['user_id'] == report_user_id and
                    datetime.fromisoformat(report['timestamp']).strftime("%Y%m%d%H%M%S") == timestamp_str):
                    target_report = report
                    break

            if target_report:
                timestamp = datetime.fromisoformat(target_report['timestamp'])

                status_display = {
                    'new': '🆕 Новый',
                    'in_progress': '⏳ В работе',
                    'resolved': '✅ Решен',
                    'rejected': '❌ Отклонен'
                }.get(target_report.get('status', 'new'), '🆕 Новый')

                category_display = {
                    'text_generation': '💬 Генерация текста',
                    'profile': '👤 Профиль',
                    'arc_maps': '🗺️ Arc Maps',
                    'arc_weather': '🌤️ Arc Weather',
                    'other': '❓ Другое'
                }.get(target_report.get('category', 'other'), '❓ Другое')

                text = f"""📋 **Детали отчета из архива**

📂 **Категория:** {category_display}
❗ **Проблема:** {target_report['issue']}
📝 **Описание:** {target_report.get('description', 'Не указано')}

👤 **Пользователь:**
• Имя: {target_report['full_name']}
• Username: @{target_report['username']}
• ID: {target_report['user_id']}

⏰ **Время:** {timestamp.strftime('%Y-%m-%d %H:%M:%S')}
📊 **Статус:** {status_display}"""

                # Archive actions buttons
                keyboard = [
                    [InlineKeyboardButton("💬 Написать пользователю", url=f"tg://user?id={target_report['user_id']}")],
                    [InlineKeyboardButton("⬅️ Назад к архиву", callback_data='reports_show_archive')]
                ]

                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
            else:
                await query.edit_message_text("❌ Отчет не найден в архиве.")

async def handle_report_detail_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle viewing report details - admin only"""
    query = update.callback_query
    user_id = query.from_user.id

    # Check admin access first
    if not check_admin_access(user_id):
        await query.answer("❌ Нет доступа")
        return

    # Check if bot is in guest mode
    from Commands.guest import is_guest_mode
    if is_guest_mode():
        await query.answer("❌ Бот в гостевом режиме")
        return

    await query.answer()
    data = query.data

    if data.startswith('report_detail_'):
        # Parse report identifier
        parts = data.split('_')
        if len(parts) >= 5:
            report_user_id = int(parts[2])
            timestamp_str = parts[3]
            filter_code = '_'.join(parts[4:])  # Join remaining parts as filter_code

            reports = load_reports()
            target_report = None

            for report in reports:
                if (report['user_id'] == report_user_id and
                    datetime.fromisoformat(report['timestamp']).strftime("%Y%m%d%H%M%S") == timestamp_str):
                    target_report = report
                    break

            if target_report:
                timestamp = datetime.fromisoformat(target_report['timestamp'])

                status_display = {
                    'new': '🆕 Новый',
                    'in_progress': '⏳ В работе',
                    'resolved': '✅ Решен',
                    'rejected': '❌ Отклонен'
                }.get(target_report.get('status', 'new'), '🆕 Новый')

                category_display = {
                    'text_generation': '� Генерация текста',
                    'profile': '👤 Профиль',
                    'arc_maps': '🗺️ Arc Maps',
                    'arc_weather': '🌤️ Arc Weather',
                    'other': '❓ Другое'
                }.get(target_report.get('category', 'other'), '❓ Другое')

                text = f"""📋 **Детали отчета**

📂 **Категория:** {category_display}
❗ **Проблема:** {target_report['issue']}
📝 **Описание:** {target_report.get('description', 'Не указано')}

👤 **Пользователь:**
• Имя: {target_report['full_name']}
• Username: @{target_report['username']}
• ID: {target_report['user_id']}

⏰ **Время:** {timestamp.strftime('%Y-%m-%d %H:%M:%S')}
📊 **Статус:** {status_display}"""

                # Status change buttons
                keyboard = []
                current_status = target_report.get('status', 'new')

                if current_status != 'in_progress':
                    keyboard.append([InlineKeyboardButton("⏳ Взять в работу", callback_data=f'report_status_{report_user_id}_{timestamp_str}_{filter_code.replace("_", "")}_in_progress')])
                if current_status != 'resolved':
                    keyboard.append([InlineKeyboardButton("✅ Отметить решенным", callback_data=f'report_status_{report_user_id}_{timestamp_str}_{filter_code.replace("_", "")}_resolved')])
                if current_status != 'rejected':
                    keyboard.append([InlineKeyboardButton("❌ Отклонить", callback_data=f'report_status_{report_user_id}_{timestamp_str}_{filter_code.replace("_", "")}_rejected')])

                # Action buttons
                keyboard.append([InlineKeyboardButton("💬 Написать пользователю", url=f"tg://user?id={target_report['user_id']}")])
                keyboard.append([InlineKeyboardButton("🙈 Скрыть", callback_data=f'admin_report_hide_{report_user_id}_{target_report["timestamp"]}')])

                # Map filter code back to full filter name
                filter_mapping = {
                    'new': 'reports_show_new',
                    'inprogress': 'reports_show_in_progress',
                    'resolved': 'reports_show_resolved',
                    'rejected': 'reports_show_rejected',
                    'all': 'reports_all',
                    'textgeneration': 'reports_category_text_generation',
                    'profile': 'reports_category_profile',
                    'arc_maps': 'reports_category_arc_maps',
                    'arc_weather': 'reports_category_arc_weather',
                    'other': 'reports_category_other'
                }
                current_filter = filter_mapping.get(filter_code, 'reports_all')
                keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data=current_filter)])

                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
            else:
                await query.edit_message_text("❌ Отчет не найден.")

    elif data.startswith('archive_detail_'):
        # Parse archive report identifier
        parts = data.split('_')
        if len(parts) >= 5:
            report_user_id = int(parts[2])
            timestamp_str = parts[3]
            filter_code = '_'.join(parts[4:])  # Join remaining parts as filter_code

            archive = load_archive()
            target_report = None

            for report in archive:
                if (report['user_id'] == report_user_id and
                    datetime.fromisoformat(report['timestamp']).strftime("%Y%m%d%H%M%S") == timestamp_str):
                    target_report = report
                    break

            if target_report:
                timestamp = datetime.fromisoformat(target_report['timestamp'])

                status_display = {
                    'new': '🆕 Новый',
                    'in_progress': '⏳ В работе',
                    'resolved': '✅ Решен',
                    'rejected': '❌ Отклонен'
                }.get(target_report.get('status', 'new'), '🆕 Новый')

                category_display = {
                    'text_generation': '💬 Генерация текста',
                    'profile': '👤 Профиль',
                    'arc_maps': '🗺️ Arc Maps',
                    'arc_weather': '🌤️ Arc Weather',
                    'other': '❓ Другое'
                }.get(target_report.get('category', 'other'), '❓ Другое')

                text = f"""📋 **Детали отчета из архива**

📂 **Категория:** {category_display}
❗ **Проблема:** {target_report['issue']}
📝 **Описание:** {target_report.get('description', 'Не указано')}

👤 **Пользователь:**
• Имя: {target_report['full_name']}
• Username: @{target_report['username']}
• ID: {target_report['user_id']}

⏰ **Время:** {timestamp.strftime('%Y-%m-%d %H:%M:%S')}
📊 **Статус:** {status_display}"""

                # Archive actions buttons
                keyboard = [
                    [InlineKeyboardButton("💬 Написать пользователю", url=f"tg://user?id={target_report['user_id']}")],
                    [InlineKeyboardButton("⬅️ Назад к архиву", callback_data='reports_show_archive')]
                ]

                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
            else:
                await query.edit_message_text("❌ Отчет не найден в архиве.")

    elif data.startswith('report_status_'):
        # Change report status
        parts = data.split('_')
        if len(parts) >= 6:
            report_user_id = int(parts[2])
            timestamp_str = parts[3]
            filter_code = '_'.join(parts[4:-1])  # Join parts between timestamp and status
            new_status = parts[-1]  # Last part is the status

            reports = load_reports()
            for report in reports:
                if (report['user_id'] == report_user_id and
                    datetime.fromisoformat(report['timestamp']).strftime("%Y%m%d%H%M%S") == timestamp_str):
                    report['status'] = new_status
                    break

            save_reports(reports)

            status_text = {
                'in_progress': 'взята в работу',
                'resolved': 'отмечена решенной',
                'rejected': 'отклонена'
            }.get(new_status, 'обновлена')

            await query.edit_message_text(f"✅ Статус отчета {status_text}.")

    elif data == 'reports_back':
        # Back to appropriate menu based on current filter
        current_filter = context.user_data.get('reports_filter', '')
        if current_filter.startswith('reports_category_'):
            # Came from category selection - go back to categories menu
            text = "Выберите папку или перейдите в нужную категорию:"
            keyboard = [
                [InlineKeyboardButton("🆕 Новые", callback_data='reports_show_new')],
                [InlineKeyboardButton("⏳ В работе", callback_data='reports_show_in_progress')],
                [InlineKeyboardButton("✅ Решено", callback_data='reports_show_resolved')],
                [InlineKeyboardButton("❌ Отклонено", callback_data='reports_show_rejected')],
                [InlineKeyboardButton("📂 Выбрать категорию", callback_data='reports_select_category')],
                [InlineKeyboardButton("⬅️ Назад", callback_data='reports_main')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(text, reply_markup=reply_markup)
        else:
            # Default back to main menu
            text = "📊 **Панель управления отчетами**\n\nВыберите действие:"
            keyboard = [
                [InlineKeyboardButton("📋 Все отчеты", callback_data='reports_all')],
                [InlineKeyboardButton("📂 Категории", callback_data='reports_categories')],
                [InlineKeyboardButton("⚡ Действия", callback_data='reports_actions')],
                [InlineKeyboardButton("❌ Закрыть", callback_data='reports_close')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        return