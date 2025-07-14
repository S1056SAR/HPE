import os
from dotenv import load_dotenv

load_dotenv()

CHROMA_PERSIST_DIRECTORY = os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_db")

SCRAPE_DELAY = float(os.getenv("SCRAPE_DELAY", "1.0"))  
USER_AGENT = os.getenv("USER_AGENT", "NetworkToolsIntegrationBot/1.0")

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-mpnet-base-v2")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "Your Groq API key")  # Your Groq API key
GROQ_MODEL = os.getenv("GROQ_MODEL", "deepseek-r1-distill-llama-70b")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


UPDATE_CHECK_INTERVAL = int(os.getenv("UPDATE_CHECK_INTERVAL", "24")) 

ENABLE_WEB_SEARCH = os.getenv("ENABLE_WEB_SEARCH", "True").lower() == "true"
MAX_SEARCH_RESULTS = int(os.getenv("MAX_SEARCH_RESULTS", "5"))

# Web search rate limiting
WEB_SEARCH_MIN_DELAY = float(os.getenv("WEB_SEARCH_MIN_DELAY", "2.0"))
WEB_SEARCH_MAX_DELAY = float(os.getenv("WEB_SEARCH_MAX_DELAY", "30.0"))
WEB_SEARCH_CACHE_TTL = int(os.getenv("WEB_SEARCH_CACHE_TTL", "3600"))  # 1 hour default
