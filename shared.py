import json
import os
import time
from datetime import datetime
from groq import Groq
from src.config import GROQ_API_KEY, TELEGRAM_ID, ADMIN_PASSWORD

# Constants
USERS_DATA_FILE = 'data/users_data.json'
ISS_PLAY_ACCOUNTS_FILE = 'data/iss_play_accounts.json'
CHATS_DIR = 'Chats'

# Ensure chats directory exists
if not os.path.exists(CHATS_DIR):
    os.makedirs(CHATS_DIR)

# Load users data
def load_users_data():
    if os.path.exists(USERS_DATA_FILE):
        try:
            with open(USERS_DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

# Save users data
def save_users_data(users_data):
    try:
        with open(USERS_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(users_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving users data: {e}")

# Reload users data from file
def reload_users_data():
    global users_data
    users_data = load_users_data()

# Check if username is available
def is_username_available(username: str, current_user_id: int = None) -> bool:
    """Check if username is available for use"""
    for user_id_str, user_data in users_data.items():
        if user_data.get('username') == username:
            # If current_user_id is provided, allow keeping the same username
            if current_user_id is not None and str(current_user_id) == user_id_str:
                continue
            return False
    return True

# Find user_id by username
def find_user_id_by_username(username: str) -> str:
    """Find user_id by username, return user_id string or None if not found"""
    for user_id_str, user_data in users_data.items():
        if user_data.get('username') == username:
            return user_id_str
    return None

# Global users data storage
users_data = load_users_data()

# ISS Play accounts storage
iss_play_accounts = {}

def load_iss_play_accounts():
    global iss_play_accounts
    if os.path.exists(ISS_PLAY_ACCOUNTS_FILE):
        try:
            with open(ISS_PLAY_ACCOUNTS_FILE, 'r', encoding='utf-8') as f:
                iss_play_accounts = json.load(f)
        except:
            iss_play_accounts = {}
    else:
        iss_play_accounts = {}

def save_iss_play_accounts():
    try:
        with open(ISS_PLAY_ACCOUNTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(iss_play_accounts, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving ISS Play accounts: {e}")

# Load ISS Play accounts on startup
load_iss_play_accounts()

# Admin access check
def check_admin_access(user_id: int, password: str = None) -> bool:
    """Check if user has admin access using admin credentials"""
    
    if user_id != int(TELEGRAM_ID):
        return False
    
    if password and password != ADMIN_PASSWORD:
        return False
        
    return True

# Generate ISS Play nicknames using Groq
def generate_iss_play_nicknames(user_data):
    """Generate 3 nickname suggestions using user's profile data"""
    try:
        # Get user info
        name = user_data.get('name', '')
        username = user_data.get('username', '')
        
        # Create prompt
        prompt = f"Generate 3 creative gaming nicknames based on the user's name '{name}' and username '{username}'. Nicknames should be 5-15 characters long, contain only Latin letters and numbers, be cool and unique for gaming. Return only 3 nicknames separated by commas, no other text."
        
        # Call Groq API
        client = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=50
        )
        
        nicknames = response.choices[0].message.content.strip().split(',')
        nicknames = [n.strip() for n in nicknames if n.strip()]
        
        # Ensure we have 3 nicknames, fallback if needed
        while len(nicknames) < 3:
            nicknames.append(f"Player{len(nicknames)+1}")
        
        return nicknames[:3]
    except Exception as e:
        print(f"Error generating nicknames: {e}")
        return ["Gamer1", "ProPlayer", "EliteGamer"]

# Format date from timestamp
def format_registration_date(timestamp_str):
    try:
        timestamp = int(timestamp_str)
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime("%d.%m.%Y")
    except (ValueError, TypeError):
        return timestamp_str  # Return as-is if conversion fails

# Load user data into context
def load_user_data(context, user_id: int):
    if not hasattr(context, 'user_data') or context.user_data is None:
        context.user_data = {}
    
    user_id_str = str(user_id)
    if user_id_str in users_data:
        # Load saved data into context
        context.user_data.update(users_data[user_id_str])
        
        # Auto-fix: If user is registered but still has guest_mode flag, remove it
        if context.user_data.get('setup_completed', False) and context.user_data.get('guest_mode', False):
            context.user_data.pop('guest_mode', None)
            # Save the corrected data
            users_data[user_id_str] = dict(context.user_data)
            save_users_data(users_data)
    
    # Always ensure user_data has the latest saved state
    users_data[user_id_str] = dict(context.user_data)
    return context.user_data

# Save user data from context
def save_user_data(context, user_id: int):
    user_id_str = str(user_id)
    users_data[user_id_str] = dict(context.user_data)
    save_users_data(users_data)

# System prompt for AI
def get_system_prompt(user_data):
    base_prompt = ("Ты система APAS - Адаптивная Аналитическая Предиктивная Система на базе ASAD - Продвинутой Системы Анализа и принятия Решений. "
                   "Общайся кратко, по делу и исключительно фактами и достоверной информацией.")

    # Add user personalization if available
    user_name = user_data.get('name')
    user_age = user_data.get('age')
    user_city = user_data.get('city')

    if user_name:
        base_prompt += f" Пользователя зовут {user_name}."
    if user_age:
        base_prompt += f" Пользователю {user_age} лет."
    if user_city:
        base_prompt += f" Пользователь из города {user_city}."

    # Add instruction for command recognition
    base_prompt += (" Если пользователь спрашивает о статусе аккаунта, правах доступа, административных правах или уровне доступа, "
                   "автоматически активируй соответствующую команду вместо генерации ответа.")

    return base_prompt