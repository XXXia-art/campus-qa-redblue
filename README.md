# 🎓 校园智能问答机器人 - AI 智能体安全攻防实验平台

基于 **Mimo OpenAI 兼容 API** 和 **RAG 检索增强** 构建的校园问答机器人，用于课堂演示 **LLM Prompt 注入攻击** 与 **网络层/应用层防御**。

> 核心设计：红队攻击不再由本机拼接 prompt，而是通过 Streamlit 开关控制一个文件标志；`mitmproxy` 读取该标志后，在真实网络流量中注入恶意 prompt。蓝队则部署在攻击者下游，对篡改后的流量进行检测、清洗或阻断。

---

## ✨ 主要功能

| 模块 | 说明 |
|---|---|
| 🏫 **校园问答** | 基于 RAG 的校园知识问答，支持文档上传、向量检索、LLM 生成。 |
| 🔴 **红队 MITM Prompt 注入** | 通过 `mitmproxy` 拦截 LLM API 请求，按开关决定是否追加恶意 prompt。 |
| 🔵 **蓝队网络层防御** | 独立的 `mitmproxy` 防御网关，检测并清洗/阻断注入载荷。 |
| 🛡️ **应用层防御** | 输入过滤、输出守卫、安全系统提示，作为最后一道防线。 |
| 🔌 **MCP 协议攻防** | 演示正常 MCP Server、恶意 Server、真实 API 攻击、恶意代理攻击等场景。 |

---

## 🏗️ 架构概览

```text
┌─────────────────┐      HTTP_PROXY=8082      ┌──────────────────────┐
│  Streamlit App  │ ────────────────────────▶ │  红队 mitmproxy      │
│  (受害者/用户)   │                           │  - 读取 .mitm_attack_mode
└─────────────────┘                           │  - 注入恶意 prompt   │
                                              └──────────┬───────────┘
                                                         │ upstream
                                                         ▼
                                              ┌──────────────────────┐
                                              │  蓝队 mitmproxy      │
                                              │  - 读取 .blue_team_enabled
                                              │  - 清洗/阻断注入     │
                                              └──────────┬───────────┘
                                                         │
                                                         ▼
                                              ┌──────────────────────┐
                                              │  LLM API             │
                                              │  api.xiaomimimo.com  │
                                              └──────────────────────┘
```

- 红队和蓝队代理通过 `--mode upstream` 串联。
- Streamlit 只负责写标志文件，**不本地拼接攻击载荷**。

---

## 📁 项目结构

```text
kimi_chat/
├── app.py                          # Streamlit Web 界面
├── cli.py                          # 命令行入口
├── requirements.txt                # pip 依赖
├── environment.yml                 # conda 环境配置
├── .env.example                    # 环境变量模板
├── DEMO_PLAN.md                    # 课堂演示完整方案 ⭐
│
├── start_redblue_chain.ps1         # 一键启动红队+蓝队代理链（本机测试）
├── start_attacker_en.ps1           # 攻击者代理启动脚本
├── start_blue_team_proxy.ps1       # 蓝队防御代理启动脚本
│
├── mitm_prompt_inject.py           # 红队 MITM Prompt 注入 addon
├── mitm_blue_team.py               # 蓝队网络层防御 addon
│
├── backend/                        # 后端核心模块
│   ├── config.py                   # 配置管理
│   ├── llm_client.py               # OpenAI/Anthropic 兼容 LLM 客户端
│   ├── rag_engine.py               # RAG 问答引擎（含输入过滤、输出守卫）
│   ├── vector_store.py             # ChromaDB 向量数据库
│   ├── document_loader.py          # 文档加载与切分
│   ├── mcp_protocol.py             # MCP 协议抽象
│   └── ...                         # 其他 MCP Server/攻击/防御相关模块
│
├── attack/                         # 🔴 红队攻击载荷
│   ├── prompt_injection.py         # Prompt 注入载荷库
│   └── mcp_attacks.py              # MCP 攻击场景
│
├── defense/                        # 🔵 蓝队防御模块
│   ├── input_filter.py             # 输入安全过滤
│   ├── output_guard.py             # 输出层安全守卫
│   └── mcp_defense.py              # MCP 防御模块
│
├── data/                           # 校园公开数据
│   └── seu_campus_full.txt
│
└── docs/                           # 课堂文档
    └── mitm_prompt_injection.md    # Prompt 中间人注入详细指南
```

---

## 🚀 快速开始

### 1. 创建 Conda 环境

```powershell
conda create -n kimi_chat python=3.11 -y
conda activate kimi_chat
```

### 2. 安装依赖

```powershell
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

> 首次安装会下载 PyTorch、Embedding 模型等，耗时约 5~10 分钟。

### 3. 配置 API Key

```powershell
copy .env.example .env
```

编辑 `.env`，填入你的 API Key：

```env
LLM_API_KEY=sk-xxxxxxxx
LLM_BASE_URL=https://api.xiaomimimo.com/v1
LLM_MODEL=mimo-v2.5-pro
```

### 4. 启动红蓝队代理链

```powershell
cd A:\The_code\kimi_chat
conda activate kimi_chat
.\start_redblue_chain.ps1 -AttackMode prompt
```

成功后显示：

```text
Blue web UI: http://127.0.0.1:8085
Red  web UI: http://127.0.0.1:8083 (password: mitm)
```

### 5. 启动 Streamlit

再开一个 PowerShell 窗口：

```powershell
cd A:\The_code\kimi_chat
conda activate kimi_chat
$env:HTTP_PROXY="http://127.0.0.1:8082"
$env:HTTPS_PROXY="http://127.0.0.1:8082"
streamlit run app.py
```

浏览器会自动打开 `http://localhost:8501`。

---

## 🎮 使用指南

### 红蓝队攻防实验

在 Streamlit 侧边栏：

| 开关 | 作用 |
|---|---|
| 🔴 **红队攻击模式** | 写入 `.mitm_attack_mode` 和 `.mitm_payload`，让 mitmproxy 注入所选载荷。 |
| 🔵 **蓝队防御模式** | 开启应用层防御，并写入 `.blue_team_enabled` 供网络层蓝队代理读取。 |

蓝队网络层动作：

- **清洗载荷（sanitize）**：剥离注入载荷后放行给 LLM。
- **阻断请求（block）**：直接返回防御响应，请求不到达 LLM。

### MCP 协议攻防

切换到 **🔌 MCP 协议攻防** 页面，可体验：

- 正常校园 MCP Server
- 真实 API Server（天气、IP 定位）
- 基础 MCP 攻击
- 真实 API 攻击（SSRF、参数注入等）
- 恶意 MCP 代理攻击

---

## 🎯 课堂演示

完整演示方案见：

📄 **[DEMO_PLAN.md](./DEMO_PLAN.md)**

简要流程：

1. **正常场景**：红队/蓝队都关闭，提问校园问题，正常回答。
2. **红队注入**：红队开、蓝队关，展示模型被注入后的异常响应。
3. **蓝队阻断**：红队开、蓝队开+阻断，展示请求被网络层拦截。
4. **蓝队清洗**：红队开、蓝队开+清洗，展示注入载荷被剥离，模型正常回答。
5. **编码混淆**：使用 Base64 等编码攻击，展示蓝队 addon 仍能解码检测。

---

## ⚙️ 配置说明（.env）

| 参数 | 说明 | 默认值 |
|---|---|---|
| `LLM_API_KEY` | API 密钥 | 必填 |
| `LLM_BASE_URL` | API 基础地址 | `https://api.xiaomimimo.com/v1` |
| `LLM_MODEL` | 模型名称 | `mimo-v2.5-pro` |
| `EMBEDDING_MODEL` | 本地 Embedding 模型 | `BAAI/bge-small-zh-v1.5` |
| `CHUNK_SIZE` | 文档切分片段长度 | `500` |
| `CHUNK_OVERLAP` | 切分重叠长度 | `50` |
| `TOP_K` | 检索返回片段数 | `3` |

---

## ⚠️ 注意事项

1. **证书问题**：受害者电脑必须安装 mitmproxy CA 证书到“受信任的根证书颁发机构”。
2. **Python 证书不信任**：即使安装了 CA，`httpx` 默认不信任系统 CA，所以 `backend/llm_client.py` 在检测到代理时会自动使用 `verify=False`。
3. **bcrypt 冲突**：若启动 mitmweb 报错，执行 `pip install bcrypt==4.0.1`。
4. **代理冲突**：运行演示前关闭 Clash/VPN，或改用 mitmproxy 端口。
5. **API Key 安全**：课堂演示中 Bearer Token 会在代理中明文可见，课后请更换 API Key。
6. **法律与道德**：本实验仅用于授权的教学场景，所有参与者必须知情同意。

---

## ❓ 常见问题

### Q1: Embedding 模型下载很慢？

```powershell
$env:HF_ENDPOINT="https://hf-mirror.com"
streamlit run app.py
```

### Q2: 端口被占用？

```powershell
Get-Process mitmweb | Stop-Process
```

### Q3: 面板打不开？

浏览器访问 `http://127.0.0.1:8083`，不要用 `0.0.0.0`。

### Q4: 可以用其他 LLM API 吗？

可以。`backend/llm_client.py` 使用 OpenAI 兼容格式，修改 `.env` 中的 `LLM_BASE_URL`、`LLM_MODEL`、`LLM_API_KEY` 即可。

---

## 📄 许可证

本项目仅用于教学和研究目的。
