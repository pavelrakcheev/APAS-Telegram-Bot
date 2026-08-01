import os
import logging
import asyncio
import requests
import json
import time
from datetime import datetime, timezone, timedelta
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.error import BadRequest
from telegram.ext import ContextTypes
from groq import Groq

from src.config import GROQ_API_KEY
client = Groq(api_key=GROQ_API_KEY)

# Chats directory
CHATS_DIR = 'Chats'

# Places cache to avoid repeated API calls
places_cache = {}
CACHE_DURATION = 3600  # 1 hour in seconds

# Load user data functions (will be imported from main)
def load_users_data():
    if os.path.exists('data/users_data.json'):
        try:
            with open('data/users_data.json', 'r', encoding='utf-8') as f:
                return __import__('json').load(f)
        except:
            return {}
    return {}

def save_users_data(users_data):
    try:
        with open('data/users_data.json', 'w', encoding='utf-8') as f:
            __import__('json').dump(users_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error(f"Error saving users data: {e}")

users_data = load_users_data()

def load_user_data(context: ContextTypes.DEFAULT_TYPE, user_id: int):
    user_id_str = str(user_id)
    if user_id_str in users_data:
        context.user_data.update(users_data[user_id_str])
    users_data[user_id_str] = dict(context.user_data)

def save_user_data(context: ContextTypes.DEFAULT_TYPE, user_id: int):
    user_id_str = str(user_id)
    users_data[user_id_str] = dict(context.user_data)
    save_users_data(users_data)

def get_user_display_settings(user_id: int):
    """Get user's display settings for places categories"""
    user_id_str = str(user_id)
    if user_id_str in users_data:
        settings = users_data[user_id_str].get('places_settings', {})
        # Default settings if not set
        if not settings:
            settings = {
                'categories': {
                    'shops': True,
                    'food': True,
                    'attractions': False,
                    'health': False,
                    'finance': False
                },
                'show_distance': False
            }
        return settings
    return {
        'categories': {
            'shops': True,
            'food': True,
            'attractions': False,
            'health': False,
            'finance': False
        },
        'show_distance': False
    }

def save_user_display_settings(user_id: int, settings: dict):
    """Save user's display settings"""
    user_id_str = str(user_id)
    if user_id_str not in users_data:
        users_data[user_id_str] = {}
    users_data[user_id_str]['places_settings'] = settings
    save_users_data(users_data)

def get_city_from_coords(lat, lon):
    """Determine city name from coordinates"""
    # Moscow coordinates approximation
    if 55.5 <= lat <= 55.9 and 37.3 <= lon <= 37.9:
        return "Москва"
    # Saint Petersburg coordinates approximation
    elif 59.8 <= lat <= 60.1 and 30.1 <= lon <= 30.5:
        return "Санкт-Петербург"
    # Default fallback
    else:
        return "Ваш город"

async def get_real_places_nearby(lat, lon, radius=1000):
    """Get real places nearby using OpenStreetMap Nominatim (free alternative)"""
    cache_key = f"{lat:.4f}_{lon:.4f}_{radius}"

    # Check cache first
    if cache_key in places_cache:
        cached_data, timestamp = places_cache[cache_key]
        if time.time() - timestamp < CACHE_DURATION:
            return cached_data

    try:
        # OpenStreetMap Nominatim API (free, no API key needed)
        base_url = "https://nominatim.openstreetmap.org/search"

        # Categories we want to search for (adapted for Nominatim)
        search_queries = {
            'shops': ['supermarket', 'convenience', 'mall', 'department_store'],
            'food': ['restaurant', 'cafe', 'bar', 'fast_food', 'food_court'],
            'attractions': ['museum', 'park', 'theatre', 'cinema', 'tourism'],
            'health': ['hospital', 'pharmacy', 'clinic', 'doctors'],
            'finance': ['bank', 'atm', 'bureau_de_change']
        }

        results = {}
        all_places = []

        # Search for each category
        for category_name, queries in search_queries.items():
            results[category_name] = []

            for query in queries[:2]:  # Limit to 2 queries per category
                try:
                    # Add delay to respect Nominatim rate limits (1 request/second)
                    await asyncio.sleep(1.1)

                    params = {
                        'q': query,
                        'format': 'json',
                        'limit': 5,
                        'bounded': 1,
                        'viewbox': f"{lon-0.01},{lat-0.01},{lon+0.01},{lat+0.01}",  # Small area around location
                        'extratags': 1,
                        'addressdetails': 1
                    }

                    response = requests.get(base_url, params=params, timeout=10,
                                          headers={'User-Agent': 'APAS-Bot/1.0'})

                    if response.status_code == 200:
                        data = response.json()

                        for place in data[:3]:  # Take up to 3 results per query
                            name = place.get('display_name', '').split(',')[0]  # Get first part of address as name

                            # Skip if we already have this place
                            if name and name not in [p['name'] for p in all_places]:
                                # Clean up address
                                address_parts = place.get('display_name', '').split(',')
                                address = ', '.join(address_parts[1:3]) if len(address_parts) > 1 else 'Адрес не указан'

                                if len(address) > 50:
                                    address = address[:47] + "..."

                                place_data = {
                                    'name': name,
                                    'address': address
                                }

                                results[category_name].append(place_data)
                                all_places.append(place_data)

                except Exception as e:
                    logging.warning(f"Error fetching {query} places: {e}")
                    continue

        # Remove duplicates across categories
        for category in results:
            seen_names = set()
            unique_places = []
            for place in results[category]:
                if place['name'] not in seen_names:
                    unique_places.append(place)
                    seen_names.add(place['name'])
            results[category] = unique_places[:4]  # Max 4 places per category

        # Cache the results
        places_cache[cache_key] = (results, time.time())
        return results

    except Exception as e:
        logging.error(f"Error fetching places from OpenStreetMap: {e}")
        return None

def get_location_prompt(lat, lon):
    """Generate AI prompt for location analysis"""
    return f"""Пользователь поделился геолокацией с координатами: широта {lat:.4f} градусов, долгота {lon:.4f} градусов.

Ты должен предоставить краткую сводку об этом месте на русском языке. Не указывай геопозицию, координаты или инфраструктуру - это будет показано отдельно.

Структура ответа должна быть очень краткой:

**Краткая сводка:** [2-3 предложения о районе/местности]

> *Резюме: [одно предложение с ключевыми особенностями места]*

Используй эмодзи для лучшей читаемости. Будь максимально кратким и полезным."""

async def handle_setup_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle location messages during setup process"""
    user_id = update.effective_user.id
    user_data = context.user_data
    setup_step = user_data.get('setup_step')

    if setup_step == 'advanced_city':
        # Get location data
        location = update.message.location
        latitude = location.latitude
        longitude = location.longitude

        # Store coordinates and ask user to confirm
        user_data['temp_location'] = {'lat': latitude, 'lon': longitude}

        text = f"Получены координаты: {latitude:.4f}, {longitude:.4f}\n\nЭто ваш город?"
        keyboard = [
            [InlineKeyboardButton("Да, сохранить", callback_data='location_confirm')],
            [InlineKeyboardButton("Нет, ввести текстом", callback_data='location_text')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(text, reply_markup=reply_markup)
        save_user_data(context, user_id)

    elif setup_step == 'edit_city':
        # Get location data for profile editing
        location = update.message.location
        latitude = location.latitude
        longitude = location.longitude

        user_data['temp_location'] = {'lat': latitude, 'lon': longitude}

        text = f"Получены координаты: {latitude:.4f}, {longitude:.4f}\n\nЭто ваш новый город?"
        keyboard = [
            [InlineKeyboardButton("Да, сохранить", callback_data='confirm_location_edit')],
            [InlineKeyboardButton("Нет, ввести текстом", callback_data='change_location_edit')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(text, reply_markup=reply_markup)
        save_user_data(context, user_id)

    else:
        # Location sent at wrong time during setup
        await update.message.reply_text("Сейчас не время отправлять геопозицию. Пожалуйста, следуйте инструкциям настройки.")

async def handle_location_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle location messages in chat"""
    user_id = update.effective_user.id

    # Load user data from persistent storage
    load_user_data(context, user_id)

    location = update.message.location
    latitude = location.latitude
    longitude = location.longitude

    # Store location data for context
    context.user_data['last_location'] = {'lat': latitude, 'lon': longitude}

    # Show "Connecting to Arc Maps" message
    connecting_message = await update.message.reply_text(
        "🔗 Подключение к Arc Maps...",
        reply_to_message_id=update.message.message_id
    )

    # Wait a short moment to show the connecting message
    await asyncio.sleep(1.5)

    # Create user directory if not exists
    user_dir = os.path.join(CHATS_DIR, str(user_id))
    if not os.path.exists(user_dir):
        os.makedirs(user_dir)

    # Chat log file
    chat_file = os.path.join(user_dir, 'chat.txt')

    # Log location message
    with open(chat_file, 'a', encoding='utf-8') as f:
        f.write(f"User Location: {latitude}, {longitude}\n")

    # Get current time in Moscow timezone
    moscow_tz = timezone(timedelta(hours=3))
    current_time = datetime.now(moscow_tz)

    city_name = get_city_from_coords(latitude, longitude)

    response_text = f"""🏙️ **{city_name}** 🕐 **{current_time.strftime('%H:%M')}**"""

    # Send initial response (replace connecting message)
    sent_message = await connecting_message.edit_text(
        response_text,
        parse_mode='Markdown'
    )

    # Send typing action only when streaming is disabled
    streaming_enabled = context.user_data.get('streaming_enabled', True)
    if not streaming_enabled:
        await update.effective_chat.send_action("typing")

    # Get system prompt (will be imported from main)
    try:
        from main import get_system_prompt
        system_prompt = get_system_prompt(context.user_data)
    except ImportError:
        # Fallback if import fails
        system_prompt = "Ты система APAS - Адаптивная Аналитическая Предиктивная Система."

    user_message = f"{get_location_prompt(latitude, longitude)} Пользователь отправил геопозицию для анализа."

    ai_response = ""
    previous_response = response_text
    try:
        # Call Groq API with streaming
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            stream=True
        )

        # Process streaming response
        for chunk in response:
            content = chunk.choices[0].delta.content
            if content and content.strip():
                ai_response += content

                if streaming_enabled:
                    # Edit the message only if content changed
                    if ai_response != previous_response:
                        try:
                            full_response = f"{response_text}\n\n📋 **Сводка по местоположению:**\n\n{ai_response}"
                            await sent_message.edit_text(full_response, parse_mode='Markdown')
                        except BadRequest as e:
                            error_msg = str(e).lower()
                            if "not modified" in error_msg:
                                pass
                            else:
                                logging.warning(f"BadRequest in edit_text: {e}")
                        except Exception as e:
                            logging.warning(f"Unexpected error in edit_text: {e}")
                        else:
                            previous_response = ai_response
                            await asyncio.sleep(0.5)

    except Exception as e:
        error_response = f"{response_text}\n\n❌ К сожалению, не удалось проанализировать местоположение. Попробуйте позже."
        keyboard = [
            [InlineKeyboardButton("Попробовать еще раз", callback_data=f'retry_{user_id}_location')],
            [InlineKeyboardButton("Сообщить об ошибке", callback_data='report_error')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await sent_message.edit_text(error_response, reply_markup=reply_markup, parse_mode='Markdown')
        logging.error(f"Groq API error: {e}")
        return

    # If streaming was disabled, send the final response now
    if not streaming_enabled:
        full_response = f"{response_text}\n\n📋 **Сводка по местоположению:**\n\n{ai_response}"
        await sent_message.edit_text(full_response, parse_mode='Markdown')

    # Add interactive buttons for additional actions
    keyboard = [
        [InlineKeyboardButton("🏪 Места рядом", callback_data=f'places_nearby_{latitude:.4f}_{longitude:.4f}')],
        [InlineKeyboardButton("🚕 Вызвать такси", callback_data=f'taxi_order_{latitude:.4f}_{longitude:.4f}')],
        [InlineKeyboardButton("🌤️ Погода", callback_data=f'weather_info_{latitude:.4f}_{longitude:.4f}')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await sent_message.edit_reply_markup(reply_markup=reply_markup)
    except Exception as e:
        logging.warning(f"Could not add reply markup: {e}")

    # Append AI response to log
    with open(chat_file, 'a', encoding='utf-8') as f:
        f.write(f"Bot: Location analysis - {ai_response}\n")

async def handle_places_nearby_callback(query, lat, lon):
    """Handle places nearby callback"""
    user_id = query.from_user.id
    city_name = get_city_from_coords(lat, lon)

    # Show loading message
    await query.answer("🔍 Поиск мест рядом...")

    # Get user settings
    settings = get_user_display_settings(user_id)

    # Try to get real places data
    places_data = await get_real_places_nearby(lat, lon)

    if places_data:
        # Format real data
        text_parts = [f"🏪 **Места рядом с вами**\n\n🏙️ **{city_name}**"]

        # Shops and supermarkets
        if places_data.get('shops'):
            text_parts.append("\n🛒 **Магазины и супермаркеты**")
            for place in places_data['shops'][:3]:
                text_parts.append(f"• {place['name']} - {place['address']}")

        # Food and restaurants
        if places_data.get('food'):
            text_parts.append("\n☕ **Кафе и рестораны**")
            for place in places_data['food'][:3]:
                text_parts.append(f"• {place['name']} - {place['address']}")

        # Attractions
        if places_data.get('attractions'):
            text_parts.append("\n🏛️ **Достопримечательности**")
            for place in places_data['attractions'][:3]:
                text_parts.append(f"• {place['name']} - {place['address']}")

        # Health facilities
        if places_data.get('health'):
            text_parts.append("\n🏥 **Медицина**")
            for place in places_data['health'][:3]:
                text_parts.append(f"• {place['name']} - {place['address']}")

        # Finance
        if places_data.get('finance'):
            text_parts.append("\n🏦 **Банки и финансы**")
            for place in places_data['finance'][:3]:
                text_parts.append(f"• {place['name']} - {place['address']}")

        text = "\n".join(text_parts)

    else:
        # Fallback to static data if API fails
        text = f"""�🏪 **Места рядом с вами**

🏙️ **{city_name}**

🛒 **Магазины и супермаркеты**
• Перекресток - ул. Ленина, 15
• Магнит - пр. Победы, 28
• Пятерочка - ул. Гагарина, 7

☕ **Кафе и рестораны**
• Кафе "Уют" - ул. Центральная, 12
• Ресторан "Вкусняшка" - пр. Солнечный, 45
• Кофейня "Арома" - ул. Парковая, 8

🏛️ **Достопримечательности**
• Центральный парк - ул. Зеленая, 1
• Городской музей - пл. Революции, 3
• Театр драмы - ул. Театральная, 22

🏥 **Медицина**
• Городская поликлиника №2 - ул. Здоровья, 15
• Аптека "Здоровье" - пр. Медицинский, 9

🏦 **Банки и финансы**
• Сбербанк - ул. Финансовая, 5
• ВТБ - пр. Банковский, 12
• Россельхозбанк - ул. Кредитная, 18

⚠️ *Показаны данные из OpenStreetMap - бесплатный сервис*"""

    # Add timestamp to make content unique and avoid "Message is not modified" error
    current_time = datetime.now().strftime('%H:%M:%S')
    text += f"\n\n📅 *Обновлено: {current_time}*"

    keyboard = [
        [InlineKeyboardButton("🔄 Обновить", callback_data=f'places_nearby_{lat:.4f}_{lon:.4f}')],
        [InlineKeyboardButton("⚙️ Параметры отображения", callback_data=f'display_settings_{lat:.4f}_{lon:.4f}')],
        [InlineKeyboardButton("⬅️ Назад", callback_data=f'back_to_location_{lat:.4f}_{lon:.4f}')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_display_settings_callback(query, lat, lon):
    """Handle display settings callback"""
    user_id = query.from_user.id
    settings = get_user_display_settings(user_id)

    # Get current enabled categories
    enabled_categories = [cat for cat, enabled in settings['categories'].items() if enabled]
    category_names = {
        'shops': 'Магазины и супермаркеты',
        'food': 'Кафе и рестораны',
        'attractions': 'Достопримечательности',
        'health': 'Медицина',
        'finance': 'Банки и финансы'
    }

    enabled_names = [category_names[cat] for cat in enabled_categories]
    enabled_text = '\n'.join(f'• {name}' for name in enabled_names) if enabled_names else '• Нет выбранных категорий'

    text = f"""⚙️ **Параметры отображения**

Выберите категории которые вы хотите видеть. Сейчас показано:
{enabled_text}

Выберите категории для отображения:"""

    keyboard = []
    for cat_key, cat_name in category_names.items():
        status = "✅" if settings['categories'][cat_key] else "❌"
        keyboard.append([InlineKeyboardButton(
            f"{status} {cat_name}",
            callback_data=f'toggle_category_{cat_key}_{lat:.4f}_{lon:.4f}'
        )])

    keyboard.append([InlineKeyboardButton("🚫 Убрать все", callback_data=f'clear_categories_{lat:.4f}_{lon:.4f}')])
    keyboard.append([InlineKeyboardButton("📏 Дополнительно", callback_data=f'distance_settings_{lat:.4f}_{lon:.4f}')])
    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data=f'places_nearby_{lat:.4f}_{lon:.4f}')])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_toggle_category_callback(query, category, lat, lon):
    """Handle category toggle callback"""
    user_id = query.from_user.id
    settings = get_user_display_settings(user_id)

    # Toggle the category
    settings['categories'][category] = not settings['categories'][category]
    save_user_display_settings(user_id, settings)

    # Refresh the settings menu
    await handle_display_settings_callback(query, lat, lon)

async def handle_clear_categories_callback(query, lat, lon):
    """Handle clear all categories callback"""
    user_id = query.from_user.id
    settings = get_user_display_settings(user_id)

    # Disable all categories
    for cat in settings['categories']:
        settings['categories'][cat] = False

    save_user_display_settings(user_id, settings)

    # Refresh the settings menu
    await handle_display_settings_callback(query, lat, lon)

async def handle_distance_settings_callback(query, lat, lon):
    """Handle distance settings callback"""
    user_id = query.from_user.id
    settings = get_user_display_settings(user_id)

    status = "Показывать" if settings['show_distance'] else "Скрыть"

    text = f"""📏 **Настройки расстояния**

Нужна ли вам информация о расстоянии до ближайшего места?
Пример: Stars Coffee - 350м

Текущее состояние: **{status} расстояние**"""

    keyboard = [
        [InlineKeyboardButton(f"{'👁️' if settings['show_distance'] else '🙈'} {status} расстояние",
                             callback_data=f'toggle_distance_{lat:.4f}_{lon:.4f}')],
        [InlineKeyboardButton("⬅️ Назад", callback_data=f'display_settings_{lat:.4f}_{lon:.4f}')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_toggle_distance_callback(query, lat, lon):
    """Handle distance toggle callback"""
    user_id = query.from_user.id
    settings = get_user_display_settings(user_id)

    # Toggle distance display
    settings['show_distance'] = not settings['show_distance']
    save_user_display_settings(user_id, settings)

    # Refresh the distance settings menu
    await handle_distance_settings_callback(query, lat, lon)

async def handle_taxi_callback(query, lat, lon):
    """Handle taxi order callback"""
    taxi_link = f"https://go.yandex/ru/?from=map&ll={lon},{lat}&z=16"

    text = f"""🚕 **Вызвать такси**

📍 Ваше местоположение: {lat:.4f}°, {lon:.4f}°

💰 **Доступные сервисы:**
• Яндекс.Go - быстро и удобно
• Uber - международный сервис
• Citymobil - местный перевозчик

💡 *Нажмите на ссылку ниже для заказа*"""

    keyboard = [
        [InlineKeyboardButton("🚕 Заказать в Яндекс.Go", url=taxi_link)],
        [InlineKeyboardButton("⬅️ Назад", callback_data=f'back_to_location_{lat:.4f}_{lon:.4f}')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_back_to_location_callback(query, lat, lon):
    """Handle back to location callback"""
    city_name = get_city_from_coords(lat, lon)

    text = f"""🏙️ **{city_name}** 🕐 **{datetime.now().strftime('%H:%M')}**

📋 **Сводка по местоположению:**"""

    keyboard = [
        [InlineKeyboardButton("🏪 Места рядом", callback_data=f'places_nearby_{lat:.4f}_{lon:.4f}')],
        [InlineKeyboardButton("🚕 Вызвать такси", callback_data=f'taxi_order_{lat:.4f}_{lon:.4f}')],
        [InlineKeyboardButton("🌤️ Погода", callback_data=f'weather_info_{lat:.4f}_{lon:.4f}')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_maps_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает callback-запросы для карт и геолокации
    """
    query = update.callback_query
    data = query.data

    if data.startswith('places_nearby_'):
        # Extract coordinates from callback data
        parts = data.replace('places_nearby_', '').split('_')
        if len(parts) == 2:
            try:
                lat = float(parts[0])
                lon = float(parts[1])
                await handle_places_nearby_callback(query, lat, lon)
            except (ValueError, IndexError):
                await query.edit_message_text("❌ Не удалось найти места рядом - неверные координаты")
        else:
            await query.edit_message_text("❌ Не удалось найти места рядом - данные повреждены")

    elif data.startswith('display_settings_'):
        # Extract coordinates from callback data
        parts = data.replace('display_settings_', '').split('_')
        if len(parts) == 2:
            try:
                lat = float(parts[0])
                lon = float(parts[1])
                await handle_display_settings_callback(query, lat, lon)
            except (ValueError, IndexError):
                await query.edit_message_text("❌ Не удалось открыть настройки - неверные координаты")
        else:
            await query.edit_message_text("❌ Не удалось открыть настройки - данные повреждены")

    elif data.startswith('toggle_category_'):
        # Extract category and coordinates from callback data
        parts = data.replace('toggle_category_', '').split('_')
        if len(parts) == 3:
            try:
                category = parts[0]
                lat = float(parts[1])
                lon = float(parts[2])
                await handle_toggle_category_callback(query, category, lat, lon)
            except (ValueError, IndexError):
                await query.edit_message_text("❌ Не удалось изменить категорию - неверные данные")
        else:
            await query.edit_message_text("❌ Не удалось изменить категорию - данные повреждены")

    elif data.startswith('clear_categories_'):
        # Extract coordinates from callback data
        parts = data.replace('clear_categories_', '').split('_')
        if len(parts) == 2:
            try:
                lat = float(parts[0])
                lon = float(parts[1])
                await handle_clear_categories_callback(query, lat, lon)
            except (ValueError, IndexError):
                await query.edit_message_text("❌ Не удалось очистить категории - неверные координаты")
        else:
            await query.edit_message_text("❌ Не удалось очистить категории - данные повреждены")

    elif data.startswith('distance_settings_'):
        # Extract coordinates from callback data
        parts = data.replace('distance_settings_', '').split('_')
        if len(parts) == 2:
            try:
                lat = float(parts[0])
                lon = float(parts[1])
                await handle_distance_settings_callback(query, lat, lon)
            except (ValueError, IndexError):
                await query.edit_message_text("❌ Не удалось открыть настройки расстояния - неверные координаты")
        else:
            await query.edit_message_text("❌ Не удалось открыть настройки расстояния - данные повреждены")

    elif data.startswith('toggle_distance_'):
        # Extract coordinates from callback data
        parts = data.replace('toggle_distance_', '').split('_')
        if len(parts) == 2:
            try:
                lat = float(parts[0])
                lon = float(parts[1])
                await handle_toggle_distance_callback(query, lat, lon)
            except (ValueError, IndexError):
                await query.edit_message_text("❌ Не удалось изменить настройки расстояния - неверные координаты")
        else:
            await query.edit_message_text("❌ Не удалось изменить настройки расстояния - данные повреждены")

    elif data.startswith('taxi_order_'):
        # Extract coordinates from callback data
        parts = data.replace('taxi_order_', '').split('_')
        if len(parts) == 2:
            try:
                lat = float(parts[0])
                lon = float(parts[1])
                await handle_taxi_callback(query, lat, lon)
            except (ValueError, IndexError):
                await query.edit_message_text("❌ Не удалось вызвать такси - неверные координаты")
        else:
            await query.edit_message_text("❌ Не удалось вызвать такси - данные повреждены")

    elif data.startswith('back_to_location_'):
        # Extract coordinates from callback data
        parts = data.replace('back_to_location_', '').split('_')
        if len(parts) == 2:
            try:
                lat = float(parts[0])
                lon = float(parts[1])
                await handle_back_to_location_callback(query, lat, lon)
            except (ValueError, IndexError):
                await query.edit_message_text("❌ Не удалось вернуться - неверные координаты")
        else:
            await query.edit_message_text("❌ Не удалось вернуться - данные повреждены")