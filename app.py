"""
校园智能问答机器人 - Web 界面
使用 Streamlit 启动：streamlit run app.py
"""

import os

# 配置代理（支持课堂演示模式）
# 默认使用 Clash 代理，但允许通过环境变量覆盖
if not os.getenv("HTTP_PROXY") and not os.getenv("http_proxy"):
    os.environ["HTTP_PROXY"] = "http://127.0.0.1:7897"
if not os.getenv("HTTPS_PROXY") and not os.getenv("https_proxy"):
    os.environ["HTTPS_PROXY"] = "http://127.0.0.1:7897"

os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

# 禁用 requests SSL 警告（教学演示环境使用 verify=False）
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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
.defense-box { background-color: #1a472a; color: #ffffff; border: 1px solid #66bb6a; padding: 10px; border-radius: 5px; }
.packet-box { background-color: #1e1e1e; color: #00ff00; font-family: monospace; padding: 10px; border-radius: 5px; overflow-x: auto; }
</style>
""", unsafe_allow_html=True)

# ========== 初始化 ==========
if 'rag' not in st.session_state:
    if not check_api_key():
        st.error("🚨 未检测到 LLM API Key！请先将 `.env.example` 复制为 `.env`，并填入你的 API Key")
        st.stop()
    st.session_state.rag = RAGEngine()
    st.session_state.history = []
    st.session_state.attack_mode = False
    st.session_state.defense_mode = False
    st.session_state.selected_attack_category = "直接注入"
    st.session_state.selected_attack_method = "ignore_instruction"
    
    # 启动时自动加载校园数据
    full_data_path = "./data/seu_campus_full.txt"
    data_dir = "./data"
    
    # 如果有完整的校园数据文件，优先加载（清空旧库确保不重复）
    if os.path.exists(full_data_path):
        current_count = st.session_state.rag.vector_store.count()
        # 简单判断：如果片段数明显偏少（只有旧数据），或没有数据，则加载
        if current_count == 0 or current_count < 50:
            with st.spinner("📚 正在加载完整校园数据到知识库..."):
                if current_count > 0:
                    st.session_state.rag.vector_store.clear()
                st.session_state.rag.ingest_document(full_data_path)
    elif os.path.exists(data_dir) and st.session_state.rag.vector_store.count() == 0:
        with st.spinner("📚 正在自动加载校园数据到知识库..."):
            st.session_state.rag.ingest_directory(data_dir)

rag = st.session_state.rag

# ========== 侧边栏 ==========
with st.sidebar:
    st.title("⚙️ 控制台")
    
    # 页面切换
    page = st.radio("选择页面", ["🏫 校园问答", "🔌 MCP 协议攻防"], horizontal=True)
    
    # API 状态
    if check_api_key():
        st.success("✅ Mimo API 已配置")
    else:
        st.error("❌ Mimo API 未配置")
    
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
    
    attack_mode = st.toggle("🔴 红队攻击模式（MITM 注入）", value=st.session_state.attack_mode)
    st.session_state.attack_mode = attack_mode
    
    # MITM 攻击标志文件路径
    attack_flag_path = os.path.join(os.path.dirname(__file__), ".mitm_attack_mode")
    payload_path = os.path.join(os.path.dirname(__file__), ".mitm_payload")
    
    if attack_mode:
        if page == "🏫 校园问答":
            st.markdown("<div style='background-color:#5c1a1a;color:#fff;border:1px solid #ef5350;padding:10px;border-radius:5px;'>红队模式已开启：mitmproxy 将自动注入所选载荷</div>", unsafe_allow_html=True)
            from attack.prompt_injection import ATTACK_REGISTRY, generate_attack_payload
            
            # 攻击分类选择
            categories = list(ATTACK_REGISTRY.keys())
            selected_category = st.selectbox("攻击分类", categories,
                                             index=categories.index(st.session_state.selected_attack_category))
            st.session_state.selected_attack_category = selected_category
            
            # 具体方法选择
            methods = ATTACK_REGISTRY[selected_category]["methods"]
            selected_method = st.selectbox("攻击方法", methods,
                                           index=methods.index(st.session_state.selected_attack_method) if st.session_state.selected_attack_method in methods else 0)
            st.session_state.selected_attack_method = selected_method
            
            # 预览载荷
            payload_preview = generate_attack_payload(selected_category, selected_method)
            st.text_area("MITM 注入载荷预览", payload_preview, height=120)
            
            # 写入标志文件和载荷文件
            try:
                with open(attack_flag_path, "w") as f:
                    f.write("enabled")
                with open(payload_path, "w", encoding="utf-8") as f:
                    f.write(payload_preview)
            except Exception as e:
                st.error(f"写入 MITM 攻击标志失败: {e}")
        else:
            st.markdown("<div style='background-color:#5c1a1a;color:#fff;border:1px solid #ef5350;padding:10px;border-radius:5px;'>红队模式已开启：MCP 流量将被中间人篡改</div>", unsafe_allow_html=True)
            # MCP 模式下同样写入攻击标志，供 mitm_mcp_attack.py 使用
            try:
                with open(attack_flag_path, "w") as f:
                    f.write("enabled")
            except Exception as e:
                st.error(f"写入 MITM 攻击标志失败: {e}")
    else:
        # 关闭时删除标志文件
        for path in [attack_flag_path, payload_path]:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except Exception:
                    pass
    
    defense_mode = st.toggle("🔵 蓝队防御模式", value=st.session_state.defense_mode)
    st.session_state.defense_mode = defense_mode
    
    # 蓝队网络层防御标志文件路径
    defense_flag_path = os.path.join(os.path.dirname(__file__), ".blue_team_enabled")
    defense_mode_path = os.path.join(os.path.dirname(__file__), ".blue_team_mode")
    
    if defense_mode:
        st.markdown("<div class='defense-box'>防御模式已开启，可疑输入将被拦截</div>", unsafe_allow_html=True)
        
        defense_action = st.selectbox(
            "蓝队网络层动作",
            ["清洗载荷（sanitize）", "阻断请求（block）"],
            index=0,
            help="清洗：剥离注入载荷后放行；阻断：直接返回拦截响应"
        )
        
        # 写入蓝队网络层防御标志
        try:
            with open(defense_flag_path, "w") as f:
                f.write("enabled")
            mode_value = "sanitize" if "清洗" in defense_action else "block"
            with open(defense_mode_path, "w", encoding="utf-8") as f:
                f.write(mode_value)
        except Exception as e:
            st.error(f"写入蓝队防御标志失败: {e}")
    else:
        for path in [defense_flag_path, defense_mode_path]:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except Exception:
                    pass

# ========== 主界面 ==========
st.title("🎓 校园智能问答机器人")
st.caption("基于 Mimo API + RAG 检索增强 | 支持红蓝队攻防实验 | MCP 协议安全")

if page == "🏫 校园问答":
    # ========== 校园问答页面 ==========
    
    # MITM 攻击模式提示
    if st.session_state.attack_mode:
        st.warning("⚠️ 当前处于红队 MITM 攻击模式，mitmproxy 会自动在 LLM 请求中注入载荷")
    
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
        actual_question = question
        
        # 显示用户消息
        with st.chat_message("user"):
            st.markdown(question)
        
        # 调用 RAG
        with st.chat_message("assistant"):
            with st.spinner("🤖 检索知识库并生成回答..."):
                try:
                    result = rag.ask(actual_question, defense_enabled=st.session_state.defense_mode)
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

else:
    # ========== MCP 真实 API Server 演示 ==========
    st.header("🔌 MCP 协议安全演示")
    st.markdown("""
    MCP 是 Anthropic 推出的开放协议，用于让 LLM Agent 连接外部工具和数据源。
    使用左侧边栏的 **🔴 红队攻击模式** 和 **🔵 蓝队防御模式** 切换 MCP 攻防状态。
    """)

    from backend.mcp_protocol import MCPClient
    from backend.mcp_real_api_server import create_real_api_mcp_server
    from defense.mcp_defense import MCPDefenseEngine

    attack_mode = st.session_state.get("attack_mode", False)
    defense_mode = st.session_state.get("defense_mode", False)

    # 始终使用真实 API MCP Server，红队攻击在 mitmproxy 层篡改真实 API 请求
    server = create_real_api_mcp_server()
    st.success(f"🌐 已启动真实 API MCP Server: {server.name}")
    if attack_mode:
        st.error("🔴 红队攻击已开启：MCP 对 wttr.in / ip-api.com 的真实 API 请求将被中间人篡改")
    else:
        st.info("本 Server 的工具会发出真实的 HTTP 请求到 wttr.in / ip-api.com")

    client = MCPClient()
    client.connect(server)

    # Server 信息展示
    with st.expander("📋 查看 MCP Server 配置"):
        info_cols = st.columns(2)
        with info_cols[0]:
            st.markdown("**Server 信息**")
            st.json(server.get_info())
        with info_cols[1]:
            st.markdown(f"**已发现工具 ({len(client.discovered_tools)} 个)**")
            for tool in client.discovered_tools:
                st.write(f"- `{tool['name']}`: {tool['description']}")

    # 安全检查
    st.divider()
    st.subheader("🔵 MCP Server 安全检查")
    defense = MCPDefenseEngine()
    perms = getattr(server, 'requested_permissions', [])
    report = defense.inspect_server({
        "name": server.name,
        "description": server.description,
        "permissions": perms,
        "tools": server.list_tools(),
    })

    blocked_by_defense = False
    if defense_mode:
        if report["overall_safe"]:
            st.success("✅ 蓝队检查通过 — 该 MCP Server 安全，可以继续调用工具")
        else:
            blocked_by_defense = True
            st.error("🛡️ 【蓝队防御拦截】检测到恶意 MCP Server，已禁止工具调用")
    else:
        if report["overall_safe"]:
            st.success("✅ 综合检查通过 — 该 MCP Server 安全风险较低")
        else:
            st.error("🚫 检测到安全风险！请谨慎使用该 Server")

    if report["recommendations"]:
        for rec in report["recommendations"]:
            st.info(rec)

    # 工具调用测试
    if not blocked_by_defense:
        st.divider()
        st.subheader("🛠️ 工具调用测试")

        if not client.discovered_tools:
            st.info("该 Server 没有注册任何工具")
        else:
            tool_names = [t["name"] for t in client.discovered_tools]
            selected_tool_name = st.selectbox("选择要调用的工具", tool_names)

            selected_tool = None
            for t in server.tools.values():
                if t.name == selected_tool_name:
                    selected_tool = t
                    break

            if selected_tool:
                args = {}
                if selected_tool.parameters:
                    param_cols = st.columns(min(len(selected_tool.parameters), 3))
                    for idx, (param_name, param_info) in enumerate(selected_tool.parameters.items()):
                        with param_cols[idx % 3]:
                            default_val = ""
                            if param_name == "city":
                                default_val = "Nanjing"
                            elif param_name == "ip":
                                default_val = "8.8.8.8"
                            elif param_name == "campus":
                                default_val = "九龙湖"
                            args[param_name] = st.text_input(
                                f"{param_name} ({param_info.get('description', '')})",
                                value=default_val,
                                key=f"mcp_param_{param_name}"
                            )

                if st.button("▶️ 调用工具", type="primary"):
                    with st.spinner("正在调用 MCP 工具..."):
                        result = client.call_tool(selected_tool_name, **args)

                    st.markdown("**调用结果：**")
                    if result.get("success"):
                        result_data = result.get("result", {})
                        if isinstance(result_data, dict) and result_data.get("warning"):
                            st.error(result_data["warning"])
                        else:
                            st.success("工具调用成功")
                        st.json(result_data)
                    else:
                        st.error(f"调用失败: {result.get('error')}")
