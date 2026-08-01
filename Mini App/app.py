from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import json
import os
from dotenv import load_dotenv
import sys

load_dotenv()

# Добавляем путь к модулям
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Modules'))

try:
    from arc_weather import get_weather_info
    WEATHER_MODULE_AVAILABLE = True
except ImportError:
    WEATHER_MODULE_AVAILABLE = False
    print("Warning: arc_weather module not available")

app = Flask(__name__,
            static_folder='.',
            static_url_path='')
CORS(app)  # Разрешаем CORS для всех доменов

# Путь к файлу с данными пользователей
# Проверяем несколько возможных путей
POSSIBLE_PATHS = [
    os.path.join(os.path.dirname(__file__), 'users_data.json'),       # ./users_data.json (Mini App folder)
    os.path.join(os.path.dirname(__file__), '..', 'users_data.json'),  # ../users_data.json
    os.path.join(os.path.dirname(__file__), '..', 'data', 'users_data.json'),  # ../data/users_data.json
    '/opt/render/project/src/users_data.json',                       # Render.com путь
    os.path.join(os.getcwd(), 'users_data.json'),                    # Текущая директория
]

USERS_DATA_FILE = None
for path in POSSIBLE_PATHS:
    if os.path.exists(path):
        USERS_DATA_FILE = path
        print(f"Found users_data.json at: {path}")
        break

if USERS_DATA_FILE is None:
    print(f"Warning: users_data.json not found in any of: {POSSIBLE_PATHS}")
    USERS_DATA_FILE = POSSIBLE_PATHS[0]  # Используем первый путь как fallback

@app.route('/api/user-profile', methods=['GET'])
def get_user_profile():
    """
    API endpoint для получения данных профиля пользователя
    Ожидает user_id в query параметрах
    """
    user_id = request.args.get('user_id')

    if not user_id:
        print(f"API Error: user_id parameter missing")
        return jsonify({'error': 'user_id is required'}), 400

    print(f"API Request: Getting profile for user_id {user_id}")

    try:
        # Загружаем данные пользователей
        if os.path.exists(USERS_DATA_FILE):
            with open(USERS_DATA_FILE, 'r', encoding='utf-8') as f:
                users_data = json.load(f)
            print(f"Users data loaded successfully, {len(users_data)} users found")
        else:
            print(f"API Error: users_data.json not found at {USERS_DATA_FILE}")
            return jsonify({'error': 'User data not found'}), 404

        # Ищем пользователя
        if user_id not in users_data:
            print(f"API Error: User {user_id} not found in users_data")
            print(f"Available users: {list(users_data.keys())}")
            return jsonify({'error': 'User not found'}), 404

        user_data = users_data[user_id]
        print(f"User data found: {user_data}")

        # Проверяем, что пользователь завершил настройку
        if not user_data.get('setup_completed', False):
            print(f"API Error: User {user_id} profile not completed")
            return jsonify({'error': 'User profile not completed'}), 403

        # Форматируем дату регистрации
        reg_date_raw = user_data.get('registration_date', 'Не указано')
        if reg_date_raw != 'Не указано' and str(reg_date_raw).isdigit():
            # Если это timestamp, конвертируем в дату
            import time
            # Проверяем, является ли timestamp в секундах или миллисекундах
            timestamp = int(reg_date_raw)
            if timestamp > 1e10:  # Если timestamp в миллисекундах
                timestamp = timestamp / 1000
            try:
                reg_date = time.strftime('%d.%m.%Y', time.localtime(timestamp))
            except:
                reg_date = str(reg_date_raw)
        else:
            reg_date = str(reg_date_raw)

        # Формируем ответ с данными профиля
        profile_data = {
            'name': user_data.get('name', 'Не указано'),
            'username': user_data.get('username', ''),
            'age': user_data.get('age', 'Не указано'),
            'city': user_data.get('city', 'Не указано'),
            'registration_date': reg_date,
            'total_reports': user_data.get('total_reports', 0),
            'active_reports': user_data.get('active_reports', 0),
            'resolved_reports': user_data.get('resolved_reports', 0)
        }

        print(f"API Response: {profile_data}")
        return jsonify(profile_data)

    except Exception as e:
        print(f"API Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/weather', methods=['GET'])
def get_weather():
    """
    API endpoint для получения данных о погоде
    """
    try:
        if not WEATHER_MODULE_AVAILABLE:
            return jsonify({'error': 'Weather module not available'}), 503

        # Для демонстрации используем координаты Москвы
        # В реальном приложении координаты должны приходить от пользователя
        lat = 55.7558  # Москва
        lon = 37.6173

        # Импортируем asyncio для работы с асинхронной функцией
        import asyncio

        # Создаем event loop для выполнения асинхронной функции
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            weather_data = loop.run_until_complete(get_weather_info(lat, lon))

            # Форматируем данные для Mini App
            weather_info = {
                'city': 'Москва',  # В будущем можно определять город по координатам
                'temperature': weather_data['current_temp'],
                'condition': weather_data['forecast']['day']['condition'].capitalize(),
                'feels_like': weather_data['feels_like']
            }

            print(f"Weather API Response: {weather_info}")
            return jsonify(weather_info)

        finally:
            loop.close()

    except Exception as e:
        print(f"Weather API Error: {str(e)}")
        import traceback
        traceback.print_exc()

        # Возвращаем демо-данные в случае ошибки
        return jsonify({
            'city': 'Москва',
            'temperature': 12,
            'condition': 'Солнечно',
            'feels_like': 10
        })

@app.route('/api/user-settings', methods=['GET'])
def get_user_settings():
    """
    API endpoint для получения настроек пользователя
    """
    user_id = request.args.get('user_id')

    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400

    try:
        # Загружаем данные пользователей
        if os.path.exists(USERS_DATA_FILE):
            with open(USERS_DATA_FILE, 'r', encoding='utf-8') as f:
                users_data = json.load(f)
        else:
            return jsonify({'error': 'User data not found'}), 404

        # Ищем пользователя
        if user_id not in users_data:
            # Возвращаем настройки по умолчанию для новых пользователей
            return jsonify({
                'streaming_enabled': True,
                'updates_enabled': True,
                'changes_enabled': True,
                'promo_enabled': True
            })

        user_data = users_data[user_id]

        # Возвращаем настройки пользователя
        settings = {
            'streaming_enabled': user_data.get('streaming_enabled', True),
            'updates_enabled': user_data.get('updates_enabled', True),
            'changes_enabled': user_data.get('changes_enabled', True),
            'promo_enabled': user_data.get('promo_enabled', True)
        }

        print(f"Settings API Response: {settings}")
        return jsonify(settings)

    except Exception as e:
        print(f"Settings API Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/user-settings', methods=['POST'])
def update_user_settings():
    """
    API endpoint для обновления настроек пользователя
    """
    try:
        data = request.get_json()

        if not data or 'user_id' not in data or 'setting' not in data:
            return jsonify({'error': 'user_id, setting, and value are required'}), 400

        user_id = data['user_id']
        setting = data['setting']
        value = data['value']

        # Загружаем данные пользователей
        if os.path.exists(USERS_DATA_FILE):
            with open(USERS_DATA_FILE, 'r', encoding='utf-8') as f:
                users_data = json.load(f)
        else:
            return jsonify({'error': 'User data not found'}), 404

        # Инициализируем данные пользователя, если их нет
        if user_id not in users_data:
            users_data[user_id] = {}

        # Обновляем настройку
        users_data[user_id][setting] = value

        # Сохраняем обновленные данные
        with open(USERS_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(users_data, f, ensure_ascii=False, indent=2)

        print(f"Settings updated for user {user_id}: {setting} = {value}")
        return jsonify({'success': True})

    except Exception as e:
        print(f"Settings Update API Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/points')
def points():
    """Отдаем страницу Points"""
    return send_from_directory('.', 'points.html')

@app.route('/settings')
def settings():
    """Отдаем страницу Settings"""
    return send_from_directory('.', 'settings.html')

@app.route('/')
def index():
    """Отдаем статический HTML файл"""
    return send_from_directory('.', 'index.html')

@app.route('/styles.css')
def styles():
    """Отдаем CSS файл"""
    return send_from_directory('.', 'styles.css')

@app.route('/api/debug', methods=['GET'])
def debug():
    """Debug endpoint для проверки работы API"""
    debug_info = {
        'status': 'ok',
        'timestamp': '2024-01-01T00:00:00Z',
        'users_data_file': USERS_DATA_FILE,
        'file_exists': os.path.exists(USERS_DATA_FILE),
        'current_dir': os.getcwd(),
        'files_in_current_dir': os.listdir('.') if os.path.exists('.') else [],
        'parent_dir': os.path.dirname(__file__),
        'files_in_parent_dir': os.listdir(os.path.dirname(__file__)) if os.path.exists(os.path.dirname(__file__)) else []
    }

    if debug_info['file_exists']:
        try:
            with open(USERS_DATA_FILE, 'r', encoding='utf-8') as f:
                users_data = json.load(f)
            debug_info['users_count'] = len(users_data)
            debug_info['user_ids'] = list(users_data.keys())
        except Exception as e:
            debug_info['file_read_error'] = str(e)

    return jsonify(debug_info)

if __name__ == '__main__':
    # Получаем порт из переменной окружения (для Render.com)
    port = int(os.environ.get('PORT', 5000))
    # Слушаем на всех интерфейсах (для production)
    app.run(host='0.0.0.0', port=port, debug=False)