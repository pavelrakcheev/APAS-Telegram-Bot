import PyInstaller.__main__
import os

# Параметры сборки
PyInstaller.__main__.run([
    'main.py',  # Основной файл
    '--onefile',  # Один exe файл
    '--windowed',  # Без консольного окна
    '--name=APAS_Connect',  # Имя exe файла
    '--icon=icon.ico',  # Иконка (если есть)
    '--hidden-import=psutil',  # Скрытые импорты
    '--hidden-import=flask',
    '--hidden-import=pystray',
    '--hidden-import=PIL',
    '--hidden-import=tkinter',
    '--add-data=config.json;.',  # Добавить config файл
    '--clean',  # Очистить временные файлы
    '--noconfirm'  # Без подтверждений
])

print("✅ Сборка завершена! Файл APAS_Connect.exe создан в папке dist/")