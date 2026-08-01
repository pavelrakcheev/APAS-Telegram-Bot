from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from shared import load_user_data, save_user_data, check_admin_access
import subprocess
import os
import sys
import logging
import asyncio
import threading
import time


async def tools_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Команда /tools - системные инструменты для оптимизации и тестирования бота
    """
    user_id = update.effective_user.id

    # Load user data from persistent storage
    load_user_data(context, user_id)

    user_data = context.user_data

    # Check admin access first
    if not check_admin_access(user_id):
        await update.message.reply_text("❌ У вас нет доступа к этой команде.")
        return

    # Check if bot is in guest mode
    from Commands.guest import is_guest_mode, guest_restricted_message
    if is_guest_mode(user_data):
        await guest_restricted_message(update, context)
        return

    # Check if user is configured
    if not user_data.get('setup_completed', False):
        await update.message.reply_text("Сначала настройте свой профиль с помощью команды /start")
        return

    text = ("🛠️ Системные команды для оптимизации и тестирования работы бота\n\n"
            "⚠️ Внимание: данные команды могут заставить работать некоторые процессы непредсказуемо.\n"
            "Используйте только при необходимости!")

    keyboard = [
        [InlineKeyboardButton("🗂️ Очистка pycache", callback_data='tools_clear_cache')],
        [InlineKeyboardButton("⚙️ Компиляция всех файлов", callback_data='tools_compile')],
        [InlineKeyboardButton("⏹️ Остановка бота", callback_data='tools_stop')],
        [InlineKeyboardButton("❌ Отмена", callback_data='tools_cancel')]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, reply_markup=reply_markup)


async def handle_tools_setup_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает текстовые сообщения для системных команд
    """
    user_id = update.effective_user.id
    user_data = context.user_data
    user_message = update.message.text.strip()

    # Check admin access first
    if not check_admin_access(user_id):
        await update.message.reply_text("❌ У вас нет доступа к этой команде.")
        return

    # Check if bot is in guest mode
    from Commands.guest import is_guest_mode
    if is_guest_mode(user_data):
        return

    # Handle tools secret phrase
    if user_data.get('tools_step') == 'enter_secret_phrase':
        if user_message.strip().lower() == 'kronos':
            # Execute the pending tool action
            action = user_data.get('pending_tool_action')
            await execute_tool_action(update, context, action)
        else:
            await update.message.reply_text("❌ Неверная секретная фраза. Попробуйте еще раз:")

        save_user_data(context, user_id)


async def handle_tools_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает callback-запросы для системных команд
    """
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    user_data = context.user_data
    data = query.data

    # Check admin access first
    if not check_admin_access(user_id):
        await query.answer("❌ Нет доступа")
        return

    # Check if bot is in guest mode
    from Commands.guest import is_guest_mode
    if is_guest_mode(user_data):
        await query.answer("❌ Бот в гостевом режиме")
        return

    if data == 'tools_clear_cache':
        user_data['pending_tool_action'] = 'clear_cache'
        user_data['tools_step'] = 'enter_secret_phrase'

        text = "🗂️ Очистка pycache\n\nДля подтверждения введите секретную фразу:"
        await query.edit_message_text(text)
        save_user_data(context, user_id)

    elif data == 'tools_compile':
        user_data['pending_tool_action'] = 'compile'
        user_data['tools_step'] = 'enter_secret_phrase'

        text = "⚙️ Компиляция всех файлов\n\nДля подтверждения введите секретную фразу:"
        await query.edit_message_text(text)
        save_user_data(context, user_id)

    elif data == 'tools_stop':
        user_data['pending_tool_action'] = 'stop'
        user_data['tools_step'] = 'enter_secret_phrase'

        text = "⏹️ Остановка бота\n\nДля подтверждения введите секретную фразу:"
        await query.edit_message_text(text)
        save_user_data(context, user_id)

    elif data == 'tools_cancel':
        # Clear tools data
        tools_keys = [k for k in user_data.keys() if k.startswith('tools_') or k.startswith('pending_tool')]
        for key in tools_keys:
            user_data.pop(key, None)

        text = "❌ Действие отменено."
        await query.edit_message_text(text)
        save_user_data(context, user_id)


async def execute_tool_action(update: Update, context: ContextTypes.DEFAULT_TYPE, action: str):
    """
    Выполняет выбранное системное действие
    """
    user_id = update.effective_user.id
    user_data = context.user_data

    try:
        if action == 'clear_cache':
            # Clear __pycache__ directories
            result = clear_pycache()
            text = f"✅ Очистка pycache выполнена!\n{result}"

        elif action == 'compile':
            # Compile all Python files
            result = compile_all_files()
            text = f"✅ Компиляция выполнена!\n{result}"

        elif action == 'stop':
            # Stop the bot immediately
            text = "⏹️ Бот останавливается..."
            
            # Clear tools data first
            tools_keys = [k for k in user_data.keys() if k.startswith('tools_') or k.startswith('pending_tool')]
            for key in tools_keys:
                user_data.pop(key, None)
            save_user_data(context, user_id)

            # Send message
            await update.message.reply_text(text)
            
            # Log stopping process
            logging.info("Initiating bot shutdown sequence...")
            
            # Stop the application
            logging.info("Calling application.stop()...")
            context.application.stop()
            logging.info("Application.stop() called")
            
            # Start a thread to force exit after 3 seconds
            def force_exit():
                logging.info("Force exit thread started, sleeping 3 seconds...")
                time.sleep(3)
                logging.info("Force exiting process with os._exit(0)")
                os._exit(0)
            
            threading.Thread(target=force_exit, daemon=True).start()
            logging.info("Force exit thread started")

        else:
            text = "❌ Неизвестное действие"

    except Exception as e:
        text = f"❌ Ошибка выполнения: {str(e)}"
        logging.error(f"Tool action '{action}' failed: {e}")

    # Clear tools data
    tools_keys = [k for k in user_data.keys() if k.startswith('tools_') or k.startswith('pending_tool')]
    for key in tools_keys:
        user_data.pop(key, None)

    await update.message.reply_text(text)
    save_user_data(context, user_id)


def clear_pycache():
    """
    Очищает все директории __pycache__
    """
    try:
        # Get the project root directory
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        # Find and remove all __pycache__ directories
        cache_dirs = []
        for root, dirs, files in os.walk(project_root):
            if '__pycache__' in dirs:
                cache_path = os.path.join(root, '__pycache__')
                cache_dirs.append(cache_path)

        removed_count = 0
        for cache_dir in cache_dirs:
            try:
                import shutil
                shutil.rmtree(cache_dir)
                removed_count += 1
            except Exception as e:
                logging.warning(f"Failed to remove {cache_dir}: {e}")

        return f"Удалено директорий: {removed_count}"

    except Exception as e:
        return f"Ошибка: {str(e)}"


def compile_all_files():
    """
    Компилирует все Python файлы в проекте
    """
    try:
        import py_compile

        # Get the project root directory
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        # Find all Python files
        python_files = []
        for root, dirs, files in os.walk(project_root):
            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))

        compiled_count = 0
        errors = []

        for py_file in python_files:
            try:
                py_compile.compile(py_file, doraise=True)
                compiled_count += 1
            except py_compile.PyCompileError as e:
                errors.append(f"{os.path.basename(py_file)}: {e}")
            except Exception as e:
                errors.append(f"{os.path.basename(py_file)}: {str(e)}")

        result = f"Скомпилировано файлов: {compiled_count}"
        if errors:
            result += f"\nОшибки ({len(errors)}):\n" + "\n".join(errors[:5])  # Show first 5 errors
            if len(errors) > 5:
                result += f"\n... и ещё {len(errors) - 5} ошибок"

        return result

    except Exception as e:
        return f"Ошибка: {str(e)}"