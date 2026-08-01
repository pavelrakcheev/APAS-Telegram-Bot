#!/usr/bin/env python3
"""
Тестовый скрипт для проверки API APAS Connect
"""

import requests
import time
import subprocess
import sys

def test_api():
    """Тестирование API"""
    try:
        print("🔍 Тестирую API APAS Connect...")

        # Тестируем /ping
        response = requests.get('http://localhost:5000/ping', timeout=5)
        if response.status_code == 200:
            print("✅ /ping работает")
        else:
            print(f"❌ /ping вернул статус {response.status_code}")

        # Тестируем /system_info
        response = requests.get('http://localhost:5000/system_info', timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ /system_info работает")
            print(f"   CPU: {data.get('cpu_percent', 'N/A')}%")
            print(f"   RAM: {data.get('ram_percent', 'N/A')}%")
            print(f"   Disk: {data.get('disk_percent', 'N/A')}%")
            print(f"   OS: {data.get('os', 'N/A')}")
            return True
        else:
            print(f"❌ /system_info вернул статус {response.status_code}")
            return False

    except requests.exceptions.ConnectionError:
        print("❌ Не удается подключиться к APAS Connect")
        return False
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

if __name__ == '__main__':
    # Запускаем APAS Connect в фоне
    print("🚀 Запускаю APAS Connect...")
    process = subprocess.Popen([sys.executable, 'main.py'], cwd='.')

    # Ждем запуска
    time.sleep(3)

    # Тестируем API
    success = test_api()

    # Останавливаем процесс
    process.terminate()
    process.wait()

    if success:
        print("🎉 Тестирование завершено успешно!")
    else:
        print("💥 Тестирование провалилось!")