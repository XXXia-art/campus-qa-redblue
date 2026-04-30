import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# Kimi API 配置
KIMI_API_KEY = os.getenv("KIMI_API_KEY", "")
KIMI_BASE_URL = os.getenv("KIMI_BASE_URL", "https://api.moonshot.cn/v1")
KIMI_MODEL = os.getenv("KIMI_MODEL", "moonshot-v1-8k")

# Embedding & RAG 配置
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-zh-v1.5")
VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH", "./chroma_db")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))
TOP_K = int(os.getenv("TOP_K", "3"))


def check_api_key():
    """检查 API Key 是否已配置"""
    if not KIMI_API_KEY or KIMI_API_KEY == "sk-your-api-key-here":
        return False
    return True
