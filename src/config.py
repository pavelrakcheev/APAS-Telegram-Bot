"""
Configuration module for loading environment variables.
Uses python-dotenv to load .env file.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Keys
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
YANDEX_API_KEY = os.getenv('YANDEX_API_KEY')

# Other configuration
TELEGRAM_ID = os.getenv('TELEGRAM_ID', '0')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', '')
GOOGLE_CLOUD_PROJECT = os.getenv('GOOGLE_CLOUD_PROJECT', 'your-project-id')
GOOGLE_CLOUD_LOCATION = os.getenv('GOOGLE_CLOUD_LOCATION', 'us-central1')
YANDEX_MUSIC_ADMIN_TOKEN = os.getenv('YANDEX_MUSIC_ADMIN_TOKEN')

# Sentry configuration
SENTRY_DSN = os.getenv('SENTRY_DSN')
SENTRY_ENVIRONMENT = os.getenv('SENTRY_ENVIRONMENT', 'production')
SENTRY_RELEASE = os.getenv('SENTRY_RELEASE', 'apas@0.1.0-canary')

# Validate required keys
REQUIRED_KEYS = ['TELEGRAM_BOT_TOKEN', 'GROQ_API_KEY']
missing_keys = [key for key in REQUIRED_KEYS if not os.getenv(key)]
if missing_keys:
    raise ValueError(f"Missing required environment variables: {', '.join(missing_keys)}")

# Optional keys (with defaults if needed)
# Add any other config variables here