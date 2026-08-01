import requests
from src.config import YANDEX_API_KEY

# YandexGPT API configuration
YANDEX_GPT_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

def get_yandex_headers():
    """Get headers for YandexGPT API"""
    return {
        "Authorization": f"Api-Key {YANDEX_API_KEY}",
        "Content-Type": "application/json"
    }

# Available YandexGPT models
YANDEX_MODELS = {
    # YandexGPT 4 models
    'yandex_gpt_4_lite': {
        'name': 'YandexGPT 4 Lite',
        'description': 'Легкая и быстрая модель YandexGPT 4 для простых задач и быстрого ответа',
        'provider': 'yandex',
        'model_uri': 'gpt://b1guaiq8otdbv7m477re/yandexgpt-4-lite/latest',
        'category': 'yandex_4'
    },
    # YandexGPT 5 models
    'yandex_gpt_5_lite': {
        'name': 'YandexGPT 5 Lite',
        'description': 'Быстрая и экономичная модель YandexGPT 5 для простых задач',
        'provider': 'yandex',
        'model_uri': 'gpt://b1guaiq8otdbv7m477re/yandexgpt-5-lite/latest',
        'category': 'yandex_5'
    },
    'yandex_gpt_5_pro': {
        'name': 'YandexGPT 5 Pro',
        'description': 'Мощная модель YandexGPT 5 для сложных задач с улучшенным пониманием контекста',
        'provider': 'yandex',
        'model_uri': 'gpt://b1guaiq8otdbv7m477re/yandexgpt-5-pro/latest',
        'category': 'yandex_5'
    },
    'yandex_gpt_5_1_pro': {
        'name': 'YandexGPT 5.1 Pro',
        'description': 'Улучшенная версия YandexGPT 5.1 Pro с повышенным качеством и пониманием контекста',
        'provider': 'yandex',
        'model_uri': 'gpt://b1guaiq8otdbv7m477re/yandexgpt-5.1/latest',
        'category': 'yandex_5'
    },
}

async def generate_yandex_response(model_config, system_prompt, user_message):
    """Generate response using YandexGPT API"""
    try:
        headers = get_yandex_headers()

        # Prepare the request payload
        payload = {
            "modelUri": model_config['model_uri'],
            "completionOptions": {
                "stream": False,
                "temperature": 0.6,
                "maxTokens": 2000
            },
            "messages": [
                {
                    "role": "system",
                    "text": system_prompt
                },
                {
                    "role": "user",
                    "text": user_message
                }
            ]
        }

        response = requests.post(YANDEX_GPT_URL, headers=headers, json=payload)
        response.raise_for_status()

        result = response.json()
        return result['result']['alternatives'][0]['message']['text']

    except Exception as e:
        raise Exception(f"Error with {model_config['name']}: {str(e)}")

def get_available_yandex_models():
    """Get all available YandexGPT models"""
    return YANDEX_MODELS