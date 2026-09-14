from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice
from telegram.ext import ContextTypes, PreCheckoutQueryHandler, SuccessfulPaymentHandler
from shared import load_user_data, save_user_data
import time

STAR_PRICES = {
    "100": {"stars": 100, "usd": 0.99, "days": 7},
    "500": {"stars": 500, "usd": 3.99, "days": 30},
    "1000": {"stars": 1000, "usd": 6.99, "days": 30},
    "5000": {"stars": 5000, "usd": 29.99, "days": 30},
}

VIP_FEATURES = [
    "🎯 Расширенные лимиты AI (без ограничений)",
    "⚡ Приоритетный ответ от ИИ",
    "🌟 Премиум эмодзи и стикеры",
    "🔒 Приватные чаты с ИИ",
    "📊 Расширенная аналитика ISS Points",
    "🎮 Бесплатные игры ISS Play ежедневно",
    "🎨 Генерация изображений без лимита",
    "🎵 Яндекс Музык премиум доступ",
]

VIP_FEATURES_PREMIUM = VIP_FEATURES + [
    "👑 Персональный ИИ-ассистент Alice",
    "📍 Все карты Arc Maps разблокированы",
    "🎭 Все модели ИИ без ограничений",
    "💎 VIP статус в ISS соцсети",
]


async def vip_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    load_user_data(context, user_id)
    user_data = context.user_data

    from Commands.guest import is_guest_mode, guest_restricted_message
    if is_guest_mode(user_data):
        await guest_restricted_message(update, context)
        return

    is_vip = user_data.get("vip_expiry", 0) > time.time()

    text = "👑 **VIP Подписка APAS**\n\n"
    text += f"Твой статус: {'✅ VIP активен' if is_vip else '❌ Обычный пользователь'}\n\n"

    if is_vip:
        remaining = int(user_data.get("vip_expiry", 0) - time.time())
        days = remaining // 86400
        text += f"⏳ Осталось: {days} дней\n\n"

    text += "Доступные пакеты:\n\n"
    for price_id, pkg in STAR_PRICES.items():
        stars = pkg["stars"]
        usd = pkg["usd"]
        days = pkg["days"]
        features = VIP_FEATURES_PREMIUM if stars >= 1000 else VIP_FEATURES
        text += f"💎 **{stars} Stars** — ${usd} ({days} дней)\n"
        text += f"   📋 {', '.join(f[:15] + '…' for f in features[:4])}\n\n"

    keyboard = []
    for price_id in STAR_PRICES:
        pkg = STAR_PRICES[price_id]
        keyboard.append([InlineKeyboardButton(
            f"💎 {pkg['stars']} Stars — ${pkg['usd']}",
            callback_data=f"vip_buy_{price_id}"
        )])
    keyboard.append([InlineKeyboardButton("❌ Закрыть", callback_data="vip_close")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")


async def handle_vip_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    load_user_data(context, user_id)
    user_data = context.user_data
    data = query.data

    if data == "vip_close":
        await query.edit_message_text("✅ Закрыто. Приходи когда будет готов! 👋")
        return

    if data.startswith("vip_buy_"):
        price_id = data.replace("vip_buy_", "")
        if price_id not in STAR_PRICES:
            await query.edit_message_text("❌ Неверный пакет.")
            return

        pkg = STAR_PRICES[price_id]
        stars = pkg["stars"]
        days = pkg["days"]

        if stars <= 1000:
            features = VIP_FEATURES
        else:
            features = VIP_FEATURES_PREMIUM

        text = (
            f"💎 **Покупка: {stars} Stars**\n\n"
            f"💰 Цена: ${pkg['usd']}\n"
            f"⏳ Срок: {days} дней\n\n"
            "**Что получишь:**\n"
        )
        for f in features:
            text += f"  ✅ {f}\n"

        payload = f"vip_{price_id}_{user_id}"

        keyboard = [
            [InlineKeyboardButton(
                f"💰 Оплатить {stars} Stars ⭐",
                callback_data=f"vip_pay_confirm_{price_id}"
            )],
            [InlineKeyboardButton("❌ Отмена", callback_data="vip_close")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")
        return

    if data.startswith("vip_pay_confirm_"):
        price_id = data.replace("vip_pay_confirm_", "")
        pkg = STAR_PRICES[price_id]
        stars = pkg["stars"]

        try:
            await context.bot.send_invoice(
                chat_id=query.from_user.id,
                title=f"APAS VIP — {stars} Stars",
                description=f"VIP подписка на {stars} Stars на {pkg['days']} дней. Все привилегии APAS.",
                payload=f"vip_{price_id}_{query.from_user.id}",
                currency="XTR",
                prices=[LabeledPrice(label=f"VIP {stars} Stars", amount=stars)],
                need_name=True,
                need_phone_number=False,
                need_email=False,
                need_shipping_address=False,
                is_flexible=False,
            )
            await query.answer()
        except Exception as e:
            await query.edit_message_text(f"❌ Ошибка оплаты: {e}")
        return

    if data.startswith("vip_pay_"):
        price_id = data.replace("vip_pay_", "")
        pkg = STAR_PRICES[price_id]
        stars = pkg["stars"]
        days = pkg["days"]

        user_data["vip_expiry"] = str(int(time.time() + days * 86400))
        user_data["vip_level"] = stars
        user_data["is_vip"] = True
        save_user_data(context, user_id)

        text = (
            f"🎉 **VIP активирован!**\n\n"
            f"💎 {stars} Stars\n⏳ {days} дней\n\n"
            "✅ Все VIP фичи разблокированы!\n\n"
            "🧞 Используй /alice, /models, /games, /iss и всё расширенное!"
        )
        await query.edit_message_text(text, parse_mode="Markdown")
        return


async def vip_status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    load_user_data(context, user_id)
    user_data = context.user_data

    is_vip = user_data.get("vip_expiry", 0) > time.time()

    if is_vip:
        remaining = int(user_data.get("vip_expiry", 0) - time.time())
        days = remaining // 86400
        hours = (remaining % 86400) // 3600
        text = (
            f"👑 **VIP Статус: АКТИВЕН**\n\n"
            f"⏳ Осталось: {days} дн {hours} ч\n"
            f"💎 Уровень: {user_data.get('vip_level', 'N/A')} Stars\n"
            f"📋 Фичи: {', '.join(f[:20] for f in VIP_FEATURES_PREMIUM[:4])}..."
        )
    else:
        text = (
            "👑 **VIP Статус: НЕ АКТИВЕН**\n\n"
            "Купи VIP и получи расширенные возможности!\n\n"
            "Впиши /vip чтобы увидеть пакеты."
        )

    await update.message.reply_text(text, parse_mode="Markdown")


async def pre_checkout_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query
    await query.answer(ok=True)


async def successful_payment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    payment = update.effective_message.successful_payment
    user_id = update.effective_user.id
    load_user_data(context, user_id)
    user_data = context.user_data

    if payment.currency == "XTR":
        total_stars = payment.total_amount
        user_data["vip_expiry"] = str(int(time.time() + 30 * 86400))
        user_data["is_vip"] = True
        user_data["vip_level"] = total_stars
        save_user_data(context, user_id)

        text = (
            f"🎉 **VIP АКТИВИРОВАН!**\n\n"
            f"💎 Оплачено: {total_stars} Stars\n"
            f"⏳ Срок: 30 дней\n\n"
            "✅ Все привилегии APAS разблокированы!\n\n"
            "🧞 Используй /alice, /models, /games, /iss и всё расширенное!"
        )
        await update.effective_message.reply_text(text, parse_mode="Markdown")
    else:
        await update.effective_message.reply_text("✅ Оплата принята!")


def get_vip_handlers():
    return [
        PreCheckoutQueryHandler(pre_checkout_query_handler),
        SuccessfulPaymentHandler(successful_payment_handler),
    ]
