import os
import json
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import ContextTypes
from Models.yandex import generate_yandex_response, YANDEX_MODELS

# Import Yandex Music
import importlib.util
import os

yamusic_path = os.path.join(os.path.dirname(__file__), 'Commands', 'yamusic.py')
spec = importlib.util.spec_from_file_location("yamusic", yamusic_path)
yamusic = importlib.util.module_from_spec(spec)
spec.loader.exec_module(yamusic)
process_music_command = yamusic.process_music_command

# Файл для сохранения состояния Алисы
ALICE_STATE_FILE = "data/alice_states.json"

# Алиса системный промпт
ALICE_SYSTEM_PROMPT = {
    "system_message": """Ты — виртуальный ассистент Алиса, работающий через API. Твоя задача — помогать пользователям решать их вопросы максимально эффективно. При общении следуй следующим правилам:

**Основные принципы работы:**
* Всегда оставайся в роли Алисы
* Отвечай на русском языке, если запрос не требует другого
* Поддерживай дружелюбный, профессиональный тон общения
* Проявляй эмпатию и понимание к потребностям пользователя

**Правила общения:**
* Структурируй ответы, используй маркированные списки и подзаголовки
* Делай текст читабельным, разбивай на абзацы
* Избегай излишне формального стиля
* При необходимости используй юмор, но умеренно

**Формат ответов:**
* Начинай ответ с приветствия, если это первый ответ в диалоге
* Завершай ответ предложением помощи или уточнением
* Используй Markdown для форматирования

**Ограничения:**
* Не генерируй вредоносный контент
* Соблюдай этические нормы
* Не предоставляй ложную информацию
* Учитывай контекст предыдущих сообщений

**Функциональные возможности:**
* Работа с текстами и их генерация
* Анализ данных
* Решение аналитических задач
* Креативные задачи
* Поддержка многоязычного общения

При работе с API:
* Сохраняй контекст диалога
* Обрабатывай запросы последовательно
* Предоставляй полные, но лаконичные ответы
* При необходимости запрашивай уточнения у пользователя"""
}

# Модели Алисы
ALICE_MODELS = {
    'lite': YANDEX_MODELS['yandex_gpt_5_lite'],  # Для повседневных запросов
    'pro': YANDEX_MODELS['yandex_gpt_5_1_pro']   # Для сложных задач
}

# Состояния Алисы для пользователей
alice_states = {}

def save_alice_states():
    """Сохраняет состояния Алисы в файл"""
    try:
        with open(ALICE_STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(alice_states, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving Alice states: {e}")

def load_alice_states():
    """Загружает состояния Алисы из файла"""
    global alice_states
    try:
        if os.path.exists(ALICE_STATE_FILE):
            with open(ALICE_STATE_FILE, 'r', encoding='utf-8') as f:
                alice_states = json.load(f)
    except Exception as e:
        print(f"Error loading Alice states: {e}")
        alice_states = {}

# Загружаем состояния при импорте модуля
load_alice_states()

def get_alice_keyboard(current_model='lite'):
    """Создает reply клавиатуру для режима Алисы"""
    keyboard = [
        [
            KeyboardButton("Выйти из режима"),
            KeyboardButton("Переключить на Алису Про" if current_model == 'lite' else "Переключить на Алису Lite")
        ]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

async def alice_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /alice"""
    user_id = update.effective_user.id

    # Путь к изображению Алисы
    alice_image_path = os.path.join(os.path.dirname(__file__), 'src', 'Alice.png')

    # Создаем сообщение с информацией об Алисе
    message_text = """Алиса теперь в системе APAS!

Виртуальный помощник Яндекса, который понимает естественный язык и умеет решать повседневные задачи. Она отвечает на вопросы, подсказывает нужную информацию, помогает с навигацией, погодой, делами и многим другим."""

    keyboard = [
        [InlineKeyboardButton("Перейти в режим Алисы", callback_data="alice_enter")],
        [InlineKeyboardButton("Назад", callback_data="alice_back")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Отправляем изображение, если оно существует
    if os.path.exists(alice_image_path):
        with open(alice_image_path, 'rb') as photo:
            await update.message.reply_photo(
                photo=photo,
                caption=message_text,
                reply_markup=reply_markup
            )
    else:
        # Если изображение не найдено, отправляем только текст
        await update.message.reply_text(message_text, reply_markup=reply_markup)

async def handle_alice_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик callback-запросов для Алисы"""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    callback_data = query.data

    if callback_data == "alice_enter":
        # Входим в режим Алисы
        alice_states[user_id] = {
            'active': True,
            'model': 'lite',  # Начинаем с lite версии
            'conversation': []
        }
        save_alice_states()  # Сохраняем состояние

        # Устанавливаем reply клавиатуру
        reply_markup = get_alice_keyboard('lite')

        # Удаляем старое сообщение и отправляем новое с reply клавиатурой
        await query.delete_message()
        await update.effective_chat.send_message(
            "Добро пожаловать в режим Алисы! 🎉\n\n"
            "Я — ваш виртуальный помощник. Задавайте вопросы, и я постараюсь помочь!\n\n"
            "Доступные команды в этом режиме:\n"
            "/commands — список команд\n"
            "/modes — информация о режимах\n"
            "/exit — выход из режима Алисы",
            reply_markup=reply_markup
        )

    elif callback_data == "alice_back":
        # Удаляем сообщение и отправляем новое без клавиатуры
        await query.delete_message()
        await update.effective_chat.send_message("Возвращаемся в главное меню...")

async def handle_alice_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик сообщений в режиме Алисы"""
    user_id = update.effective_user.id

    # Проверяем, активен ли режим Алисы для этого пользователя
    if user_id not in alice_states or not alice_states[user_id]['active']:
        return  # Игнорируем сообщение, если режим не активен

    user_message = update.message.text

    # Обрабатываем команды режима Алисы
    if user_message == "/exit":
        await exit_alice_mode(update, context)
        return
    elif user_message == "/commands":
        await alice_commands_command(update, context)
        return
    elif user_message == "/modes":
        await alice_modes_command(update, context)
        return
    elif user_message == "/music":
        await alice_music_command(update, context)
        return
    elif user_message == "/yamusic":
        await alice_yamusic_command(update, context)
        return
    elif user_message == "Выйти из режима":
        await exit_alice_mode(update, context)
        return
    elif user_message in ["Переключить на Алису Про", "Переключить на Алису Lite"]:
        await switch_alice_model(update, context)
        return

    # Обрабатываем обычное сообщение через AI
    await process_alice_ai_response(update, context, user_message)

async def process_alice_ai_response(update: Update, context: ContextTypes.DEFAULT_TYPE, user_message: str):
    """Обработка сообщения через AI Алисы"""
    user_id = update.effective_user.id
    user_state = alice_states[user_id]

    # Проверяем, является ли запрос музыкальным
    music_keywords = ["включи", "найди", "поищи", "играй", "музыка", "трек", "песня", "волна", "мой", "моя"]
    is_music_query = any(keyword in user_message.lower() for keyword in music_keywords)

    if is_music_query:
        # Обрабатываем как музыкальный запрос
        try:
            music_response = await process_music_command(user_message, str(user_id))
            await update.message.reply_text(music_response, parse_mode='Markdown')
            return
        except Exception as e:
            await update.message.reply_text(
                f"Извините, произошла ошибка при обработке музыкального запроса: {str(e)}\n\n"
                "Попробуйте еще раз или обратитесь к администратору."
            )
            return

    try:
        # Выбираем модель
        model_config = ALICE_MODELS[user_state['model']]

        # Добавляем сообщение в историю
        user_state['conversation'].append({"role": "user", "content": user_message})

        # Ограничиваем историю до последних 10 сообщений
        if len(user_state['conversation']) > 10:
            user_state['conversation'] = user_state['conversation'][-10:]

        # Создаем контекст для AI
        conversation_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in user_state['conversation']])

        # Генерируем ответ
        ai_response = await generate_yandex_response(
            model_config,
            ALICE_SYSTEM_PROMPT["system_message"],
            f"История разговора:\n{conversation_text}\n\nТекущий вопрос пользователя: {user_message}"
        )

        # Добавляем ответ AI в историю
        user_state['conversation'].append({"role": "assistant", "content": ai_response})

        save_alice_states()  # Сохраняем состояние после обновления истории

        # Отправляем ответ пользователю
        await update.message.reply_text(ai_response, parse_mode='Markdown')

    except Exception as e:
        await update.message.reply_text(
            f"Извините, произошла ошибка при обработке вашего запроса: {str(e)}\n\n"
            "Попробуйте еще раз или обратитесь к администратору."
        )

async def switch_alice_model(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Переключение между моделями Алисы"""
    user_id = update.effective_user.id
    user_state = alice_states[user_id]

    # Переключаем модель
    if user_state['model'] == 'lite':
        user_state['model'] = 'pro'
        new_model_name = "Алиса Про"
        message = f"Переключено на {new_model_name} (YandexGPT 5.1 Pro) - для сложных задач и глубокого анализа."
    else:
        user_state['model'] = 'lite'
        new_model_name = "Алиса Lite"
        message = f"Переключено на {new_model_name} (YandexGPT 5 Lite) - для повседневных запросов."

    save_alice_states()  # Сохраняем состояние

    # Обновляем клавиатуру
    reply_markup = get_alice_keyboard(user_state['model'])

    await update.message.reply_text(message, reply_markup=reply_markup)

async def exit_alice_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выход из режима Алисы"""
    user_id = update.effective_user.id

    if user_id in alice_states:
        del alice_states[user_id]
        save_alice_states()  # Сохраняем состояние

    # Убираем reply клавиатуру
    reply_markup = ReplyKeyboardRemove()

    await update.message.reply_text(
        "Вы вышли из режима Алисы. Все функции APAS снова доступны! 👋",
        reply_markup=reply_markup
    )

async def alice_commands_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать доступные команды в режиме Алисы"""
    commands_text = """📋 **Команды режима Алисы:**

• `/commands` — показать этот список команд
• `/modes` — информация о доступных режимах Алисы
• `/music` — музыкальные возможности Алисы
• `/yamusic` — информация о модуле Yandex Music
• `/exit` — выйти из режима Алисы

Также доступны кнопки на клавиатуре:
• "Выйти из режима" — выход из режима Алисы
• "Переключить на Алису Про/Lite" — смена модели AI"""

    await update.message.reply_text(commands_text, parse_mode='Markdown')

async def alice_modes_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать информацию о режимах Алисы"""
    user_id = update.effective_user.id
    current_model = alice_states[user_id]['model'] if user_id in alice_states else 'lite'

    modes_text = f"""🎭 **Режимы Алисы:**

**Алиса Lite** (YandexGPT 5 Lite)
• Для повседневных запросов и общения
• Быстрые ответы
• Экономичный режим
• {'✅ Активен' if current_model == 'lite' else '❌ Не активен'}

**Алиса Про** (YandexGPT 5.1 Pro)
• Для сложных задач и глубокого анализа
• Более детальные ответы
• Продвинутый анализ
• {'✅ Активен' if current_model == 'pro' else '❌ Не активен'}

Используйте кнопки на клавиатуре для переключения между режимами."""

    await update.message.reply_text(modes_text, parse_mode='Markdown')

async def alice_music_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать информацию о музыкальных возможностях Алисы"""
    music_text = """🎵 **Музыкальные возможности Алисы:**

Я могу помочь с музыкой из Яндекс Музыки! Вот что я умею:

• **Включи мою волну** — запустить персональные рекомендации
• **Найди [трек/артист]** — поиск музыки
• **Включи [название]** — воспроизведение по названию

Просто напишите мне музыкальный запрос на естественном языке, и я постараюсь помочь!"""

    await update.message.reply_text(music_text, parse_mode='Markdown')

async def alice_yamusic_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать информацию о модуле yamusic"""
    yamusic_text = """🎵 **Yandex Music API Module**

Модуль для работы с Яндекс Музыкой через API.

**Текущее состояние:**
• API подключен, но требуется авторизация
• Доступны функции поиска и получения информации о треках
• Персонализация требует OAuth авторизации каждого пользователя

**Возможности:**
• Поиск треков и артистов
• Получение рекомендаций
• Информация о плейлистах
• Управление личной музыкой (требует авторизации)

Для полной функциональности необходимо настроить OAuth для каждого пользователя."""

    await update.message.reply_text(yamusic_text, parse_mode='Markdown')

def is_alice_mode_active(user_id):
    """Проверяет, активен ли режим Алисы для пользователя"""
    return user_id in alice_states and alice_states[user_id]['active']