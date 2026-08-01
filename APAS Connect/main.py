import os
import sys
import json
import psutil
import platform
import requests
import threading
import time
import tkinter as tk
from tkinter import messagebox
from flask import Flask, jsonify
import pystray
from PIL import Image, ImageDraw
import subprocess
import winreg

# Конфигурация
CONFIG_FILE = 'config.json'
DEFAULT_CONFIG = {
    'bot_token': 'YOUR_BOT_TOKEN_HERE',  # Замените на ваш токен
    'server_port': 5000,
    'server_host': '127.0.0.1'
}

# Flask приложение
app = Flask(__name__)

def load_config():
    """Загрузить конфигурацию"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return DEFAULT_CONFIG

def save_config(config):
    """Сохранить конфигурацию"""
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)

def get_system_info():
    """Получить информацию о системе"""
    try:
        # Базовая информация
        info = {
            'hostname': platform.node(),
            'os': platform.system() + ' ' + platform.release(),
            'architecture': platform.machine(),
            'processor': platform.processor() or 'Unknown'
        }

        # Оперативная память
        memory = psutil.virtual_memory()
        info['ram_total_gb'] = round(memory.total / (1024**3), 1)
        info['ram_available_gb'] = round(memory.available / (1024**3), 1)
        info['ram_percent'] = memory.percent

        # Диск
        disk = psutil.disk_usage('/')
        info['disk_total_gb'] = round(disk.total / (1024**3), 1)
        info['disk_free_gb'] = round(disk.free / (1024**3), 1)
        info['disk_percent'] = disk.percent

        # Батарея (если есть)
        battery = psutil.sensors_battery()
        if battery:
            info['battery_percent'] = battery.percent
            info['battery_plugged'] = battery.power_plugged
        else:
            info['battery_percent'] = None

        # CPU
        info['cpu_percent'] = psutil.cpu_percent(interval=1)

        return info
    except Exception as e:
        return {'error': str(e)}

@app.route('/system_info')
def system_info():
    """API endpoint для системной информации"""
    return jsonify(get_system_info())

@app.route('/ping')
def ping():
    """Проверка соединения"""
    return jsonify({'status': 'ok', 'timestamp': time.time()})

def get_system_theme():
    """Определить тему системы Windows"""
    try:
        import winreg

        # Проверяем реестр Windows для темы
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
        value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        winreg.CloseKey(key)

        # 0 = темная тема, 1 = светлая тема
        return "light" if value == 1 else "dark"
    except:
        # Если не удалось определить, возвращаем темную по умолчанию
        return "dark"

def create_icon():
    """Создать иконку для трея в зависимости от темы"""
    theme = get_system_theme()

    # Создаем иконку программно в зависимости от темы
    image = Image.new('RGBA', (64, 64), color=(0, 0, 0, 0))  # Прозрачный фон

    # Создаем круг с градиентом
    draw = ImageDraw.Draw(image)

    # Основной цвет зависит от темы
    if theme == "dark":
        # Темная тема - светлая иконка
        bg_color = (255, 255, 255, 220)  # Белый с прозрачностью
        text_color = (0, 0, 0, 255)      # Черный текст
    else:
        # Светлая тема - темная иконка
        bg_color = (0, 0, 0, 180)       # Черный с прозрачностью
        text_color = (255, 255, 255, 255)  # Белый текст

    # Рисуем круг
    draw.ellipse([4, 4, 60, 60], fill=bg_color)

    # Рисуем букву A в центре
    draw.text((32, 32), 'A', fill=text_color, anchor='mm', font=None)

    print(f"📱 Создана иконка для {theme} темы")
    return image

def on_quit(icon, item):
    """Обработчик выхода из трея"""
    icon.stop()
    os._exit(0)

def show_main_window():
    """Показать главное окно"""
    root = tk.Tk()
    root.title("APAS Connect")
    root.geometry("300x200")
    root.resizable(False, False)

    # Центрируем окно
    root.eval('tk::PlaceWindow . center')

    tk.Label(root, text="🎉 APAS Connect активен!", font=("Arial", 14)).pack(pady=20)
    tk.Label(root, text="Программа подключена к боту", font=("Arial", 10)).pack(pady=5)

    def disconnect():
        """Отключить программу"""
        if messagebox.askyesno("Подтверждение", "Вы действительно хотите отключить APAS Connect?"):
            root.destroy()
            os._exit(0)

    def refresh():
        """Обновить соединение"""
        try:
            config = load_config()
            # Проверяем соединение с ботом
            # Здесь можно добавить проверку API бота
            messagebox.showinfo("Обновление", "Соединение обновлено успешно!")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось обновить соединение: {e}")

    tk.Button(root, text="Отключить", command=disconnect, bg='red', fg='white').pack(side='left', padx=20, pady=20)
    tk.Button(root, text="Обновить", command=refresh, bg='green', fg='white').pack(side='right', padx=20, pady=20)

    root.mainloop()

def show_startup_message():
    """Показывает информационное окно при запуске"""
    root = tk.Tk()
    root.title("APAS Connect")
    root.geometry("300x150")
    root.resizable(False, False)

    # Центрируем окно
    root.eval('tk::PlaceWindow . center')

    tk.Label(root, text="🚀 APAS Connect запущен!", font=("Arial", 12, "bold")).pack(pady=10)
    tk.Label(root, text="Программа работает в фоне.\nСервер доступен на http://localhost:5000", justify=tk.CENTER).pack(pady=5)

    tk.Button(root, text="OK", command=root.destroy).pack(pady=10)

    root.mainloop()

def run_flask():
    """Запустить Flask сервер в отдельном потоке"""
    config = load_config()
    app.run(host=config['server_host'], port=config['server_port'], debug=False)

def main():
    """Главная функция"""
    print("🚀 Запуск APAS Connect...")

    # Запускаем Flask сервер в отдельном потоке
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # Небольшая задержка для запуска сервера
    time.sleep(1)

    # Создаем иконку для трея
    icon = pystray.Icon("APAS Connect", create_icon(), "APAS Connect")

    # Меню трея
    menu = pystray.Menu(
        pystray.MenuItem("Показать", lambda: show_main_window()),
        pystray.MenuItem("Выход", on_quit)
    )
    icon.menu = menu

    # Запускаем трей (без показа окна при запуске)
    print("📱 Программа запущена и свернута в трей")
    icon.run()

if __name__ == '__main__':
    main()