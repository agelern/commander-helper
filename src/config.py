import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Ollama configuration
OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'mistral')

# Ensure the host is properly formatted
if not OLLAMA_HOST.startswith(('http://', 'https://')):
    OLLAMA_HOST = f'http://{OLLAMA_HOST}' 