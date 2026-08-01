from groq import Groq
import os

# Initialize Groq client lazily
groq_client = None

def get_groq_client():
    """Get or create Groq client"""
    global groq_client
    if groq_client is None:
        groq_client = Groq(api_key=GROQ_API_KEY)
    return groq_client

from src.config import GROQ_API_KEY
GROQ_MODELS = {
    # OpenAI models
    'groq_gpt_oss_20b': {
        'name': 'GPT OSS 20B',
        'description': 'OpenAI GPT модель 20B параметров',
        'provider': 'groq',
        'model_id': 'openai/gpt-oss-20b',
        'category': 'groq_openai'
    },
    'groq_gpt_oss_120b': {
        'name': 'GPT OSS 120B',
        'description': 'OpenAI GPT модель 120B параметров (рекомендуется)',
        'provider': 'groq',
        'model_id': 'openai/gpt-oss-120b',
        'category': 'groq_openai'
    },
    # Moonshot AI models
    'groq_kimi_k2_instruct': {
        'name': 'Kimi K2 Instruct',
        'description': 'Moonshot AI Kimi модель для инструкций',
        'provider': 'groq',
        'model_id': 'kimi-k2-instruct-0905',
        'category': 'groq_moonshot'
    },
    # Qwen models
    'groq_qwen3_32b': {
        'name': 'Qwen3 32B',
        'description': 'Qwen модель 32B параметров',
        'provider': 'groq',
        'model_id': 'qwen3-32b',
        'category': 'groq_qwen'
    },
    # Meta Llama 3 models
    'groq_llama_3_1_8b_instant': {
        'name': 'Llama 3.1 8B Instant',
        'description': 'Meta Llama 3.1 модель 8B параметров (быстрая)',
        'provider': 'groq',
        'model_id': 'llama-3.1-8b-instant',
        'category': 'groq_llama3'
    },
    'groq_llama_3_3_70b_versatile': {
        'name': 'Llama 3.3 70B Versatile',
        'description': 'Meta Llama 3.3 модель 70B параметров (универсальная)',
        'provider': 'groq',
        'model_id': 'llama-3.3-70b-versatile',
        'category': 'groq_llama3'
    },
    # Meta Llama 4 models
    'groq_llama_4_maverick': {
        'name': 'Llama 4 Maverick 17B',
        'description': 'Meta Llama 4 Maverick модель 17B параметров',
        'provider': 'groq',
        'model_id': 'llama-4-maverick-17b-128e-instruct',
        'category': 'groq_llama4'
    },
    'groq_llama_4_scout': {
        'name': 'Llama 4 Scout 17B',
        'description': 'Meta Llama 4 Scout модель 17B параметров',
        'provider': 'groq',
        'model_id': 'llama-4-scout-17b-16e-instruct',
        'category': 'groq_llama4'
    },
}

async def generate_groq_response(model_config, system_prompt, user_message, streaming_enabled=True):
    """Generate response using Groq API"""
    try:
        client = get_groq_client()
        response = client.chat.completions.create(
            model=model_config['model_id'],
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            stream=streaming_enabled
        )

        if streaming_enabled:
            return response  # Return streaming response for async iteration
        else:
            return response.choices[0].message.content
    except Exception as e:
        raise Exception(f"Error with {model_config['name']}: {str(e)}")

def get_available_groq_models():
    """Get all available Groq models"""
    return GROQ_MODELS