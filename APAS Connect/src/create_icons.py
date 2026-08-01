#!/usr/bin/env python3
"""
Скрипт для создания ICO файлов из PNG иконок
"""

from PIL import Image
import os

def create_ico_from_png(png_path, ico_path, sizes):
    """Создать ICO файл из PNG с указанными размерами"""
    try:
        # Открываем оригинальное изображение
        img = Image.open(png_path)

        # Создаем список изображений разных размеров
        icons = []
        for size in sizes:
            # Масштабируем изображение
            resized = img.resize((size, size), Image.Resampling.LANCZOS)
            icons.append(resized)

        # Сохраняем как ICO
        icons[0].save(ico_path, format='ICO', sizes=[(size, size) for size in sizes])

        print(f"✅ Создан {ico_path} с размерами: {sizes}")
        return True

    except Exception as e:
        print(f"❌ Ошибка при создании {ico_path}: {e}")
        return False

def main():
    """Главная функция"""
    print("🎨 Создание ICO файлов для APAS Connect...")

    # Создаем ICO для программы (несколько размеров)
    program_sizes = [16, 32, 48, 64, 128, 256]
    if create_ico_from_png('Icon.png', '../icon.ico', program_sizes):
        print("📁 Программная иконка сохранена как ../icon.ico")

    # Создаем ICO для трея (темная тема)
    tray_sizes = [32, 64]
    if create_ico_from_png('Icon tray (black).png', '../icon_tray_black.ico', tray_sizes):
        print("📁 Иконка трея (темная) сохранена как ../icon_tray_black.ico")

    # Создаем ICO для трея (светлая тема)
    if create_ico_from_png('Icon tray (white).png', '../icon_tray_white.ico', tray_sizes):
        print("📁 Иконка трея (светлая) сохранена как ../icon_tray_white.ico")

    print("🎉 Все ICO файлы созданы!")

if __name__ == '__main__':
    main()