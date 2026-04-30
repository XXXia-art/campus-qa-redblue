"""
校园智能问答机器人 - 命令行版本
直接运行：python cli.py
"""

import os
import sys
from backend.config import check_api_key
from backend.rag_engine import RAGEngine


def print_banner():
    print("=" * 50)
    print("🎓 校园智能问答机器人 (CLI 版)")
    print("基于 Kimi API + RAG 检索增强")
    print("=" * 50)
    print()


def main():
    if not check_api_key():
        print("❌ 错误：未检测到 Kimi API Key！")
        print("请复制 .env.example 为 .env，并填入你的 API Key")
        sys.exit(1)

    print_banner()
    rag = RAGEngine()

    # 自动加载 data 目录
    data_dir = "./data"
    if os.path.exists(data_dir):
        print(f"📚 正在加载 {data_dir} 目录下的文档...")
        rag.ingest_directory(data_dir)
        print(f"✅ 知识库就绪，共 {rag.vector_store.count()} 个片段\n")
    else:
        print("⚠️ 未找到 data 目录，知识库为空\n")

    print("💡 提示：输入 'exit' 或 'quit' 退出\n")

    while True:
        try:
            question = input("你 👤 > ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n👋 再见！")
            break

        if question.lower() in ('exit', 'quit', '退出', 'q'):
            print("👋 再见！")
            break
        if not question:
            continue

        print("🤖 思考中...")
        try:
            result = rag.ask(question)
        except Exception as e:
            print(f"❌ 错误: {e}\n")
            continue

        if result.get("blocked"):
            print(f"\n🛡️ 助手 > {result['answer']}\n")
        else:
            print(f"\n💬 助手 > {result['answer']}\n")
            if result['sources']:
                print(f"   📄 参考来源: {', '.join(result['sources'])}\n")


if __name__ == "__main__":
    main()
