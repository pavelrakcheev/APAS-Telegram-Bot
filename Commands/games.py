from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
import time
from shared import load_user_data, save_user_data, generate_iss_play_nicknames, iss_play_accounts, save_iss_play_accounts
from Commands.guest import is_guest_mode, guest_restricted_message

async def games_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data = load_user_data(context, user_id)

    if is_guest_mode(user_data):
        await guest_restricted_message(update, context)
        return

    text = (
        "Сможешь ли ты победить ИИ в мини играх? А вот и проверь :)\n\n"
        "Перед тем как начать, заведи свой игровой профиль ISS Play. С ним ты сможешь:\n\n"
        "- Просматривать свой профиль, очки и достижения\n"
        "- Добавлять друзей и следить за их статистикой\n"
        "- Соревноваться с друзьями и следить за рейтингом"
    )

    keyboard = [
        [InlineKeyboardButton("Зарегистрироваться в ISS Play", callback_data="games_register")],
        [InlineKeyboardButton("Какие игры есть?", callback_data="games_list")],
        [InlineKeyboardButton("Назад", callback_data="games_back")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(text, reply_markup=reply_markup)

async def handle_games_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    user_data = load_user_data(context, user_id)

    if query.data == "games_register":
        text = (
            "Отлично! Создание учетной записи происходит в несколько этапов. "
            "Ваш профиль ISS Play будет интегрирован с вашим личным аккаунтом ISS."
        )
        keyboard = [
            [InlineKeyboardButton("Начать", callback_data="games_register_start")],
            [InlineKeyboardButton("Назад", callback_data="games_back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup)
    elif query.data == "games_register_start":
        # Этап 1/3: Генерация никнеймов
        nicknames = generate_iss_play_nicknames(user_data)
        user_data['iss_play_nicknames'] = nicknames
        save_user_data(context, user_id)
        
        text = "Этап 1/3\nПридумайте себе игровой никнейм или выберите из рекомендации ИИ:"
        keyboard = [
            [InlineKeyboardButton(f"1. {nicknames[0]}", callback_data="games_nickname_1")],
            [InlineKeyboardButton(f"2. {nicknames[1]}", callback_data="games_nickname_2")],
            [InlineKeyboardButton(f"3. {nicknames[2]}", callback_data="games_nickname_3")],
            [InlineKeyboardButton("Придумать свой", callback_data="games_nickname_custom")],
            [InlineKeyboardButton("Назад", callback_data="games_register")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup)
    elif query.data == "games_nickname_custom":
        user_data['iss_play_registration_step'] = 'nickname_input'
        save_user_data(context, user_id)
        await query.edit_message_text(
            "Введите ваш игровой никнейм (только латинские буквы и цифры, минимум 5 символов):"
        )
    elif query.data in ["games_nickname_1", "games_nickname_2", "games_nickname_3"]:
        # Выбор никнейма
        idx = int(query.data.split('_')[-1]) - 1
        selected_nickname = user_data.get('iss_play_nicknames', [''])[idx]
        user_data['iss_play_selected_nickname'] = selected_nickname
        user_data['iss_play_registration_step'] = 'confirm_nickname'
        save_user_data(context, user_id)
        
        text = f"Этап 2/3\nВаш никнейм: #{selected_nickname}"
        keyboard = [
            [InlineKeyboardButton("Продолжить", callback_data="games_nickname_confirm")],
            [InlineKeyboardButton("Изменить", callback_data="games_register_start")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup)
    elif query.data == "games_nickname_confirm":
        # Этап 3/3
        nickname = user_data.get('iss_play_selected_nickname', '')
        text = f"Супер! Теперь вы #{nickname}. Готовьтесь побеждать!"
        keyboard = [
            [InlineKeyboardButton("Класс! Поехали!", callback_data="games_finish_registration")],
            [InlineKeyboardButton("Закрыть", callback_data="games_back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup)
    elif query.data == "games_finish_registration":
        # Финальное сообщение
        nickname = user_data.get('iss_play_selected_nickname', '')
        
        # Создать ISS Play аккаунт
        iss_play_accounts[str(user_id)] = {
            'nickname': nickname,
            'created_at': int(time.time()),
            'linked_to_iss': False
        }
        save_iss_play_accounts()
        
        text = (
            "Теперь у вас есть профиль ISS Play. В данный момент он не связан с вашим личным ISS аккаунтом.\n"
            "Вы можете сейчас связать оба аккаунта или сделать это позже в настройках аккаунта."
        )
        keyboard = [
            [InlineKeyboardButton("Связать сейчас", callback_data="games_link_accounts")],
            [InlineKeyboardButton("Сделаю это позже", callback_data="games_back_to_main")],
            [InlineKeyboardButton("Зачем это нужно?", callback_data="games_why_link")],
            [InlineKeyboardButton("Закрыть", callback_data="games_back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup)
    elif query.data == "games_link_accounts":
        # Связать аккаунты
        nickname = user_data.get('iss_play_selected_nickname', '')
        user_data['iss_play_linked'] = True
        user_data['iss_play_nickname'] = nickname
        save_user_data(context, user_id)
        
        # Обновить ISS Play аккаунт
        iss_play_accounts[str(user_id)]['linked_to_iss'] = True
        save_iss_play_accounts()
        
        text = f"Аккаунты успешно связаны! Ваш игровой никнейм #{nickname} теперь отображается в профиле."
        keyboard = [[InlineKeyboardButton("Отлично!", callback_data="games_back_to_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup)
    elif query.data == "games_why_link":
        text = (
            "Связывание аккаунтов позволяет:\n"
            "• Отображать игровой никнейм в вашем профиле\n"
            "• Доступ к кнопке 'Мой ISS Play' в профиле\n"
            "• Синхронизацию достижений и статистики\n"
            "• Удобный доступ к игровым функциям"
        )
        keyboard = [[InlineKeyboardButton("Понятно", callback_data="games_finish_registration")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup)
    elif query.data == "games_list":
        text = "На момент запуска сейчас доступны:\n\n1. Крестики-Нолики"
        keyboard = [[InlineKeyboardButton("Назад", callback_data="games_back_to_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup)
    elif query.data == "games_back_to_main":
        # Возврат к основному сообщению games
        text = (
            "Сможешь ли ты победить ИИ в мини играх? А вот и проверь :)\n\n"
            "Перед тем как начать, заведи свой игровой профиль ISS Play. С ним ты сможешь:\n\n"
            "- Просматривать свой профиль, очки и достижения\n"
            "- Добавлять друзей и следить за их статистикой\n"
            "- Соревноваться с друзьями и следить за рейтингом"
        )
        keyboard = [
            [InlineKeyboardButton("Зарегистрироваться в ISS Play", callback_data="games_register")],
            [InlineKeyboardButton("Какие игры есть?", callback_data="games_list")],
            [InlineKeyboardButton("Назад", callback_data="games_back")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup)
    elif query.data == "games_back":
        # Назад - возможно, к главному меню или /start
        await query.edit_message_text("Возвращаемся в главное меню. Используйте /start для навигации.")

async def handle_iss_play_nickname_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data = load_user_data(context, user_id)
    nickname = update.message.text.strip()
    
    # Validate nickname
    import re
    if not re.match(r'^[a-zA-Z0-9]{5,}$', nickname):
        await update.message.reply_text(
            "Никнейм должен содержать только латинские буквы и цифры, минимум 5 символов. Попробуйте еще раз:"
        )
        return
    
    # Check if nickname is already taken
    nickname_taken = any(acc.get('nickname') == nickname for acc in iss_play_accounts.values())
    if nickname_taken:
        await update.message.reply_text(
            "Этот никнейм уже занят. Придумайте другой:"
        )
        return
    
    # Save selected nickname
    user_data['iss_play_selected_nickname'] = nickname
    user_data['iss_play_registration_step'] = 'confirm_nickname'
    save_user_data(context, user_id)
    
    # Show confirmation
    text = f"Этап 2/3\nВаш никнейм: #{nickname}"
    keyboard = [
        [InlineKeyboardButton("Продолжить", callback_data="games_nickname_confirm")],
        [InlineKeyboardButton("Изменить", callback_data="games_register_start")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, reply_markup=reply_markup)