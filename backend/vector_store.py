import os

# HuggingFace 国内镜像配置
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

import chromadb
from sentence_transformers import SentenceTransformer
from backend.config import EMBEDDING_MODEL, VECTOR_DB_PATH


def _load_embedding_model(model_name: str):
    """加载 Embedding 模型，优先本地缓存，其次自动下载"""
    # 1. 优先从项目本地 models 目录加载（手动下载放这里）
    local_path = os.path.join("models", model_name.replace("/", os.sep))
    if os.path.exists(local_path):
        print(f"📦 从本地加载模型: {local_path}")
        return SentenceTransformer(local_path)

    # 2. 尝试从本地 HuggingFace 缓存加载
    try:
        return SentenceTransformer(model_name, local_files_only=True)
    except Exception:
        pass

    # 3. 尝试从 hf-mirror 自动下载
    print(f"🔄 尝试从 hf-mirror.com 下载模型: {model_name} ...")
    try:
        from huggingface_hub import snapshot_download
        cache_dir = os.path.expanduser("~/.cache/huggingface/hub")
        model_path = snapshot_download(
            repo_id=model_name,
            cache_dir=cache_dir,
            local_files_only=False,
            endpoint="https://hf-mirror.com",
        )
        return SentenceTransformer(model_path)
    except Exception as e:
        raise RuntimeError(
            f"模型加载失败。请手动从 https://hf-mirror.com/{model_name} 下载所有文件，"
            f"放到项目目录的 models/{model_name.replace('/', os.sep)}/ 下。\n"
            f"错误: {e}"
        )


class VectorStore:
    """基于 ChromaDB 的向量存储"""

    def __init__(self, collection_name: str = "campus_docs"):
        self.client = chromadb.PersistentClient(path=VECTOR_DB_PATH)
        self.collection = self.client.get_or_create_collection(name=collection_name)
        print(f"🔄 正在加载 Embedding 模型: {EMBEDDING_MODEL} ...")
        self.embedding_model = _load_embedding_model(EMBEDDING_MODEL)
        print("✅ Embedding 模型加载完成")

    def add_documents(self, documents: list, ids: list = None, metadatas: list = None):
        """向知识库中添加文档片段"""
        if ids is None:
            start_id = self.collection.count()
            ids = [str(start_id + i) for i in range(len(documents))]

        embeddings = self.embedding_model.encode(documents, show_progress_bar=True).tolist()
        self.collection.add(
            documents=documents,
            embeddings=embeddings,
            ids=ids,
            metadatas=metadatas
        )

    def query(self, query_text: str, top_k: int = 3):
        """检索与问题最相关的文档片段"""
        embedding = self.embedding_model.encode([query_text]).tolist()
        results = self.collection.query(
            query_embeddings=embedding,
            n_results=top_k
        )
        return results

    def count(self):
        """返回当前知识库中的文档片段数量"""
        return self.collection.count()

    def clear(self):
        """清空知识库"""
        name = self.collection.name
        self.client.delete_collection(name)
        self.collection = self.client.get_or_create_collection(name=name)
