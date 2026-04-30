"""
校园智能问答机器人 - Web 界面
使用 Streamlit 启动：streamlit run app.py
"""

import os
import sys
import streamlit as st

# 必须放在最前面
st.set_page_config(page_title="AI智能体安全攻防 - 校园问答机器人", layout="wide")

from backend.config import check_api_key
from backend.rag_engine import RAGEngine

# ========== 页面样式 ==========
st.markdown("""
<style>
.chat-box { border-radius: 10px; padding: 15px; margin: 10px 0; }
.user-box { background-color: #e3f2fd; }
.assistant-box { background-color: #f3e5f5; }
.attack-box { background-color: #5c1a1a; color: #ffffff; border: 1px solid #ef5350; padding: 10px; border-radius: 5px; }
.defense-box { background-color: #1a472a; color: #ffffff; border: 1px solid #66bb6a; padding: 10px; border-radius: 5px; }
</style>
""", unsafe_allow_html=True)

# ========== 初始化 ==========
if 'rag' not in st.session_state:
    if not check_api_key():
        st.error("🚨 未检测到 Kimi API Key！请先将 `.env.example` 复制为 `.env`，并填入你的 API Key")
        st.stop()
    st.session_state.rag = RAGEngine()
    st.session_state.history = []
    st.session_state.attack_mode = False
    st.session_state.defense_mode = False
    st.session_state.selected_payload = "手动输入"
    
    # 启动时自动加载 data 目录下的校园数据
    data_dir = "./data"
    if os.path.exists(data_dir) and st.session_state.rag.vector_store.count() == 0:
        with st.spinner("📚 正在自动加载校园数据到知识库..."):
            st.session_state.rag.ingest_directory(data_dir)

rag = st.session_state.rag

# ========== 侧边栏 ==========
with st.sidebar:
    st.title("⚙️ 控制台")
    
    # API 状态
    if check_api_key():
        st.success("✅ Kimi API 已配置")
    else:
        st.error("❌ Kimi API 未配置")
    
    st.divider()
    
    # 知识库管理
    st.header("📚 知识库管理")
    uploaded_files = st.file_uploader(
        "上传校园文档", 
        accept_multiple_files=True, 
        type=['txt', 'md', 'pdf']
    )
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📥 加入知识库"):
            if uploaded_files:
                os.makedirs("./temp_uploads", exist_ok=True)
                for file in uploaded_files:
                    save_path = os.path.join("./temp_uploads", file.name)
                    with open(save_path, "wb") as f:
                        f.write(file.getbuffer())
                    rag.ingest_document(save_path)
                st.success(f"已处理 {len(uploaded_files)} 个文件")
                st.rerun()
            else:
                st.warning("请先上传文件")
    
    with col2:
        if st.button("🗑️ 清空"):
            rag.vector_store.clear()
            st.success("知识库已清空")
            st.rerun()
    
    st.info(f"当前知识库片段数: **{rag.vector_store.count()}**")
    
    # 加载示例数据
    st.divider()
    if st.button("📂 加载示例校园数据"):
        sample_dir = "./data"
        if os.path.exists(sample_dir):
            rag.ingest_directory(sample_dir)
            st.success("示例数据加载完成")
            st.rerun()
        else:
            st.error("示例数据目录不存在")
    
    st.divider()
    
    # 红蓝队模式
    st.header("🎯 攻防模式")
    
    attack_mode = st.toggle("🔴 红队攻击模式", value=st.session_state.attack_mode)
    st.session_state.attack_mode = attack_mode
    
    if attack_mode:
        st.markdown("<div class='attack-box'>攻击模式已开启，可直接输入注入载荷测试</div>", unsafe_allow_html=True)
        from attack.prompt_injection import PromptInjection
        payloads = PromptInjection.list_payloads()
        payload_names = ["手动输入"] + list(payloads.keys())
        selected = st.selectbox("快速选择攻击载荷", payload_names, 
                                index=payload_names.index(st.session_state.selected_payload))
        st.session_state.selected_payload = selected
        if selected != "手动输入":
            st.text_area("载荷预览", payloads[selected], height=100)
    
    defense_mode = st.toggle("🔵 蓝队防御模式", value=st.session_state.defense_mode)
    st.session_state.defense_mode = defense_mode
    
    if defense_mode:
        st.markdown("<div class='defense-box'>防御模式已开启，可疑输入将被拦截</div>", unsafe_allow_html=True)

# ========== 主界面 ==========
st.title("🎓 校园智能问答机器人")
st.caption("基于 Kimi API + RAG 检索增强 | 支持红蓝队攻防实验")

# 攻击模式提示
if st.session_state.attack_mode:
    st.warning("⚠️ 当前处于红队攻击模式，可测试提示词注入等攻击手段")

# 显示对话历史
for msg_idx, msg in enumerate(st.session_state.history):
    with st.chat_message("user"):
        st.markdown(msg['question'])
    with st.chat_message("assistant"):
        if msg.get("blocked"):
            st.error(msg['answer'])
        else:
            st.markdown(msg['answer'])
        if msg.get('contexts'):
            with st.expander("🔍 查看检索到的参考片段"):
                for i, ctx in enumerate(msg['contexts']):
                    st.text_area(f"片段 {i+1}", ctx, height=80, disabled=True, key=f"hist_{msg_idx}_ctx_{i}")
        if msg.get('sources'):
            st.caption(f"📄 来源: {', '.join(msg['sources'])}")

# 输入框
question = st.chat_input("请输入你的问题...")

if question:
    display_question = question
    # 红队：自动附加选中的攻击载荷
    if st.session_state.attack_mode and st.session_state.selected_payload != "手动输入":
        from attack.prompt_injection import PromptInjection
        payload = PromptInjection.get_payload(st.session_state.selected_payload)
        question = question + "\n\n" + payload
        st.toast(f"⚠️ 已自动附加攻击载荷: {st.session_state.selected_payload}", icon="🔴")
    
    # 显示用户消息（显示原始问题）
    with st.chat_message("user"):
        st.markdown(display_question)
    
    # 调用 RAG
    with st.chat_message("assistant"):
        with st.spinner("🤖 检索知识库并生成回答..."):
            try:
                result = rag.ask(question, defense_enabled=st.session_state.defense_mode)
            except Exception as e:
                st.error(f"调用出错: {e}")
                st.stop()
        
        if result.get("blocked"):
            st.error(result['answer'])
        else:
            st.markdown(result['answer'])
        
        if not result.get("blocked") and result.get('contexts'):
            with st.expander("🔍 查看检索到的参考片段"):
                for i, ctx in enumerate(result['contexts']):
                    st.text_area(f"片段 {i+1}", ctx, height=80, disabled=True, key=f"curr_ctx_{i}")
        
        if result.get('sources'):
            st.caption(f"📄 来源: {', '.join(result['sources'])}")
    
    # 保存历史
    st.session_state.history.append(result)
