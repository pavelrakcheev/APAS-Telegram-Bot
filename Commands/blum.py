from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from datetime import datetime
from shared import load_user_data, save_user_data
from Commands.guest import is_guest_mode, guest_restricted_message

def get_blum_greeting():
    """Get appropriate greeting based on current time"""
    hour = datetime.now().hour
    
    if 6 <= hour < 12:
        return "Доброе утро"
    elif 12 <= hour < 18:
        return "Добрый день"
    elif 18 <= hour < 22:
        return "Добрый вечер"
    else:
        return "Доброй ночи"

async def blum_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data = load_user_data(context, user_id)

    if is_guest_mode(user_data):
        await guest_restricted_message(update, context)
        return

    greeting = get_blum_greeting()
    text = (
        f"{greeting}, Я- Блюм.\n"
        "Твой персональный психолог и друг.\n\n"
        "Если хочешь, можем познакомиться поближе. Я расскажу о себе и о том как я работаю, "
        "либо же можешь пропустить знакомство и сразу приступить к разговору."
    )

    keyboard = [
        [InlineKeyboardButton("Узнать подробнее о Блюм", callback_data="blum_about")],
        [InlineKeyboardButton("Настроить Блюм под себя", callback_data="blum_settings")],
        [InlineKeyboardButton("Назад", callback_data="blum_back")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Send photo with caption
    try:
        with open('src/blum.jpg', 'rb') as photo:
            await update.message.reply_photo(photo=photo, caption=text, reply_markup=reply_markup)
    except FileNotFoundError:
        # If photo not found, send text only
        await update.message.reply_text(text, reply_markup=reply_markup)

async def handle_blum_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "blum_about":
        text = (
            "Я специально настроенная языковая модель и моя главная задача общаться с тобой на личные темы конфиденциально и без лишних вопросов.\n\n"
            "Честно говоря, я правда хочу помочь, так как моя модель и надстройка моего поведения была создана для подобного сценария.\n\n"
            "Все наши разговоры не сохраняются и твое сообщение при отправке каждый раз шифруется, чтобы анонимизировать данные на сервере, тем самым ни Павел, ни кто либо другой не может полчить доступ к нашему диалогу.\n\n"
            "Я могу хранить важные моменты или факты из нашего разговора чтобы более персонализировано давать советы и углубляться в вопросы.\n\n"
            "Надеюсь, что данное сообщение было тебе полезно. Можешь начать со мной диалог либо вернуться к прошлому сообщению."
        )
        keyboard = [
            [InlineKeyboardButton("Начать диалог", callback_data="blum_start_dialog")],
            [InlineKeyboardButton("Назад", callback_data="blum_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_caption(caption=text, reply_markup=reply_markup)
    elif query.data == "blum_start_dialog":
        # Start dialog with Blum
        text = "Отлично! Теперь мы можем начать наш разговор. Расскажи мне, что тебя беспокоит или что ты хочешь обсудить. Я здесь, чтобы помочь."
        keyboard = [[InlineKeyboardButton("Назад", callback_data="blum_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_caption(caption=text, reply_markup=reply_markup)
        # Placeholder for now
        await query.edit_message_caption(
            caption="Функция 'Настроить Блюм под себя' будет реализована в ближайшее время.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data="blum_main")]])
        )
    elif query.data == "blum_back":
        # Back to main menu
        await query.edit_message_caption(
            caption="Возвращаемся в главное меню. Используйте /start для навигации."
        )
    elif query.data == "blum_main":
        # Return to main Blum message
        greeting = get_blum_greeting()
        text = (
            f"{greeting}, Я- Блюм.\n"
            "Твой персональный психолог и друг.\n\n"
            "Если хочешь, можем познакомиться поближе. Я расскажу о себе и о том как я работаю, "
            "либо же можешь пропустить знакомство и сразу приступить к разговору."
        )
        keyboard = [
            [InlineKeyboardButton("Узнать подробнее о Блюм", callback_data="blum_about")],
            [InlineKeyboardButton("Настроить Блюм под себя", callback_data="blum_settings")],
            [InlineKeyboardButton("Назад", callback_data="blum_back")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_caption(caption=text, reply_markup=reply_markup)