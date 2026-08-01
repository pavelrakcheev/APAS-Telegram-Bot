"""
Модуль генерации мини-приложений APAS
Создает готовые мини-приложения на основе текстовых описаний
"""

import os
import json
import shutil
from typing import Dict, List, Optional
from datetime import datetime

class MiniAppGenerator:
    """Генератор мини-приложений"""

    def __init__(self, base_path: str = "users_apps"):
        self.base_path = base_path
        self.templates_path = os.path.join(os.path.dirname(__file__), "templates")
        os.makedirs(self.base_path, exist_ok=True)
        os.makedirs(self.templates_path, exist_ok=True)

    def create_calculator_app(self, app_name: str, user_id: int) -> str:
        """Создать мини-приложение калькулятор"""
        app_dir = os.path.join(self.base_path, f"{user_id}_{app_name.lower().replace(' ', '_')}")

        # Создаем структуру приложения
        os.makedirs(app_dir, exist_ok=True)

        # Создаем app.py
        app_code = f'''from flask import Flask, request, jsonify, render_template_string
import os

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>{app_name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 400px; margin: 0 auto; padding: 20px; }}
        .calculator {{ background: #f0f0f0; padding: 20px; border-radius: 10px; }}
        .display {{ background: white; padding: 10px; margin-bottom: 10px; border-radius: 5px; font-size: 24px; text-align: right; }}
        .buttons {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; }}
        button {{ padding: 15px; font-size: 18px; border: none; border-radius: 5px; cursor: pointer; }}
        .number {{ background: #e0e0e0; }}
        .operator {{ background: #ff9500; color: white; }}
        .equals {{ background: #ff3b30; color: white; grid-column: span 2; }}
        .clear {{ background: #8e8e93; color: white; }}
    </style>
</head>
<body>
    <h1>{app_name}</h1>
    <div class="calculator">
        <div class="display" id="display">0</div>
        <div class="buttons">
            <button class="clear" onclick="clearDisplay()">C</button>
            <button class="operator" onclick="appendToDisplay('/')">/</button>
            <button class="operator" onclick="appendToDisplay('*')">*</button>
            <button class="operator" onclick="appendToDisplay('-')">-</button>
            <button class="number" onclick="appendToDisplay('7')">7</button>
            <button class="number" onclick="appendToDisplay('8')">8</button>
            <button class="number" onclick="appendToDisplay('9')">9</button>
            <button class="operator" onclick="appendToDisplay('+')">+</button>
            <button class="number" onclick="appendToDisplay('4')">4</button>
            <button class="number" onclick="appendToDisplay('5')">5</button>
            <button class="number" onclick="appendToDisplay('6')">6</button>
            <button class="number" onclick="appendToDisplay('1')">1</button>
            <button class="number" onclick="appendToDisplay('2')">2</button>
            <button class="number" onclick="appendToDisplay('3')">3</button>
            <button class="equals" onclick="calculate()">=</button>
            <button class="number" onclick="appendToDisplay('0')">0</button>
            <button class="number" onclick="appendToDisplay('.')">.</button>
        </div>
    </div>

    <script>
        let display = document.getElementById('display');

        function appendToDisplay(value) {{
            if (display.innerText === '0') {{
                display.innerText = value;
            }} else {{
                display.innerText += value;
            }}
        }}

        function clearDisplay() {{
            display.innerText = '0';
        }}

        function calculate() {{
            try {{
                display.innerText = eval(display.innerText);
            }} catch {{
                display.innerText = 'Error';
            }}
        }}
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/calculate', methods=['POST'])
def api_calculate():
    data = request.json
    expression = data.get('expression', '')
    try:
        result = eval(expression)
        return jsonify({{'result': result}})
    except:
        return jsonify({{'error': 'Invalid expression'}}), 400

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
'''

        # Создаем requirements.txt
        requirements = """Flask==2.3.3
Werkzeug==2.3.7
"""

        # Создаем README.md
        readme = f"""# {app_name}

Простой калькулятор - мини-приложение APAS.

## Запуск
```bash
pip install -r requirements.txt
python app.py
```

Приложение будет доступно на http://localhost:5001
"""

        # Записываем файлы
        with open(os.path.join(app_dir, 'app.py'), 'w', encoding='utf-8') as f:
            f.write(app_code)

        with open(os.path.join(app_dir, 'requirements.txt'), 'w', encoding='utf-8') as f:
            f.write(requirements)

        with open(os.path.join(app_dir, 'README.md'), 'w', encoding='utf-8') as f:
            f.write(readme)

        return app_dir

    def create_notes_app(self, app_name: str, user_id: int) -> str:
        """Создать мини-приложение заметки"""
        app_dir = os.path.join(self.base_path, f"{user_id}_{app_name.lower().replace(' ', '_')}")

        os.makedirs(app_dir, exist_ok=True)

        app_code = f'''from flask import Flask, request, jsonify, render_template_string
import json
import os
from datetime import datetime

app = Flask(__name__)

NOTES_FILE = 'notes.json'

def load_notes():
    if os.path.exists(NOTES_FILE):
        with open(NOTES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_notes(notes):
    with open(NOTES_FILE, 'w', encoding='utf-8') as f:
        json.dump(notes, f, indent=2, ensure_ascii=False)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>{app_name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; }}
        .note {{ background: #f9f9f9; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #007bff; }}
        .note-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }}
        .note-title {{ font-weight: bold; font-size: 18px; }}
        .note-date {{ color: #666; font-size: 12px; }}
        .note-content {{ line-height: 1.5; }}
        .add-note {{ margin: 20px 0; }}
        input, textarea {{ width: 100%; padding: 10px; margin: 5px 0; border: 1px solid #ddd; border-radius: 4px; }}
        button {{ padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }}
        button:hover {{ background: #0056b3; }}
        .delete-btn {{ background: #dc3545; margin-left: 10px; }}
        .delete-btn:hover {{ background: #c82333; }}
    </style>
</head>
<body>
    <h1>{app_name}</h1>

    <div class="add-note">
        <h3>Добавить заметку</h3>
        <input type="text" id="noteTitle" placeholder="Заголовок заметки">
        <textarea id="noteContent" rows="4" placeholder="Текст заметки"></textarea>
        <button onclick="addNote()">Добавить</button>
    </div>

    <div id="notesList">
        <!-- Заметки будут загружены здесь -->
    </div>

    <script>
        async function loadNotes() {{
            const response = await fetch('/api/notes');
            const notes = await response.json();
            displayNotes(notes);
        }}

        function displayNotes(notes) {{
            const container = document.getElementById('notesList');
            container.innerHTML = '';

            notes.forEach((note, index) => {{
                const noteDiv = document.createElement('div');
                noteDiv.className = 'note';
                noteDiv.innerHTML = `
                    <div class="note-header">
                        <div class="note-title">${{note.title}}</div>
                        <div class="note-date">${{note.date}}</div>
                        <button class="delete-btn" onclick="deleteNote(${{index}})">Удалить</button>
                    </div>
                    <div class="note-content">${{note.content}}</div>
                `;
                container.appendChild(noteDiv);
            }});
        }}

        async function addNote() {{
            const title = document.getElementById('noteTitle').value;
            const content = document.getElementById('noteContent').value;

            if (!title || !content) {{
                alert('Заполните все поля');
                return;
            }}

            const response = await fetch('/api/notes', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify({{ title, content }})
            }});

            if (response.ok) {{
                document.getElementById('noteTitle').value = '';
                document.getElementById('noteContent').value = '';
                loadNotes();
            }}
        }}

        async function deleteNote(index) {{
            if (confirm('Удалить заметку?')) {{
                await fetch(`/api/notes/${{index}}`, {{ method: 'DELETE' }});
                loadNotes();
            }}
        }}

        loadNotes();
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/notes', methods=['GET'])
def get_notes():
    return jsonify(load_notes())

@app.route('/api/notes', methods=['POST'])
def add_note():
    data = request.json
    notes = load_notes()

    new_note = {{
        'title': data['title'],
        'content': data['content'],
        'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }}

    notes.append(new_note)
    save_notes(notes)
    return jsonify(new_note), 201

@app.route('/api/notes/<int:index>', methods=['DELETE'])
def delete_note(index):
    notes = load_notes()
    if 0 <= index < len(notes):
        deleted_note = notes.pop(index)
        save_notes(notes)
        return jsonify(deleted_note)
    return jsonify({{'error': 'Note not found'}}), 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002)
'''

        requirements = """Flask==2.3.3
Werkzeug==2.3.7
"""

        readme = f"""# {app_name}

Приложение для заметок - мини-приложение APAS.

## Запуск
```bash
pip install -r requirements.txt
python app.py
```

Приложение будет доступно на http://localhost:5002
"""

        with open(os.path.join(app_dir, 'app.py'), 'w', encoding='utf-8') as f:
            f.write(app_code)

        with open(os.path.join(app_dir, 'requirements.txt'), 'w', encoding='utf-8') as f:
            f.write(requirements)

        with open(os.path.join(app_dir, 'README.md'), 'w', encoding='utf-8') as f:
            f.write(readme)

        return app_dir

    def create_timer_app(self, app_name: str, user_id: int) -> str:
        """Создать мини-приложение таймер"""
        app_dir = os.path.join(self.base_path, f"{user_id}_{app_name.lower().replace(' ', '_')}")

        os.makedirs(app_dir, exist_ok=True)

        app_code = f'''from flask import Flask, request, jsonify, render_template_string
import time
import threading

app = Flask(__name__)

# Глобальные переменные для таймера
timer_running = False
timer_seconds = 0
timer_thread = None

def timer_worker():
    """Фоновая функция таймера"""
    global timer_running, timer_seconds
    while timer_running and timer_seconds > 0:
        time.sleep(1)
        timer_seconds -= 1
    if timer_seconds == 0 and timer_running:
        timer_running = False
        print("Timer finished!")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>{app_name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 400px; margin: 0 auto; padding: 20px; }}
        .timer {{ background: #f0f0f0; padding: 30px; border-radius: 15px; text-align: center; }}
        .time-display {{ font-size: 48px; font-weight: bold; margin: 20px 0; color: #333; }}
        .controls {{ display: flex; justify-content: center; gap: 10px; margin: 20px 0; }}
        button {{ padding: 12px 24px; font-size: 16px; border: none; border-radius: 8px; cursor: pointer; }}
        .start {{ background: #28a745; color: white; }}
        .stop {{ background: #dc3545; color: white; }}
        .reset {{ background: #6c757d; color: white; }}
        .input-group {{ margin: 20px 0; }}
        input {{ padding: 8px; font-size: 16px; width: 80px; text-align: center; }}
        .status {{ margin-top: 20px; padding: 10px; border-radius: 5px; }}
        .running {{ background: #d4edda; color: #155724; }}
        .stopped {{ background: #f8d7da; color: #721c24; }}
    </style>
</head>
<body>
    <h1>{app_name}</h1>
    <div class="timer">
        <div class="time-display" id="timeDisplay">00:00:00</div>

        <div class="input-group">
            <label>Минуты: <input type="number" id="minutesInput" min="0" max="59" value="0"></label>
            <label>Секунды: <input type="number" id="secondsInput" min="0" max="59" value="30"></label>
        </div>

        <div class="controls">
            <button class="start" onclick="startTimer()">Старт</button>
            <button class="stop" onclick="stopTimer()">Стоп</button>
            <button class="reset" onclick="resetTimer()">Сброс</button>
        </div>

        <div class="status stopped" id="status">Таймер остановлен</div>
    </div>

    <script>
        let timerInterval;
        let isRunning = false;

        function updateDisplay(seconds) {{
            const hours = Math.floor(seconds / 3600);
            const minutes = Math.floor((seconds % 3600) / 60);
            const secs = seconds % 60;

            document.getElementById('timeDisplay').textContent =
                String(hours).padStart(2, '0') + ':' +
                String(minutes).padStart(2, '0') + ':' +
                String(secs).padStart(2, '0');
        }}

        async function startTimer() {{
            if (isRunning) return;

            const minutes = parseInt(document.getElementById('minutesInput').value) || 0;
            const seconds = parseInt(document.getElementById('secondsInput').value) || 0;
            const totalSeconds = minutes * 60 + seconds;

            if (totalSeconds <= 0) {{
                alert('Установите время больше 0');
                return;
            }}

            const response = await fetch('/api/timer/start', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify({{ seconds: totalSeconds }})
            }});

            if (response.ok) {{
                isRunning = true;
                updateStatus(true);
                startLocalTimer(totalSeconds);
            }}
        }}

        function startLocalTimer(totalSeconds) {{
            let currentSeconds = totalSeconds;
            updateDisplay(currentSeconds);

            timerInterval = setInterval(async () => {{
                currentSeconds--;

                if (currentSeconds <= 0) {{
                    clearInterval(timerInterval);
                    isRunning = false;
                    updateStatus(false);
                    updateDisplay(0);
                    alert('Время вышло!');
                    return;
                }}

                updateDisplay(currentSeconds);
            }}, 1000);
        }}

        async function stopTimer() {{
            await fetch('/api/timer/stop', {{ method: 'POST' }});
            clearInterval(timerInterval);
            isRunning = false;
            updateStatus(false);
        }}

        async function resetTimer() {{
            await fetch('/api/timer/reset', {{ method: 'POST' }});
            clearInterval(timerInterval);
            isRunning = false;
            updateStatus(false);
            updateDisplay(0);
        }}

        function updateStatus(running) {{
            const status = document.getElementById('status');
            if (running) {{
                status.textContent = 'Таймер запущен';
                status.className = 'status running';
            }} else {{
                status.textContent = 'Таймер остановлен';
                status.className = 'status stopped';
            }}
        }}

        // Загружаем статус при загрузке страницы
        async function loadStatus() {{
            const response = await fetch('/api/timer/status');
            const data = await response.json();
            isRunning = data.running;
            updateDisplay(data.seconds);
            updateStatus(data.running);
        }}

        loadStatus();
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/timer/start', methods=['POST'])
def start_timer():
    global timer_running, timer_seconds, timer_thread

    data = request.json
    timer_seconds = data.get('seconds', 0)

    if timer_seconds > 0:
        timer_running = True
        timer_thread = threading.Thread(target=timer_worker, daemon=True)
        timer_thread.start()
        return jsonify({'status': 'started', 'seconds': timer_seconds})

    return jsonify({'error': 'Invalid time'}), 400

@app.route('/api/timer/stop', methods=['POST'])
def stop_timer():
    global timer_running
    timer_running = False
    return jsonify({'status': 'stopped'})

@app.route('/api/timer/reset', methods=['POST'])
def reset_timer():
    global timer_running, timer_seconds
    timer_running = False
    timer_seconds = 0
    return jsonify({'status': 'reset'})

@app.route('/api/timer/status')
def get_timer_status():
    global timer_running, timer_seconds
    return jsonify({
        'running': timer_running,
        'seconds': timer_seconds
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5003)
'''

        requirements = """Flask==2.3.3
Werkzeug==2.3.7
"""

        readme = f"""# {app_name}

Таймер и секундомер - мини-приложение APAS.

## Запуск
```bash
pip install -r requirements.txt
python app.py
```

Приложение будет доступно на http://localhost:5003
"""

        with open(os.path.join(app_dir, 'app.py'), 'w', encoding='utf-8') as f:
            f.write(app_code)

        with open(os.path.join(app_dir, 'requirements.txt'), 'w', encoding='utf-8') as f:
            f.write(requirements)

        with open(os.path.join(app_dir, 'README.md'), 'w', encoding='utf-8') as f:
            f.write(readme)

        return app_dir

    def get_available_templates(self) -> List[str]:
        """Получить список доступных шаблонов"""
        return [
            'calculator',
            'notes',
            'timer',
            'weather',
            'todo'
        ]

    def analyze_request(self, user_request: str) -> Dict:
        """Анализировать запрос пользователя и предложить подходящий шаблон"""
        request_lower = user_request.lower()

        # Простой анализ ключевых слов
        if any(word in request_lower for word in ['калькулятор', 'calculator', 'вычисл', 'считать']):
            return {
                'template': 'calculator',
                'confidence': 0.9,
                'description': 'Калькулятор для математических вычислений'
            }
        elif any(word in request_lower for word in ['заметки', 'notes', 'записки', 'блокнот']):
            return {
                'template': 'notes',
                'confidence': 0.8,
                'description': 'Приложение для создания и хранения заметок'
            }
        elif any(word in request_lower for word in ['таймер', 'timer', 'время', 'секундомер']):
            return {
                'template': 'timer',
                'confidence': 0.7,
                'description': 'Таймер и секундомер'
            }
        elif any(word in request_lower for word in ['погода', 'weather', 'температура']):
            return {
                'template': 'weather',
                'confidence': 0.8,
                'description': 'Приложение для просмотра погоды'
            }
        elif any(word in request_lower for word in ['список', 'todo', 'задачи', 'дела']):
            return {
                'template': 'todo',
                'confidence': 0.7,
                'description': 'Список дел и задач'
            }
        else:
            return {
                'template': 'custom',
                'confidence': 0.3,
                'description': 'Пользовательское приложение (требует дополнительной настройки)'
            }