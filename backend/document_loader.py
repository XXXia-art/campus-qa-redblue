import re
from pathlib import Path


class DocumentLoader:
    """文档加载与切分器"""

    @staticmethod
    def load_file(file_path: str) -> str:
        """加载单个文件（支持 txt / md / pdf）"""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        suffix = path.suffix.lower()
        if suffix in ('.txt', '.md'):
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        elif suffix == '.pdf':
            try:
                import PyPDF2
                text = ""
                with open(path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    for page in reader.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                return text
            except Exception as e:
                raise RuntimeError(f"PDF 解析失败: {e}")
        else:
            raise ValueError(f"不支持的文件格式: {suffix}（仅支持 txt/md/pdf）")

    @staticmethod
    def load_directory(dir_path: str) -> dict:
        """加载目录下所有支持的文件，返回 {文件路径: 内容}"""
        results = {}
        path = Path(dir_path)
        for file_path in path.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in ('.txt', '.md', '.pdf'):
                try:
                    results[str(file_path)] = DocumentLoader.load_file(str(file_path))
                except Exception as e:
                    print(f"⚠️ 加载文件失败 {file_path}: {e}")
        return results

    @staticmethod
    def split_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list:
        """
        按语义段落切分文本，尽量保证段落完整性
        """
        # 先按自然段拆分
        paragraphs = re.split(r'\n\s*\n', text)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]

        chunks = []
        current_chunk = ""

        for para in paragraphs:
            # 如果单个段落就超过 chunk_size，则按句子进一步切分
            if len(para) > chunk_size:
                sentences = re.split(r'(?<=[。！？.!?])\s+', para)
                for sent in sentences:
                    if len(current_chunk) + len(sent) > chunk_size:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                        current_chunk = sent
                    else:
                        current_chunk += sent
            else:
                if len(current_chunk) + len(para) > chunk_size:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = para
                else:
                    if current_chunk:
                        current_chunk += "\n" + para
                    else:
                        current_chunk = para

        if current_chunk:
            chunks.append(current_chunk.strip())

        # 添加 overlap 逻辑
        if overlap > 0 and len(chunks) > 1:
            final_chunks = []
            for i, chunk in enumerate(chunks):
                if i > 0:
                    prev_tail = chunks[i - 1][-overlap:]
                    chunk = prev_tail + chunk
                final_chunks.append(chunk)
            return final_chunks

        return chunks
