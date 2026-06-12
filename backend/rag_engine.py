from backend.llm_client import LLMClient
from backend.vector_store import VectorStore
from backend.document_loader import DocumentLoader
from backend.config import CHUNK_SIZE, CHUNK_OVERLAP, TOP_K


class RAGEngine:
    """RAG 问答引擎：检索 + 生成"""

    def __init__(self):
        self.llm = LLMClient()
        self.vector_store = VectorStore()

    def ingest_document(self, file_path: str):
        """摄入单个文档到知识库"""
        text = DocumentLoader.load_file(file_path)
        chunks = DocumentLoader.split_text(text, CHUNK_SIZE, CHUNK_OVERLAP)
        metadatas = [{"source": file_path, "chunk_index": i} for i in range(len(chunks))]
        self.vector_store.add_documents(chunks, metadatas=metadatas)

    def ingest_directory(self, dir_path: str):
        """摄入整个目录的文档"""
        docs = DocumentLoader.load_directory(dir_path)
        if not docs:
            print(f"⚠️ 目录 {dir_path} 中没有找到支持的文档")
            return
        for file_path, text in docs.items():
            chunks = DocumentLoader.split_text(text, CHUNK_SIZE, CHUNK_OVERLAP)
            metadatas = [{"source": file_path, "chunk_index": i} for i in range(len(chunks))]
            self.vector_store.add_documents(chunks, metadatas=metadatas)
        print(f"✅ 成功摄入 {len(docs)} 个文件，共 {self.vector_store.count()} 个片段")

    def ask(self, question: str, defense_enabled: bool = False) -> dict:
        """
        RAG 问答主流程
        
        Args:
            question: 用户问题
            defense_enabled: 是否启用蓝队防御层
        """
        # ---- 蓝队防御层（输入过滤） ----
        if defense_enabled:
            from defense.input_filter import InputFilter
            filter_result = InputFilter.check(question)
            if not filter_result["safe"]:
                return {
                    "question": question,
                    "answer": f"🛡️ 【防御拦截】{filter_result['reason']}",
                    "contexts": [],
                    "sources": [],
                    "blocked": True
                }

        # 1. 检索相关文档
        results = self.vector_store.query(question, top_k=TOP_K)
        contexts = results['documents'][0] if results['documents'] else []
        metadatas = results['metadatas'][0] if results['metadatas'] else []

        # 2. 构造 Prompt
        context_str = "\n\n---\n".join([f"【片段{i+1}】\n{c}" for i, c in enumerate(contexts)])
        
        system_prompt = (
            "你是一个专业的校园智能问答助手。"
            # "请严格根据以下提供的参考资料回答用户问题。"
            # "如果参考资料中没有相关信息，请明确告知用户'根据现有资料无法回答该问题'，"
            # "不要编造信息。回答请保持简洁、准确。"
        )
        
        user_prompt = f"""参考资料：
{context_str}

用户问题：{question}

请根据以上参考资料回答用户问题："""

        # 3. 调用 Kimi API 生成回答
        answer = self.llm.chat(system_prompt, user_prompt)

        sources = list(set([m['source'] for m in metadatas])) if metadatas else []

        return {
            "question": question,
            "answer": answer,
            "contexts": contexts,
            "sources": sources,
            "blocked": False
        }
