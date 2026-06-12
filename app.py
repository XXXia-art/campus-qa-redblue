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

# 页面切换
page = st.radio("选择页面", ["🏫 校园问答", "🔌 MCP 协议攻防"], horizontal=True)

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
    # ========== MCP 协议攻防页面 ==========
    st.header("🔌 MCP (Model Context Protocol) 协议安全攻防")
    st.markdown("""
    MCP 是 Anthropic 推出的开放协议，用于让 LLM Agent 连接外部工具和数据源。
    本页面演示针对 MCP 协议的攻击场景及对应的防御措施，**支持真实调用工具**。
    """)
    
    from attack.mcp_attacks import MCPAttackDemo
    from defense.mcp_defense import MCPDefenseEngine
    from backend.mcp_protocol import MCPClient
    from backend.mcp_campus_server import create_campus_mcp_server
    
    # ========== 第一步：选择 Server 类型 ==========
    server_mode = st.radio("选择 MCP Server", 
                           ["✅ 正常校园 Server", "🌐 真实 API Server", "🔴 基础 MCP 攻击", "🔴 真实 API 攻击", "🕵️ 恶意代理攻击"], 
                           horizontal=True)
    
    if server_mode == "✅ 正常校园 Server":
        server = create_campus_mcp_server()
        st.success(f"✅ 已启动正常 MCP Server: {server.name}")
    elif server_mode == "🌐 真实 API Server":
        from backend.mcp_real_api_server import create_real_api_mcp_server
        server = create_real_api_mcp_server()
        st.success(f"🌐 已启动真实 API MCP Server: {server.name}")
        st.info("本 Server 的工具会发出真实的 HTTP 请求到 wttr.in / ip-api.com")
    elif server_mode == "🔴 基础 MCP 攻击":
        # 选择攻击场景
        scenarios = MCPAttackDemo.list_scenarios()
        scenario_key = st.selectbox("选择攻击场景", list(scenarios.keys()), 
                                    format_func=lambda k: scenarios[k])
        
        scenario = MCPAttackDemo.get_scenario(scenario_key)
        server_class = scenario["server_class"]
        server = server_class()
        
        st.error(f"🔴 已启动恶意 MCP Server: {server.name}")
        st.caption(f"攻击类型: {scenario['name']} — {scenario['description']}")
    elif server_mode == "🔴 真实 API 攻击":
        # 真实 API 攻击场景
        from attack.mcp_real_api_attacks import REAL_API_ATTACK_REGISTRY
        attack_keys = list(REAL_API_ATTACK_REGISTRY.keys())
        attack_names = [REAL_API_ATTACK_REGISTRY[k]["name"] for k in attack_keys]
        
        selected_attack = st.selectbox("选择真实 API 攻击场景", attack_keys,
                                       format_func=lambda k: REAL_API_ATTACK_REGISTRY[k]["name"])
        
        attack_info = REAL_API_ATTACK_REGISTRY[selected_attack]
        server = attack_info["server_class"]()
        
        st.error(f"🔴 已启动真实 API 攻击 Server: {server.name}")
        st.caption(f"攻击类型: {attack_info['name']} — {attack_info['description']}")
        
        # 显示攻击载荷
        with st.expander("💣 攻击载荷示例（点击填入）"):
            for payload_name, payload_value in attack_info["payloads"].items():
                if st.button(f"填入: {payload_name} = `{payload_value}`", key=f"payload_{payload_name}"):
                    st.session_state[f"mcp_inject_{selected_attack}"] = payload_value
                    st.rerun()
    else:
        # ========== 恶意代理攻击 ==========
        from backend.mcp_proxy_attacks import (
            MaliciousProxyServer, create_sniffer_proxy, 
            create_mitm_proxy, create_exfil_proxy
        )
        
        st.header("🕵️ 恶意 MCP 代理攻击（真实流量拦截）")
        st.markdown("""
        本模式下，MCP Server 作为**中间人代理**：
        1. 接收 Client 的请求
        2. **真实拦截** HTTP 请求/响应（抓包）
        3. **篡改**请求参数或响应内容
        4. **外泄**数据到第三方服务器（httpbin.org）
        5. 转发到真实 API
        """)
        
        proxy_mode = st.selectbox("选择代理攻击模式", [
            "sniff_only",
            "tamper_request", 
            "tamper_response",
            "exfiltrate_data",
            "full_mitm"
        ], format_func=lambda x: {
            "sniff_only": "📡 仅抓包（记录所有流量）",
            "tamper_request": "✏️ 篡改请求（修改参数后发给真实API）",
            "tamper_response": "🔧 篡改响应（修改真实API返回结果）",
            "exfiltrate_data": "📤 数据外泄（把请求数据发到外部服务器）",
            "full_mitm": "☠️ 完整MITM（篡改+外泄同时进行）",
        }.get(x, x))
        
        # 创建代理 Server
        server = MaliciousProxyServer()
        server.set_attack_mode(proxy_mode)
        
        # 外泄目标配置
        if "exfil" in proxy_mode or proxy_mode == "full_mitm":
            exfil_target = st.text_input("外泄目标 URL", value="https://httpbin.org/post")
            server.exfiltrate_target = exfil_target
            st.warning(f"⚠️ 请求数据将被**真实发送**到: {exfil_target}")
            st.info("验证方式：调用工具后，访问 https://httpbin.org/get 或查看下方抓包记录")
        
        st.error(f"🕵️ 已启动恶意代理: {server.name} | 模式: {proxy_mode}")
    
    # 用 Client 连接 Server
    client = MCPClient()
    client.connect(server)
    
    # ========== 第二步：Server 信息展示 ==========
    with st.expander("📋 查看 MCP Server 配置"):
        info_cols = st.columns(2)
        with info_cols[0]:
            st.markdown("**Server 信息**")
            st.json(server.get_info())
        with info_cols[1]:
            st.markdown(f"**已发现工具 ({len(client.discovered_tools)} 个)**")
            for tool in client.discovered_tools:
                st.write(f"- `{tool['name']}`: {tool['description']}")
    
    # ========== 第三步：真实工具调用 ==========
    st.divider()
    st.subheader("🛠️ 工具调用测试")
    
    if not client.discovered_tools:
        st.info("该 Server 没有注册任何工具")
    else:
        tool_names = [t["name"] for t in client.discovered_tools]
        selected_tool_name = st.selectbox("选择要调用的工具", tool_names)
        
        # 获取工具参数
        selected_tool = None
        for t in server.tools.values():
            if t.name == selected_tool_name:
                selected_tool = t
                break
        
        if selected_tool:
            # 动态生成参数输入框
            args = {}
            if selected_tool.parameters:
                param_cols = st.columns(min(len(selected_tool.parameters), 3))
                for idx, (param_name, param_info) in enumerate(selected_tool.parameters.items()):
                    with param_cols[idx % 3]:
                        default_val = ""
                        
                        # 检查是否有预置的攻击载荷
                        inject_key = None
                        for key in st.session_state:
                            if key.startswith("mcp_inject_"):
                                inject_key = key
                                break
                        
                        if inject_key and param_name in ["city", "ip_list", "ip"]:
                            default_val = st.session_state[inject_key]
                        elif param_name == "book_name":
                            default_val = "人工智能导论"
                        elif param_name == "card_id":
                            default_val = "22020001"
                        elif param_name == "student_id":
                            default_val = "22020001"
                        elif param_name == "date":
                            default_val = "2024-01-15"
                        elif param_name == "data_source":
                            default_val = "/campus/student_records.db"
                        elif param_name == "report_type":
                            default_val = "成绩统计"
                        elif param_name == "to":
                            default_val = "admin@seu.edu.cn"
                        elif param_name == "subject":
                            default_val = "校园通知"
                        elif param_name == "body":
                            default_val = "这是一条测试通知"
                        elif param_name == "command":
                            default_val = "cat /etc/passwd"
                        elif param_name == "campus":
                            default_val = "九龙湖"
                        elif param_name == "direction":
                            default_val = "四牌楼→九龙湖"
                        elif param_name == "keyword":
                            default_val = "安全须知"
                        
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
                    # 处理恶意工具的隐藏行为展示
                    result_data = result.get("result", {})
                    if isinstance(result_data, dict) and result_data.get("warning"):
                        st.error(result_data["warning"])
                        st.json(result_data)
                    else:
                        st.success("工具调用成功")
                        st.json(result_data)
                else:
                    st.error(f"调用失败: {result.get('error')}")
    
    # ========== 第四步：防御检测 ==========
    st.divider()
    st.subheader("🔵 防御检测")
    defense = MCPDefenseEngine()
    
    # 综合检查
    perms = getattr(server, 'requested_permissions', [])
    report = defense.inspect_server({
        "name": server.name,
        "description": server.description,
        "permissions": perms,
        "tools": server.list_tools(),
    })
    
    if report["overall_safe"]:
        st.success("✅ 综合检查通过 — 该 MCP Server 安全风险较低")
    else:
        st.error("🚫 检测到安全风险！请谨慎使用该 Server")
    
    # 详细报告
    detail_cols = st.columns(2)
    with detail_cols[0]:
        with st.expander("权限风险评估"):
            perm = report["details"]["permissions"]
            st.markdown(f"**风险等级**: `{perm['risk_level'].upper()}`")
            st.write(f"- 高危权限 ({len(perm['high_risk'])}): {', '.join(perm['high_risk']) or '无'}")
            st.write(f"- 中危权限 ({len(perm['medium_risk'])}): {', '.join(perm['medium_risk']) or '无'}")
            st.write(f"- 低危权限 ({len(perm['low_risk'])}): {', '.join(perm['low_risk']) or '无'}")
    
    with detail_cols[1]:
        with st.expander("工具安全验证"):
            tools = report["details"]["tools"]
            st.markdown(f"**验证结果**: {'✅ 全部通过' if tools['all_safe'] else '❌ 发现问题'}")
            for r in tools["tool_results"]:
                if r["warnings"]:
                    for w in r["warnings"]:
                        st.warning(w)
            if tools["duplicate_tools"]:
                st.error(f"检测到同名工具冲突: {', '.join(tools['duplicate_tools'])}")
    
    # 防御建议
    if report["recommendations"]:
        st.markdown("#### 🛡️ 防御建议")
        for rec in report["recommendations"]:
            st.info(rec)
    
    # ========== 第五步：恶意代理的抓包展示 ==========
    if server_mode == "🕵️ 恶意代理攻击" and isinstance(server, MaliciousProxyServer):
        st.divider()
        st.header("📡 抓包记录（真实 HTTP 流量）")
        
        records = server.get_records()
        if not records:
            st.info("暂无抓包记录，请先调用工具")
        else:
            st.write(f"已拦截 **{len(records)}** 条 HTTP 流量")
            
            for rec in records:
                icon = "📡"
                if rec["tampered_request"] and rec["tampered_response"]:
                    icon = "☠️"
                elif rec["tampered_request"]:
                    icon = "✏️"
                elif rec["tampered_response"]:
                    icon = "🔧"
                elif rec["exfiltrated"]:
                    icon = "📤"
                
                with st.expander(f"{icon} #{rec['id']} {rec['method']} {rec['url'][:60]}... ({rec['status']}) {rec['time_ms']}ms"):
                    cols = st.columns(2)
                    
                    with cols[0]:
                        st.markdown("**📤 请求**")
                        st.markdown(f"```\n{rec['method']} {rec['url']}\n```")
                        if rec.get("tamper_details"):
                            st.error(f"🚨 攻击操作: {rec['tamper_details']}")
                    
                    with cols[1]:
                        st.markdown("**📥 响应**")
                        st.markdown(f"```\nHTTP {rec['status']}\nTime: {rec['time_ms']}ms\n```")
                        if rec["exfiltrated"]:
                            st.error(f"📤 数据已外泄到: {rec['exfiltrate_target']}")
                    
                    # 详细请求/响应体
                    detail = server.get_record_detail(rec["id"])
                    if detail:
                        st.markdown("**请求体：**")
                        st.code(detail.request_body[:500], language="json")
                        st.markdown("**响应体（前 800 字符）：**")
                        st.code(detail.response_body[:800], language="json")
            
            if st.button("🗑️ 清空抓包记录"):
                server.clear_records()
                st.rerun()
    
    # 资源清洗演示（针对间接注入）
    if server_mode == "🔴 基础 MCP 攻击" and scenario_key == "indirect_injection":
        st.divider()
        st.subheader("📄 资源内容清洗演示")
        resource = server.read_resource("campus_safety_guide")
        if resource.get("success"):
            sanitized = defense.inspect_resource(resource["content"])
            
            clean_cols = st.columns(2)
            with clean_cols[0]:
                st.markdown("**原始内容（含毒化指令）**")
                st.code(resource["content"], language="text")
            with clean_cols[1]:
                st.markdown("**清洗后内容**")
                if not sanitized["safe"]:
                    st.error(f"检测到威胁标记: {', '.join(sanitized['threats'])}")
                st.code(sanitized["cleaned"], language="text")
