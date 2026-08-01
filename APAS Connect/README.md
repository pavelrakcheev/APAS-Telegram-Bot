# APAS Connect

Программа-посредник для связи между вашим ПК и Telegram ботом APAS.

## 🚀 Функции

- 📊 Сбор системной информации (ОЗУ, диск, CPU, батарея)
- 🌐 HTTP API сервер для получения данных
- 📱 Сворачивание в системный трей
- 🔄 GUI с кнопками управления

## 📋 Требования

- Python 3.8+
- Windows 10/11

## 🛠️ Установка

1. **Установите зависимости:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Настройте конфигурацию:**
   Отредактируйте `config.json`:
   ```json
   {
     "bot_token": "ВАШ_ТОКЕН_БОТА",
     "server_port": 5000,
     "server_host": "127.0.0.1"
   }
   ```

## ▶️ Запуск

### В режиме разработки:
```bash
python main.py
```

### Создание .exe файла:

1. **Установите PyInstaller:**
   ```bash
   pip install pyinstaller
   ```

2. **Создайте иконку (опционально):**
   Поместите файл `icon.ico` в папку проекта

3. **Соберите exe:**
   ```bash
   python build_exe.py
   ```

4. **Запустите:**
   Найдите `APAS_Connect.exe` в папке `dist/`

## 📡 API Endpoints

- `GET /system_info` - Получить информацию о системе
- `GET /ping` - Проверка соединения

## 🎯 Использование

1. Запустите программу
2. Появится окно "APAS Connect активен!"
3. Нажмите "Обновить" для проверки соединения
4. Программа свернется в трей
5. Правой кнопкой мыши на иконке в трее → "Показать" для повторного открытия

## 🔧 Настройка в боте

В основном боте APAS добавьте команду `/remote`:

```python
async def remote_command(update, context):
    try:
        response = requests.get('http://127.0.0.1:5000/system_info', timeout=5)
        data = response.json()

        message = f"""💻 **Информация о ПК**

🖥️ **Модель:** {data.get('hostname', 'Unknown')}
🧠 **Процессор:** {data.get('processor', 'Unknown')}
💾 **ОЗУ:** {data['ram_total_gb']} ГБ (свободно: {data['ram_available_gb']} ГБ)
💿 **Память:** {data['disk_total_gb']} ГБ (свободно: {data['disk_free_gb']} ГБ)"""

        if data.get('battery_percent'):
            message += f"\n🔋 **Батарея:** {data['battery_percent']}%"

        keyboard = [[InlineKeyboardButton("Назад", callback_data="back_to_main")]]
        await update.message.reply_text(message, reply_markup=InlineKeyboardMarkup(keyboard))

    except Exception as e:
        await update.message.reply_text(f"❌ Не удалось получить информацию о ПК: {e}")
```

## 🛡️ Безопасность

- Программа работает только локально (127.0.0.1)
- Для удаленного доступа настройте VPN или прокси
- Данные не передаются третьим лицам

## 📝 Логи

Логи выводятся в консоль при запуске из Python. В exe версии логи недоступны.

## 🐛 Устранение неполадок

1. **Программа не запускается:**
   - Проверьте установку всех зависимостей
   - Убедитесь, что порт 5000 свободен

2. **Бот не может подключиться:**
   - Проверьте, что APAS Connect запущен
   - Проверьте настройки в config.json

3. **Иконка не отображается в трее:**
   - Установите pystray и Pillow
   - Перезапустите программу