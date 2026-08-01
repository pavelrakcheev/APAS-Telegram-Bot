from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, InputFile
import os
from telegram.ext import ContextTypes
from shared import load_user_data, save_user_data
from Commands.guest import is_guest_mode, guest_restricted_message
from Models.gemini import generate_gemini_response, get_available_gemini_models
from Models.groq import generate_groq_response, get_available_groq_models
from Models.yandex import generate_yandex_response, get_available_yandex_models

# Available models - combine all providers
MODELS = {}
MODELS.update(get_available_groq_models())
MODELS.update(get_available_gemini_models())
MODELS.update(get_available_yandex_models())

# Default model
DEFAULT_MODEL = 'groq_gpt_oss_120b'

def get_category_image(category):
    """Get image path for category"""
    image_map = {
        'groq_openai': 'Models/src/openai.png',
        'groq_moonshot': 'Models/src/moonshot.png',
        'groq_qwen': 'Models/src/qwen.png',
        'groq_llama3': 'Models/src/meta.png',
        'groq_llama4': 'Models/src/meta.png',
        'gemini_2_0': 'Models/src/google.png',
        'gemini_2_5': 'Models/src/google.png',
        'yandex_4': 'Models/src/YandexGPT 4.png',
        'yandex_5': 'Models/src/YandexGPT 5.png'
    }
    return image_map.get(category)

async def models_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /models - выбор модели ИИ"""
    user_id = update.effective_user.id
    user_data = load_user_data(context, user_id)

    if is_guest_mode(user_data):
        await guest_restricted_message(update, context)
        return

    # Get current model
    current_model_key = user_data.get('selected_model', DEFAULT_MODEL)
    current_model = MODELS.get(current_model_key, MODELS[DEFAULT_MODEL])

    text = f"🤖 Выберите провайдера генеративных моделей:\n\nСейчас используется: **{current_model['name']}**"

    keyboard = [
        [InlineKeyboardButton("🚀 Groq", callback_data='models_provider_groq')],
        [InlineKeyboardButton("🤖 Google (Gemini)", callback_data='models_provider_google')],
        [InlineKeyboardButton("🇷🇺 ЯндексGPT", callback_data='models_provider_yandex')],
        [InlineKeyboardButton("❌ Закрыть", callback_data='models_close')]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_models_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка callback'ов выбора модели"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    user_data = load_user_data(context, user_id)
    data = query.data

    # Get current model for display
    current_model_key = user_data.get('selected_model', DEFAULT_MODEL)
    current_model = MODELS.get(current_model_key, MODELS[DEFAULT_MODEL])

    if data == 'models_provider_groq':
        # Show Groq categories
        text = f"🚀 Выберите категорию моделей Groq:\n\nСейчас используется: **{current_model['name']}**"
        keyboard = [
            [InlineKeyboardButton("🤖 OpenAI", callback_data='models_category_groq_openai')],
            [InlineKeyboardButton("🌙 Moonshot AI", callback_data='models_category_groq_moonshot')],
            [InlineKeyboardButton("🧠 Qwen", callback_data='models_category_groq_qwen')],
            [InlineKeyboardButton("🦙 Meta Llama 3", callback_data='models_category_groq_llama3')],
            [InlineKeyboardButton("🦙 Meta Llama 4", callback_data='models_category_groq_llama4')],
            [InlineKeyboardButton("⬅️ Назад", callback_data='models_back_to_providers')],
            [InlineKeyboardButton("❌ Закрыть", callback_data='models_close')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        # Check if current message has photo (coming back from category with image)
        if hasattr(query.message, 'photo') and query.message.photo:
            # Delete photo message and send text message
            await query.delete_message()
            await query.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    elif data == 'models_provider_google':
        # Show Google/Gemini categories
        text = f"🤖 Выберите категорию моделей Google Gemini:\n\nСейчас используется: **{current_model['name']}**"
        keyboard = [
            [InlineKeyboardButton("2.0 Flash", callback_data='models_category_gemini_2_0')],
            [InlineKeyboardButton("2.5 Flash/Pro", callback_data='models_category_gemini_2_5')],
            [InlineKeyboardButton("⬅️ Назад", callback_data='models_back_to_providers')],
            [InlineKeyboardButton("❌ Закрыть", callback_data='models_close')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        # Check if current message has photo (coming back from category with image)
        if hasattr(query.message, 'photo') and query.message.photo:
            # Delete photo message and send text message
            await query.delete_message()
            await query.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    elif data == 'models_provider_yandex':
        # Show YandexGPT categories
        text = f"🇷🇺 Выберите поколение моделей YandexGPT:\n\nСейчас используется: **{current_model['name']}**"
        keyboard = [
            [InlineKeyboardButton("4️⃣ YandexGPT 4", callback_data='models_category_yandex_4')],
            [InlineKeyboardButton("5️⃣ YandexGPT 5", callback_data='models_category_yandex_5')],
            [InlineKeyboardButton("⬅️ Назад", callback_data='models_back_to_providers')],
            [InlineKeyboardButton("❌ Закрыть", callback_data='models_close')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        # Check if current message has photo (coming back from category with image)
        if hasattr(query.message, 'photo') and query.message.photo:
            # Delete photo message and send text message
            await query.delete_message()
            await query.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    elif data.startswith('models_category_'):
        # Show models in selected category
        category = data.replace('models_category_', '')
        category_models = {k: v for k, v in MODELS.items() if v.get('category') == category}

        if not category_models:
            await query.answer("❌ Модели в этой категории не найдены")
            return

        # Get category display name
        category_names = {
            'groq_openai': '🤖 Groq - OpenAI модели',
            'groq_moonshot': '🌙 Groq - Moonshot AI модели',
            'groq_qwen': '🧠 Groq - Qwen модели',
            'groq_llama3': '🦙 Groq - Meta Llama 3 модели',
            'groq_llama4': '🦙 Groq - Meta Llama 4 модели',
            'gemini_2_0': '🤖 Gemini 2.0',
            'gemini_2_5': '🤖 Gemini 2.5',
            'yandex_4': '🇷🇺 YandexGPT 4',
            'yandex_5': '🇷🇺 YandexGPT 5'
        }
        category_name = category_names.get(category, f'Категория: {category}')

        text = f"{category_name}\n\nСейчас используется: **{current_model['name']}**\n\nВыберите модель:"

        keyboard = []
        for model_key, model_info in category_models.items():
            status = " ✅" if model_key == current_model_key else ""
            keyboard.append([
                InlineKeyboardButton(
                    f"{model_info['name']}{status}",
                    callback_data=f'model_select_{model_key}'
                )
            ])

        # Add back button
        if category.startswith('groq'):
            back_callback = 'models_provider_groq'
        elif category.startswith('gemini'):
            back_callback = 'models_provider_google'
        elif category.startswith('yandex'):
            back_callback = 'models_provider_yandex'
        else:
            back_callback = 'models_back_to_providers'
        keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data=back_callback)])
        keyboard.append([InlineKeyboardButton("❌ Закрыть", callback_data='models_close')])

        reply_markup = InlineKeyboardMarkup(keyboard)

        # Check if we have an image for this category
        image_path = get_category_image(category)
        if image_path and os.path.exists(image_path):
            # Delete the current message and send a new one with image
            await query.delete_message()
            with open(image_path, 'rb') as photo:
                await query.message.reply_photo(
                    photo=photo,
                    caption=text,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
        else:
            # No image, just edit the message
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    elif data == 'models_back_to_providers':
        # Back to provider selection
        text = f"🤖 Выберите провайдера генеративных моделей:\n\nСейчас используется: **{current_model['name']}**"
        keyboard = [
            [InlineKeyboardButton("🚀 Groq", callback_data='models_provider_groq')],
            [InlineKeyboardButton("🤖 Google (Gemini)", callback_data='models_provider_google')],
            [InlineKeyboardButton("🇷🇺 ЯндексGPT", callback_data='models_provider_yandex')],
            [InlineKeyboardButton("❌ Закрыть", callback_data='models_close')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    elif data.startswith('model_select_'):
        model_key = data.replace('model_select_', '')
        if model_key in MODELS:
            # Update user's selected model
            user_data['selected_model'] = model_key
            save_user_data(context, user_id)

            model_info = MODELS[model_key]
            text = f"✅ Модель изменена на: **{model_info['name']}**\n\n{model_info['description']}"

            # Return to provider selection
            keyboard = [
                [InlineKeyboardButton("🚀 Groq", callback_data='models_provider_groq')],
                [InlineKeyboardButton("🤖 Google (Gemini)", callback_data='models_provider_google')],
                [InlineKeyboardButton("🇷🇺 ЯндексGPT", callback_data='models_provider_yandex')],
                [InlineKeyboardButton("❌ Закрыть", callback_data='models_close')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            # Check if current message has photo (coming from category with image)
            if hasattr(query.message, 'photo') and query.message.photo:
                # Delete photo message and send text message
                await query.delete_message()
                await query.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
            else:
                await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await query.answer("❌ Модель не найдена")

    elif data == 'models_close':
        await query.delete_message()

def get_user_model(user_data):
    """Get the model configuration for a user"""
    model_key = user_data.get('selected_model', DEFAULT_MODEL)
    return MODELS.get(model_key, MODELS[DEFAULT_MODEL])

async def generate_ai_response(user_data, system_prompt, user_message, streaming_enabled=True):
    """Generate AI response using the user's selected model"""
    model_config = get_user_model(user_data)

    try:
        if model_config['provider'] == 'groq':
            return await generate_groq_response(model_config, system_prompt, user_message, streaming_enabled)
        elif model_config['provider'] == 'gemini':
            return await generate_gemini_response(model_config, system_prompt, user_message)
        elif model_config['provider'] == 'yandex':
            return await generate_yandex_response(model_config, system_prompt, user_message)
        else:
            raise Exception(f"Unknown provider: {model_config['provider']}")
    except Exception as e:
        raise Exception(f"Error with {model_config['name']}: {str(e)}")