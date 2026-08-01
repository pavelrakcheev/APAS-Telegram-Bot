import os
import logging
import asyncio
import json
import time
import re
from datetime import datetime
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.error import BadRequest
from telegram.ext import Application, ContextTypes, MessageHandler, filters, CommandHandler, CallbackQueryHandler
from groq import Groq
from dotenv import load_dotenv

# Import modules
from Modules.arc_maps import handle_setup_location, handle_location_message, handle_places_nearby_callback, handle_taxi_callback, handle_back_to_location_callback, handle_display_settings_callback, handle_toggle_category_callback, handle_clear_categories_callback, handle_distance_settings_callback, handle_toggle_distance_callback, handle_maps_callback
from Modules.arc_weather import handle_weather_callback

# Import shared utilities
from shared import users_data, load_user_data, save_user_data, format_registration_date, is_username_available, find_user_id_by_username, get_system_prompt

# Import command modules
from Commands.about import about_command
from Commands.iss import iss_command
from Commands.commands import commands_command
from Commands.acc_stat import acc_stat_command
from Commands.notifications import notifications_command, handle_notifications_callback
from Commands.settings import settings_command, handle_settings_callback
from Commands.createpost import createpost_command, handle_post_setup_message, handle_post_callback
from Commands.profile import profile_command, show_shared_profile, handle_profile_setup_message, handle_profile_callback
from Commands.points import points_command, handle_points_callback
from Commands.start import start_command, handle_setup_message, handle_start_callback
from Commands.report import report_command, handle_report_callback, handle_report_message
from Commands.reports import reports_command, handle_reports_callback, handle_report_detail_callback
from Commands.myreports import myreports_command, handle_myreports_callback, handle_myreports_detail_callback
from Commands.tools import tools_command, handle_tools_setup_message, handle_tools_callback
from Commands.addpoints import addpoints_command, handle_addpoints_callback, handle_addpoints_message
from Commands.guest import guest_command, handle_guest_callback, is_guest_mode, guest_restricted_message, signup_command
from Commands.games import games_command, handle_games_callback, handle_iss_play_nickname_input
from Commands.blum import blum_command, handle_blum_callback
from Commands.models import models_command, handle_models_callback, get_user_model, generate_ai_response

# Import Alice mode
from Modes.Alice.alice import alice_command, handle_alice_callback, handle_alice_message, is_alice_mode_active

# Import image generation
from Commands.image import image_command, handle_image_callback, handle_image_message

# Import remote command
from Commands.remote import remote_command

# Load configuration
from src.config import TELEGRAM_BOT_TOKEN, GROQ_API_KEY

# Initialize Groq client
client = Groq(api_key=GROQ_API_KEY)

# Chats directory
CHATS_DIR = 'Chats'

# Users data file
USERS_DATA_FILE = 'data/users_data.json'

# Ensure chats directory exists
if not os.path.exists(CHATS_DIR):
    os.makedirs(CHATS_DIR)

# Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    # await query.answer()  # Removed to prevent double answering - handlers will answer individually

    user_id = query.from_user.id
    
    # Load user data from persistent storage
    load_user_data(context, user_id)
    
    user_data = context.user_data
    data = query.data

    # print(f"DEBUG: Button callback received: {data} from user {user_id}")  # Debug log

    # Check if this is an Alice callback
    alice_callbacks = ['alice_enter', 'alice_back']
    if data in alice_callbacks:
        await handle_alice_callback(update, context)
        return

    # Check if this is a start/setup callback first
    start_callbacks = ['setup_simple', 'setup_advanced', 'guest_mode', 'notifications_all', 'notifications_updates', 
                      'notifications_changes', 'notifications_promo', 'change_age', 'report_age_issue',
                      'city_confirm', 'city_change', 'location_confirm', 'location_text', 'start_chat']
    if data in start_callbacks:
        await handle_start_callback(update, context)
        return

    if data.startswith('retry_'):
        # Get stored message
        last_message = user_data.get('last_message', '')
        if not last_message:
            await query.edit_message_text("Не удалось найти предыдущее сообщение для повтора.")
            return
            
        await query.edit_message_text("Повторная генерация ответа...")
        
        # Retry AI call using user's selected model
        try:
            ai_response = await generate_ai_response(user_data, get_system_prompt(user_data), last_message, streaming_enabled=False)
            await query.edit_message_text(ai_response)
            
        except Exception as e:
            await query.edit_message_text("Повторная попытка также не удалась. Попробуйте позже.")
            logging.error(f"Retry AI API error: {e}")
        
    elif data == 'report_error':
        text = ("Для сообщения об ошибке напишите @rakcheev_me с описанием проблемы и временем когда она произошла.")
        await query.edit_message_text(text)
        
    elif data in ['toggle_updates', 'toggle_changes', 'toggle_promo', 'toggle_all', 'toggle_streaming']:
        # Handle settings and notifications callbacks
        if data == 'toggle_streaming':
            await handle_settings_callback(update, context)
        else:
            await handle_notifications_callback(update, context)

    # Check if this is a post creation callback
    if data.startswith('post_'):
        await handle_post_callback(update, context)
        return

    # Check if this is a profile callback
    profile_callbacks = ['edit_profile', 'set_username', 'share_profile', 'delete_profile', 'confirm_delete', 'cancel_delete', 
                        'edit_name', 'edit_age', 'edit_city', 'edit_username', 'cancel_edit', 
                        'change_age_edit', 'confirm_city_edit', 'confirm_location_edit', 
                        'change_city_edit', 'change_location_edit', 'back_to_profile', 'view_points',
                        'earn_more_points', 'back_to_points']
    if data in profile_callbacks or data.startswith(('message_user_', 'add_friend_')):
        await handle_profile_callback(update, context)
        return

    # Check if this is a points callback
    points_callbacks = ['earn_more_points', 'points_history', 'back_to_points', 'points_main', 'points_history_prev', 'points_history_next', 'points_history_page']
    if data in points_callbacks:
        await handle_points_callback(update, context)
        return

    # Check if this is a maps callback
    maps_callbacks = ['places_nearby_', 'display_settings_', 'toggle_category_', 'clear_categories_', 
                     'distance_settings_', 'toggle_distance_', 'taxi_order_', 'back_to_location_']
    if any(data.startswith(prefix) for prefix in maps_callbacks):
        await handle_maps_callback(update, context)
        return

    # Check if this is a weather callback
    if data.startswith('weather_info_'):
        # Extract coordinates from callback data
        parts = data.replace('weather_info_', '').split('_')
        if len(parts) == 2:
            try:
                lat = float(parts[0])
                lon = float(parts[1])
                await handle_weather_callback(update.callback_query, lat, lon)
            except (ValueError, IndexError):
                await update.callback_query.edit_message_text("❌ Не удалось получить погоду - неверные координаты")
        else:
            await update.callback_query.edit_message_text("❌ Не удалось получить погоду - данные повреждены")
        return

    # Check if this is a report callback
    if data.startswith('report_'):
        await handle_report_callback(update, context)
        return

    # Check if this is a reports callback (admin only)
    if data.startswith('reports_') or data.startswith('admin_'):
        await handle_reports_callback(update, context)
        return

    # Check if this is a report detail callback (admin only)
    if data.startswith('report_detail_') or data.startswith('report_status_') or data.startswith('archive_detail_'):
        await handle_report_detail_callback(update, context)
        return

    # Check if this is a myreports callback (user's own reports)
    if data.startswith('myreports_') or data.startswith('myreports_detail_'):
        await handle_myreports_callback(update, context)
        return

    # Check if this is a tools callback
    if data.startswith('tools_'):
        await handle_tools_callback(update, context)
        return

    # Check if this is an addpoints callback
    if data.startswith('addpoints_'):
        await handle_addpoints_callback(update, context)
        return

    # Check if this is a guest callback
    guest_callbacks = ['guest_start', 'guest_back', 'guest_commands', 'guest_signup']
    if data in guest_callbacks:
        await handle_guest_callback(update, context)
        return

    # Check if this is a games callback
    games_callbacks = ['games_register', 'games_list', 'games_back', 'games_back_to_main', 'games_register_start', 
                      'games_nickname_1', 'games_nickname_2', 'games_nickname_3', 'games_nickname_custom',
                      'games_nickname_confirm', 'games_finish_registration', 'games_link_accounts', 
                      'games_why_link']
    if data in games_callbacks:
        await handle_games_callback(update, context)
        return

    # Check if this is a blum callback
    blum_callbacks = ['blum_about', 'blum_settings', 'blum_back', 'blum_main', 'blum_start_dialog']
    if data in blum_callbacks:
        await handle_blum_callback(update, context)
        return

    # Check if this is a models callback
    models_callbacks = ['models_close', 'models_back_to_providers']
    if (data.startswith('model_select_') or data.startswith('models_provider_') or 
        data.startswith('models_category_') or data in models_callbacks):
        await handle_models_callback(update, context)
        return

    # Check if this is an image callback
    image_callbacks = ['image_model_vertexai', 'image_reason', 'image_try_request', 'image_back_to_providers', 'image_close', 'image_like', 'image_dislike', 'image_edit', 'image_back', 'image_cancel']
    if data in image_callbacks:
        await handle_image_callback(update, context)
        return

    # Check if this is a mini app callback
    if data.startswith('mini_app_') or data.startswith('enhance_') or data.startswith('icon_'):
        # Mini app callbacks are handled by individual apps through handle_mini_app_mode
        return

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # Load user data from persistent storage
    load_user_data(context, user_id)
    
    user_message = update.message.text

    # Check if user is in setup process - redirect to setup handler
    setup_step = context.user_data.get('setup_step')
    if setup_step:
        print(f"DEBUG: Redirecting to setup handler from handle_message, step: {setup_step}")
        await handle_setup_message(update, context)
        return

    # Check for account status queries with more specific patterns
    status_keywords = [
        # Russian keywords
        'статус профиля', 'статус аккаунта', 'мой статус', 'какой статус',
        'уровень доступа', 'права доступа', 'административные права',
        'права', 'доступ', 'статус', 'права администратора',
        'админ права', 'права админа', 'уровень прав',
        'статус учетной записи', 'права учетной записи',
        # English keywords  
        'account status', 'profile status', 'my status', 'access level',
        'permissions', 'admin rights', 'administrator rights',
        'account permissions', 'user status'
    ]
    
    user_message_lower = user_message.lower()
    
    # More specific pattern matching for status queries
    is_status_query = False
    
    # Check for direct status questions
    if any(keyword in user_message_lower for keyword in status_keywords):
        # Additional checks for personal status questions
        personal_indicators = ['мой', 'у меня', 'мне', 'я', 'my', 'me', 'i have', 'what is my']
        question_words = ['какой', 'какие', 'что', 'какова', 'what', 'which', 'how', 'tell me']
        
        # If it contains status keywords, it's likely a status query
        # But we give extra weight to personal/question patterns
        has_personal = any(indicator in user_message_lower for indicator in personal_indicators)
        has_question = any(word in user_message_lower for word in question_words)
        is_direct_status = user_message_lower.strip() in ['статус', 'status', 'права', 'rights']
        
        # Trigger if: direct status word, OR has question word, OR has personal indicator, OR is a common status phrase
        if is_direct_status or has_question or has_personal or user_message_lower in ['статус аккаунта', 'account status', 'права доступа', 'access rights']:
            is_status_query = True
    
    if is_status_query:
        await acc_stat_command(update, context)
        return

    # Store last message for retry functionality
    context.user_data['last_message'] = user_message

    # Create user directory if not exists
    user_dir = os.path.join(CHATS_DIR, str(user_id))
    if not os.path.exists(user_dir):
        os.makedirs(user_dir)

    # Chat log file
    chat_file = os.path.join(user_dir, 'chat.txt')

    # Append user message to log
    with open(chat_file, 'a', encoding='utf-8') as f:
        f.write(f"User: {user_message}\n")

    # Send typing action only when streaming is disabled
    streaming_enabled = context.user_data.get('streaming_enabled', True)
    if not streaming_enabled:
        await update.effective_chat.send_action("typing")

    if streaming_enabled:
        # Send initial response message for streaming
        sent_message = await update.message.reply_text("Generating response...", reply_to_message_id=update.message.message_id)
    else:
        # Send a static message that will be replaced at the end
        sent_message = await update.message.reply_text("Generating response...", reply_to_message_id=update.message.message_id)

    ai_response = ""
    previous_response = "Generating response..."
    try:
        # Generate AI response using user's selected model
        from Commands.models import get_user_model
        model_config = get_user_model(context.user_data)
        
        async def update_message(content, prev_content, message):
            """Update message if content changed"""
            if content != prev_content:
                try:
                    await message.edit_text(content)
                except BadRequest as e:
                    error_msg = str(e).lower()
                    if "not modified" in error_msg:
                        # Ignore "message not modified" errors
                        pass
                    else:
                        # Log other BadRequest errors
                        logging.warning(f"BadRequest in edit_text: {e}")
                except Exception as e:
                    # Log unexpected errors
                    logging.warning(f"Unexpected error in edit_text: {e}")
        
        if streaming_enabled and model_config['provider'] == 'groq':
            # Streaming only for Groq
            response = await generate_ai_response(context.user_data, get_system_prompt(context.user_data), user_message, streaming_enabled=True)
            
            # Use asyncio.Queue for thread-safe communication
            import asyncio
            update_queue = asyncio.Queue()
            
            async def message_updater():
                """Async task to update message from queue"""
                nonlocal ai_response, previous_response, sent_message
                while True:
                    try:
                        content = await update_queue.get()
                        if content is None:  # Sentinel value to stop
                            break
                        if content != previous_response:
                            try:
                                await sent_message.edit_text(content)
                                previous_response = content
                            except BadRequest as e:
                                error_msg = str(e).lower()
                                if "not modified" in error_msg:
                                    pass
                                else:
                                    logging.warning(f"BadRequest in edit_text: {e}")
                            except Exception as e:
                                logging.warning(f"Unexpected error in edit_text: {e}")
                    except Exception as e:
                        logging.error(f"Message updater error: {e}")
                        break
            
            # Start the updater task
            updater_task = asyncio.create_task(message_updater())
            
            def process_stream():
                nonlocal ai_response
                try:
                    for chunk in response:
                        content = chunk.choices[0].delta.content
                        if content and content.strip():
                            ai_response += content
                            # Put update in queue (non-blocking)
                            update_queue.put_nowait(ai_response)
                except Exception as e:
                    logging.error(f"Streaming error: {e}")
                finally:
                    # Signal updater to stop
                    update_queue.put_nowait(None)
            
            # Run streaming in thread
            await asyncio.get_event_loop().run_in_executor(None, process_stream)
            
            # Wait for updater to finish
            await updater_task
        else:
            # Non-streaming response for all models
            ai_response = await generate_ai_response(context.user_data, get_system_prompt(context.user_data), user_message, streaming_enabled=False)
            await sent_message.edit_text(ai_response)

    except Exception as e:
        ai_response = "Sorry, I couldn't process your request right now."
        keyboard = [
            [InlineKeyboardButton("Попробовать еще раз", callback_data=f'retry_{user_id}_{len(user_message)}')],
            [InlineKeyboardButton("Сообщить об ошибке", callback_data='report_error')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        if ai_response != previous_response:
            try:
                await sent_message.edit_text(ai_response, reply_markup=reply_markup)
            except BadRequest as e:
                error_msg = str(e).lower()
                if "not modified" in error_msg:
                    # Ignore "message not modified" errors
                    pass
                else:
                    # Log other BadRequest errors
                    logging.warning(f"BadRequest in edit_text: {e}")
            except Exception as e:
                # Log unexpected errors
                logging.warning(f"Unexpected error in edit_text: {e}")
            else:
                # Only update if no exception
                previous_response = ai_response
        logging.error(f"AI API error: {e}")

    # If streaming was disabled, send the final response now
    if not streaming_enabled:
        # Only edit if content actually changed
        if ai_response != previous_response:
            try:
                await sent_message.edit_text(ai_response)
            except BadRequest as e:
                error_msg = str(e).lower()
                if "not modified" in error_msg:
                    # Ignore "message not modified" errors
                    pass
                else:
                    # Log other BadRequest errors
                    logging.warning(f"BadRequest in edit_text: {e}")
            except Exception as e:
                # Log unexpected errors
                logging.warning(f"Unexpected error in edit_text: {e}")
            else:
                # Only update if no exception
                previous_response = ai_response

    # Append AI response to log
    with open(chat_file, 'a', encoding='utf-8') as f:
        f.write(f"Bot: {ai_response}\n")

def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("about", about_command))
    application.add_handler(CommandHandler("iss", iss_command))
    application.add_handler(CommandHandler("settings", settings_command))
    application.add_handler(CommandHandler("notifications", notifications_command))
    application.add_handler(CommandHandler("profile", profile_command))
    application.add_handler(CommandHandler("points", points_command))
    application.add_handler(CommandHandler("createpost", createpost_command))
    application.add_handler(CommandHandler("acc_stat", acc_stat_command))
    application.add_handler(CommandHandler("commands", commands_command))
    application.add_handler(CommandHandler("report", report_command))
    application.add_handler(CommandHandler("reports", reports_command))
    application.add_handler(CommandHandler("myreports", myreports_command))
    application.add_handler(CommandHandler("tools", tools_command))
    application.add_handler(CommandHandler("addpoints", addpoints_command))
    application.add_handler(CommandHandler("guest", guest_command))
    application.add_handler(CommandHandler("signup", signup_command))
    application.add_handler(CommandHandler("games", games_command))
    application.add_handler(CommandHandler("blum", blum_command))
    application.add_handler(CommandHandler("models", models_command))
    application.add_handler(CommandHandler("remote", remote_command))
    application.add_handler(CommandHandler("alice", alice_command))
    application.add_handler(CallbackQueryHandler(button_callback))

    # Message handler - only for non-commands and when not in setup
    async def message_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        
        # Load user data from persistent storage
        load_user_data(context, user_id)
        
        user_data = context.user_data
        user_message = update.message.text
        message_text = user_message
        setup_step = user_data.get('setup_step')
        post_step = user_data.get('post_creation_step')
        
        # Also check global users_data directly as backup
        user_id_str = str(user_id)
        global_setup_step = None
        if user_id_str in users_data:
            global_setup_step = users_data[user_id_str].get('setup_step')
        
        # Use global data if context data is missing
        if not setup_step and global_setup_step:
            setup_step = global_setup_step
            user_data['setup_step'] = setup_step
        
        # Check if user is in guest mode
        if is_guest_mode(user_data):
            # In guest mode, only allow normal messages (AI chat)
            await handle_message(update, context)
            return
        
        # If user is in post creation process, handle post messages
        if post_step:
            await handle_post_setup_message(update, context)
            return
        
        # Check if user is editing profile
        profile_steps = ['edit_name', 'edit_age', 'edit_city', 'set_username', 'edit_username']
        if setup_step in profile_steps:
            await handle_profile_setup_message(update, context)
            return
        
        # If user is in setup process, handle setup messages
        if setup_step:
            await handle_setup_message(update, context)
            return
        
        # If user is not configured, redirect to setup
        if not user_data.get('setup_completed', False):
            await start_command(update, context)
            return
        
        # Check if user is describing a report issue
        if user_data.get('report_step') == 'describe':
            await handle_report_message(update, context)
            return

        # Check if user is in tools process
        if user_data.get('tools_step') == 'enter_secret_phrase':
            await handle_tools_setup_message(update, context)
            return
        
        # Check if user is in addpoints process
        if user_data.get('addpoints_selected_user') or message_text.startswith('@'):
            await handle_addpoints_message(update, context)
            return
        
        # Check if user is in ISS Play nickname input
        if user_data.get('iss_play_registration_step') == 'nickname_input':
            await handle_iss_play_nickname_input(update, context)
            return

        # Check if user is in Alice mode
        if is_alice_mode_active(user_id):
            await handle_alice_message(update, context)
            return

        # Check if user is generating an image
        if user_data.get('image_generation_step') == 'waiting_description':
            await handle_image_message(update, context)
            return

        # Normal message handling
        await handle_message(update, context)
    
    message_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), message_filter)
    application.add_handler(message_handler)

    # Location handler for setup and general messages
    async def location_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        
        # Load user data from persistent storage
        load_user_data(context, user_id)
        
        user_data = context.user_data
        setup_step = user_data.get('setup_step')
        post_step = user_data.get('post_creation_step')
        
        # If user is in post creation process, handle post location (if needed)
        if post_step:
            # For now, posts don't use location, so redirect to post setup
            await handle_post_setup_message(update, context)
            return
        
        # Check if user is editing profile location
        if setup_step in ['edit_city']:
            # Handle location for profile editing
            await handle_setup_location(update, context)
            return
        
        # If user is in setup process, handle setup location
        if setup_step:
            await handle_setup_location(update, context)
            return
        
        # If user is not configured, redirect to setup
        if not user_data.get('setup_completed', False):
            await start_command(update, context)
            return
        
        # Normal location handling
        await handle_location_message(update, context)
    
    location_handler = MessageHandler(filters.LOCATION, location_filter)
    application.add_handler(location_handler)

    # Run the bot
    application.run_polling()

if __name__ == '__main__':
    main()