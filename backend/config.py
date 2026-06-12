import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# LLM API 配置（兼容 OpenAI / Anthropic / Mimo 等格式）
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.moonshot.cn/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "moonshot-v1-8k")

# Embedding & RAG 配置
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-zh-v1.5")
VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH", "./chroma_db")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))
TOP_K = int(os.getenv("TOP_K", "3"))


def check_api_key():
    """检查 API Key 是否已配置"""
    if not LLM_API_KEY or LLM_API_KEY in ("sk-your-api-key-here", "tp-your-api-key-here", "your-api-key"):
        return False
    return True
