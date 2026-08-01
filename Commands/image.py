import os
import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, InputFile
from telegram.ext import ContextTypes
from shared import load_user_data, save_user_data
from Commands.guest import is_guest_mode, guest_restricted_message
from PIL import Image
from io import BytesIO
import vertexai
from vertexai.preview.vision_models import ImageGenerationModel
from src.config import GOOGLE_CLOUD_PROJECT, GOOGLE_CLOUD_LOCATION

# Initialize Vertex AI lazily
vertexai_initialized = False

def initialize_vertexai():
    """Initialize Vertex AI if not already initialized"""
    global vertexai_initialized
    if not vertexai_initialized:
        # For Vertex AI, we need project_id and location
        # These should be set in environment variables or config
        project_id = GOOGLE_CLOUD_PROJECT
        location = GOOGLE_CLOUD_LOCATION

        if project_id == 'your-project-id':
            raise Exception("Google Cloud Project не настроен. Для генерации изображений настройте Vertex AI: https://cloud.google.com/vertex-ai/docs/generative-ai/image/generate-images")

        vertexai.init(project=project_id, location=location)
        vertexai_initialized = True

async def image_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /image - генерация изображений"""
    user_id = update.effective_user.id
    user_data = load_user_data(context, user_id)

    if is_guest_mode(user_data):
        await guest_restricted_message(update, context)
        return

    text = "Создавайте изображения с помощью генеративных ИИ. Выберите с помощью какой модели вы хотите создать изображение:"

    keyboard = [
        [InlineKeyboardButton("Vertex AI", callback_data='image_model_vertexai')],
        [InlineKeyboardButton("❌ Закрыть", callback_data='image_close')]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, reply_markup=reply_markup)

async def handle_image_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка callback'ов генерации изображений"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    user_data = load_user_data(context, user_id)
    data = query.data

    if data == 'image_model_vertexai':
        # Показать сообщение о недоступности
        text = "В данный момент эта функция недоступна."
        keyboard = [
            [InlineKeyboardButton("Причина", callback_data='image_reason')],
            [InlineKeyboardButton("Попробовать отправить запрос", callback_data='image_try_request')],
            [InlineKeyboardButton("⬅️ Назад", callback_data='image_back_to_providers')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup)

    elif data == 'image_reason':
        # Показать информацию о причине
        text = """Vertex AI API
Добавлено в APAS 23.10.2025
Последнее изменение в работе Vertex AI: 23.10.2025 в 18:27 (МСК)

Причина заморозки функции: Не подтвержен биллинговый аккаунт Google Cloud Console"""
        keyboard = [
            [InlineKeyboardButton("⬅️ Назад", callback_data='image_model_vertexai')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup)

    elif data == 'image_try_request':
        # Попытаться выполнить генерацию (как будто биллинг работает)
        text = "Опишите картинку которую вы хотите создать:"
        keyboard = [
            [InlineKeyboardButton("⬅️ Назад", callback_data='image_back')],
            [InlineKeyboardButton("❌ Отмена", callback_data='image_cancel')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup)

        # Установить состояние ожидания описания
        user_data['image_generation_step'] = 'waiting_description'
        save_user_data(context, user_id)

    elif data == 'image_close':
        await query.delete_message()

        # Очистить состояние
        if 'image_generation_step' in user_data:
            del user_data['image_generation_step']
            save_user_data(context, user_id)

    elif data == 'image_like':
        text = "Рад, что вам понравилось! 🎨"
        await query.edit_message_caption(text)

        # Очистить состояние
        if 'image_generation_step' in user_data:
            del user_data['image_generation_step']
            save_user_data(context, user_id)

    elif data == 'image_dislike':
        text = "Жаль, что не понравилось. Попробуйте описать по-другому! 📝"
        await query.edit_message_caption(text)

        # Очистить состояние
        if 'image_generation_step' in user_data:
            del user_data['image_generation_step']
            save_user_data(context, user_id)

    elif data == 'image_back_to_providers':
        # Вернуться к выбору провайдера
        text = "Создавайте изображения с помощью генеративных ИИ. Выберите с помощью какой модели вы хотите создать изображение:"
        keyboard = [
            [InlineKeyboardButton("Vertex AI", callback_data='image_model_vertexai')],
            [InlineKeyboardButton("❌ Закрыть", callback_data='image_close')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup)

    elif data == 'image_back':
        # Вернуться к выбору провайдера (то же, что и image_back_to_providers)
        text = "Создавайте изображения с помощью генеративных ИИ. Выберите с помощью какой модели вы хотите создать изображение:"
        keyboard = [
            [InlineKeyboardButton("Vertex AI", callback_data='image_model_vertexai')],
            [InlineKeyboardButton("❌ Закрыть", callback_data='image_close')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup)

    elif data == 'image_cancel':
        await query.delete_message()

        # Очистить состояние
        if 'image_generation_step' in user_data:
            del user_data['image_generation_step']
            save_user_data(context, user_id)

async def handle_image_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка сообщений с описанием картинки"""
    user_id = update.effective_user.id
    user_data = load_user_data(context, user_id)

    # Проверить, что пользователь в режиме генерации изображений
    if user_data.get('image_generation_step') != 'waiting_description':
        return False  # Не обрабатывать это сообщение

    prompt = update.message.text

    # Сохранить запрос пользователя
    user_data['last_image_prompt'] = prompt

    # Показать статус генерации
    status_message = await update.message.reply_text("Генерация изображения. Ожидание того стоит...")

    try:
        # Генерировать изображение
        image_data = await generate_image(prompt)

        # Отправить изображение
        await status_message.delete()  # Удалить статус

        text = f"Ура! Все готово. Как вам результат?\n\nВаш запрос: {prompt}"

        keyboard = [
            [InlineKeyboardButton("Нравится! 👍", callback_data='image_like')],
            [InlineKeyboardButton("Не нравится 👎", callback_data='image_dislike')],
            [InlineKeyboardButton("Редактировать ✏️", callback_data='image_edit')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Отправить изображение с подписью
        await update.message.reply_photo(
            photo=image_data,
            caption=text,
            reply_markup=reply_markup
        )

        # Очистить состояние
        user_data['image_generation_step'] = 'completed'
        save_user_data(context, user_id)

    except Exception as e:
        await status_message.edit_text(f"❌ Ошибка генерации изображения: {str(e)}")
        logging.error(f"Image generation error: {e}")

        # Очистить состояние
        if 'image_generation_step' in user_data:
            del user_data['image_generation_step']
            save_user_data(context, user_id)

async def generate_image(prompt):
    """Generate image using Vertex AI Imagen"""
    try:
        initialize_vertexai()

        model = ImageGenerationModel.from_pretrained("imagen-3.0-generate-001")

        # Generate image
        response = model.generate_images(
            prompt=prompt,
            number_of_images=1,
            aspect_ratio="1:1",
            safety_filter_level="block_some",
            person_generation="allow_adult",
        )

        # Get the first image
        if response and len(response) > 0:
            image = response[0]

            # Convert to bytes
            img_byte_arr = BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()

            return img_byte_arr
        else:
            raise Exception("No image generated")

    except Exception as e:
        error_str = str(e).lower()
        if "billing" in error_str or "bill" in error_str:
            raise Exception("Для использования Vertex AI требуется включенный биллинговый аккаунт в Google Cloud Console. Перейдите по ссылке: https://console.developers.google.com/billing/enable?project=main-byte-469713-t1")
        elif "quota" in error_str or "limit" in error_str:
            raise Exception("Превышен лимит использования Vertex AI. Попробуйте позже.")
        elif "permission" in error_str or "unauthorized" in error_str:
            raise Exception("Ошибка доступа к Vertex AI. Проверьте настройки аутентификации.")
        elif "location" in error_str or "region" in error_str:
            raise Exception("Vertex AI недоступен в вашем регионе. Попробуйте изменить регион в настройках.")
        else:
            raise Exception(f"Ошибка генерации изображения: {str(e)}")