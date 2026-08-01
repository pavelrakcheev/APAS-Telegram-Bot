import logging
import asyncio
from datetime import datetime
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

async def get_weather_info(lat, lon):
    """Get weather information for coordinates"""
    # This is a mock implementation - in real app you'd call a weather API
    # For now, return static weather data
    return {
        'current_temp': 12,
        'feels_like': 10,
        'humidity': 65,
        'pressure': 745,
        'wind_speed': 3,
        'wind_direction': 'ЮВ',
        'precipitation': 10,
        'forecast': {
            'morning': {'temp': 10, 'condition': 'солнечно'},
            'day': {'temp': 15, 'condition': 'переменная облачность'},
            'evening': {'temp': 8, 'condition': 'ясно'}
        }
    }

async def handle_weather_callback(query, lat, lon):
    """Handle weather info callback"""
    # Show "Connecting to Arc Weather" message
    await query.answer("🔗 Подключение к Arc Weather...")
    await asyncio.sleep(1.0)

    try:
        weather_data = await get_weather_info(lat, lon)

        text = f"""🌤️ **Погода**

📍 Координаты: {lat:.4f}°, {lon:.4f}°

🌡️ **Текущие условия:**
• Температура: +{weather_data['current_temp']}°C
• Ощущается как: +{weather_data['feels_like']}°C
• Влажность: {weather_data['humidity']}%
• Давление: {weather_data['pressure']} мм рт.ст.
• Ветер: {weather_data['wind_speed']} м/с, {weather_data['wind_direction']}

🌧️ **Осадки:**
• Вероятность дождя: {weather_data['precipitation']}%
• Без осадков в ближайшие 3 часа

📅 **Прогноз на сегодня:**
• Утро: +{weather_data['forecast']['morning']['temp']}°C, {weather_data['forecast']['morning']['condition']}
• День: +{weather_data['forecast']['day']['temp']}°C, {weather_data['forecast']['day']['condition']}
• Вечер: +{weather_data['forecast']['evening']['temp']}°C, {weather_data['forecast']['evening']['condition']}

*Данные на {datetime.now().strftime('%H:%M %d.%m.%Y')}*"""

        keyboard = [
            [InlineKeyboardButton("🔄 Обновить", callback_data=f'weather_info_{lat:.4f}_{lon:.4f}')],
            [InlineKeyboardButton("⬅️ Назад", callback_data=f'back_to_location_{lat:.4f}_{lon:.4f}')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    except Exception as e:
        logging.error(f"Weather API error: {e}")
        text = f"""❌ **Ошибка получения погоды**

Не удалось получить данные о погоде для координат {lat:.4f}°, {lon:.4f}°.

Попробуйте позже или проверьте подключение к интернету."""

        keyboard = [
            [InlineKeyboardButton("🔄 Попробовать еще раз", callback_data=f'weather_info_{lat:.4f}_{lon:.4f}')],
            [InlineKeyboardButton("⬅️ Назад", callback_data=f'back_to_location_{lat:.4f}_{lon:.4f}')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')