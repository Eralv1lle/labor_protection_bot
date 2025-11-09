import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ADMIN_TELEGRAM_IDS = [int(id_) for id_ in os.getenv('ADMIN_TELEGRAM_IDS', '').split(',') if id_]

# GigaChat API
GIGACHAT_TOKEN = os.getenv('GIGACHAT_TOKEN')
GIGACHAT_SCOPE = os.getenv('GIGACHAT_SCOPE', 'GIGACHAT_API_PERS')

# Flask
FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key')
FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))
FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'

# Database
DATABASE_PATH = os.getenv('DATABASE_PATH', 'database.db')

# Mini App
MINI_APP_URL = os.getenv('MINI_APP_URL', 'http://localhost:5000')

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOCS_DIR = os.path.join(BASE_DIR, 'docs')
EMBEDDINGS_DIR = os.path.join(BASE_DIR, 'embeddings')

# RAG Settings
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
TOP_K_RESULTS = 5

# Create directories if not exist
os.makedirs(DOCS_DIR, exist_ok=True)
os.makedirs(EMBEDDINGS_DIR, exist_ok=True)
