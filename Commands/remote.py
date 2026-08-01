import requests
from telegram import Update
from telegram.ext import ContextTypes


async def remote_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Команда /remote - показывает информацию о подключенном ПК через APAS Connect
    """
    user_id = update.effective_user.id

    try:
        # Попытка подключения к локальному API APAS Connect
        response = requests.get('http://localhost:5000/system_info', timeout=5)

        if response.status_code == 200:
            data = response.json()

            # Форматирование информации о системе
            system_info = ("🖥️ Информация о подключенном ПК:\n\n"
                          f"💻 ОС: {data.get('os', 'Неизвестно')}\n"
                          f"🔧 Процессор: {data.get('cpu', 'Неизвестно')}\n"
                          f"🧠 RAM: {data.get('ram_total', 'Неизвестно')} GB\n"
                          f"💾 Диск: {data.get('disk_total', 'Неизвестно')} GB\n"
                          f"📊 Загрузка CPU: {data.get('cpu_percent', 'Неизвестно')}%\n"
                          f"🧠 Использование RAM: {data.get('ram_percent', 'Неизвестно')}%\n"
                          f"💾 Свободно на диске: {data.get('disk_free', 'Неизвестно')} GB\n"
                          f"🌐 IP адрес: {data.get('ip_address', 'Неизвестно')}\n"
                          f"⏰ Время работы: {data.get('uptime', 'Неизвестно')}\n"
                          f"🔗 Статус: Подключено ✅")

            await update.message.reply_text(system_info)
        else:
            await update.message.reply_text("❌ Ошибка подключения к APAS Connect. Убедитесь, что программа запущена на вашем ПК.")

    except requests.exceptions.ConnectionError:
        await update.message.reply_text("❌ Не удается подключиться к APAS Connect. Запустите программу APAS Connect на вашем ПК.")

    except requests.exceptions.Timeout:
        await update.message.reply_text("⏱️ Таймаут подключения. Проверьте, запущена ли программа APAS Connect.")

    except Exception as e:
        await update.message.reply_text(f"❌ Произошла ошибка при получении информации о системе: {str(e)}")