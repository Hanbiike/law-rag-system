import os
from dotenv import load_dotenv

# Загрузка переменных окружения из .env файла
load_dotenv()

AZURE_ENDPOINT = os.environ.get("AZURE_ENDPOINT")
AZURE_OPENAI_API_KEY = os.environ.get("AZURE_OPENAI_API_KEY")
AZURE_DEPLOYMENT = os.environ.get("AZURE_DEPLOYMENT")
AZURE_API_VERSION = os.environ.get("AZURE_API_VERSION")

AZURE_ENDPOINT_NANO = os.environ.get("AZURE_ENDPOINT_NANO")
AZURE_OPENAI_API_KEY_NANO = os.environ.get("AZURE_OPENAI_API_KEY_NANO")
AZURE_DEPLOYMENT_NANO = os.environ.get("AZURE_DEPLOYMENT_NANO")
AZURE_API_VERSION_NANO = os.environ.get("AZURE_API_VERSION_NANO")