import google.generativeai as genai
from src.config import GEMINI_API_KEY

# Configure Gemini API lazily
gemini_configured = False

def configure_gemini():
    """Configure Gemini API if not already configured"""
    global gemini_configured
    if not gemini_configured:
        genai.configure(api_key=GEMINI_API_KEY)
        gemini_configured = True

# Available Gemini models
GEMINI_MODELS = {
    # Gemini 2.0 models
    'gemini_2_0_flash_exp': {
        'name': 'Gemini 2.0 Flash Exp',
        'description': 'Экспериментальная версия Gemini 2.0 Flash',
        'provider': 'gemini',
        'model_id': 'gemini-2.0-flash-exp',
        'category': 'gemini_2_0'
    },
    'gemini_2_0_flash_lite': {
        'name': 'Gemini 2.0 Flash Lite',
        'description': 'Легкая версия Gemini 2.0 Flash',
        'provider': 'gemini',
        'model_id': 'gemini-2.0-flash-lite',
        'category': 'gemini_2_0'
    },
    'gemini_2_0_flash': {
        'name': 'Gemini 2.0 Flash',
        'description': 'Стандартная версия Gemini 2.0 Flash',
        'provider': 'gemini',
        'model_id': 'gemini-2.0-flash',
        'category': 'gemini_2_0'
    },
    # Gemini 2.5 models
    'gemini_2_5_flash_lite': {
        'name': 'Gemini 2.5 Flash Lite',
        'description': 'Легкая версия Gemini 2.5 Flash',
        'provider': 'gemini',
        'model_id': 'gemini-2.5-flash-lite',
        'category': 'gemini_2_5'
    },
    'gemini_2_5_flash': {
        'name': 'Gemini 2.5 Flash',
        'description': 'Стандартная версия Gemini 2.5 Flash',
        'provider': 'gemini',
        'model_id': 'gemini-2.5-flash',
        'category': 'gemini_2_5'
    },
    'gemini_2_5_pro': {
        'name': 'Gemini 2.5 Pro',
        'description': 'Профессиональная версия Gemini 2.5',
        'provider': 'gemini',
        'model_id': 'gemini-2.5-pro',
        'category': 'gemini_2_5'
    },
}

async def generate_gemini_response(model_config, system_prompt, user_message):
    """Generate response using Gemini API"""
    try:
        configure_gemini()
        model = genai.GenerativeModel(model_config['model_id'])
        chat = model.start_chat(history=[])

        full_prompt = f"System: {system_prompt}\n\nUser: {user_message}"
        response = chat.send_message(full_prompt)

        return response.text
    except Exception as e:
        raise Exception(f"Error with {model_config['name']}: {str(e)}")

def get_available_gemini_models():
    """Get all available Gemini models"""
    return GEMINI_MODELS