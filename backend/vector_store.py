import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

import hashlib
import chromadb
from sentence_transformers import SentenceTransformer
from backend.config import EMBEDDING_MODEL, VECTOR_DB_PATH


class VectorStore:
    """基于 ChromaDB 的向量存储"""

    def __init__(self, collection_name: str = "campus_docs"):
        self.client = chromadb.PersistentClient(path=VECTOR_DB_PATH)
        self.collection = self.client.get_or_create_collection(name=collection_name)
        # 本地 Embedding 模型（首次会自动从 HuggingFace 下载）
        print(f"🔄 正在加载 Embedding 模型: {EMBEDDING_MODEL} ...")
        self.embedding_model = SentenceTransformer(EMBEDDING_MODEL)
        print("✅ Embedding 模型加载完成")

    def add_documents(self, documents: list, ids: list = None, metadatas: list = None):
        """向知识库中添加文档片段"""
        if ids is None:
            metadata_values = metadatas or [{} for _ in documents]
            ids = [
                hashlib.sha256(
                    f"{metadata.get('source', '')}:{metadata.get('chunk_index', '')}:{document}".encode("utf-8")
                ).hexdigest()
                for document, metadata in zip(documents, metadata_values)
            ]

        embeddings = self.embedding_model.encode(documents, show_progress_bar=True).tolist()
        self.collection.upsert(
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
