from telegram import Update
from telegram.ext import ContextTypes


async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Команда /about - показывает информацию о боте и системе APAS
    """
    text = ("Данный бот создан для непрерывного развития и разработки систем APAS и языковых моделей ASAD и NVLM. "
            "Данный бот выполняет роль песочницы для обкатки всех нововведений и может иметь нестабильную работу или генерацию ответов, "
            "так как сюда добавляются все новые решения и функции без определенного тестирования. "
            "По всем вопросам и ошибкам пишите @rakcheev_me")
    await update.message.reply_text(text)