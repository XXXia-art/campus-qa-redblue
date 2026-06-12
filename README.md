# 🎓 校园智能问答机器人（Kimi API + RAG）

基于 **Kimi API** 和 **RAG 检索增强技术** 构建的简易智能问答机器人，用于 AI 智能体安全攻防实验。

---

## 📁 项目结构

```
kimi_chat/
├── app.py                          # Web 界面入口（Streamlit）
├── cli.py                          # 命令行入口
├── start_attacker_en.ps1          # 攻击者一键启动脚本（课堂演示）
├── mitm_prompt_inject.py          # Prompt 中间人注入 mitmproxy 脚本
├── requirements.txt               # pip 依赖
├── environment.yml                # conda 环境配置
├── .env.example                   # 环境变量模板
├── data/                          # 校园公开数据（可替换为你自己的）
│   ├── sample_campus.txt
│   ├── security_policy.txt
│   └── seu_campus.txt
├── backend/                       # 后端核心模块
│   ├── config.py                  # 配置管理
│   ├── llm_client.py              # Kimi API 客户端
│   ├── document_loader.py         # 文档加载与切分
│   ├── vector_store.py            # 向量数据库（ChromaDB）
│   ├── rag_engine.py              # RAG 问答引擎
│   ├── mcp_protocol.py            # MCP 协议抽象
│   ├── mcp_real_api_server.py     # 真实 API MCP Server
│   └── mcp_proxy_attacks.py       # 恶意 MCP 代理攻击
├── attack/                        # 🔴 红队攻击模块
│   └── prompt_injection.py        # 提示词注入载荷库
├── defense/                       # 🔵 蓝队防御模块
│   ├── input_filter.py            # 输入安全过滤器
│   └── mcp_defense.py             # MCP 防御模块
├── docs/                          # 课堂演示文档
│   └── mitm_prompt_injection.md   # Prompt 中间人注入详细指南
└── 课堂展示_双机对抗流程.md       # 课堂演示完整流程
```

---

## 🚀 快速开始

### 1. 创建 Conda 环境

```bash
conda create -n kimi_chat python=3.11 -y
conda activate kimi_chat
```

### 2. 安装依赖

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

> 首次安装会下载 PyTorch、Embedding 模型等，耗时约 5~10 分钟，请耐心等待。

### 3. 配置 API Key

```bash
copy .env.example .env
```

编辑 `.env` 文件，填入你的 API Key。

### 4. 启动

```bash
streamlit run app.py
```

浏览器会自动打开 `http://localhost:8501`。

---

## ⚙️ 配置说明

### 可选参数（.env 文件）

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `LLM_API_KEY` | API 密钥 | 必填 |
| `LLM_BASE_URL` | API 基础地址 | `https://api.xiaomimimo.com/v1` |
| `LLM_MODEL` | 模型名称 | `mimo-v2.5-pro` |
| `EMBEDDING_MODEL` | 本地 Embedding 模型 | `BAAI/bge-small-zh-v1.5` |
| `CHUNK_SIZE` | 文档切分片段长度 | `500` |
| `CHUNK_OVERLAP` | 切分重叠长度 | `50` |
| `TOP_K` | 检索返回的片段数 | `3` |

---

## 🖥️ 使用指南

### 启动后自动加载数据

启动 Web 界面后，系统会**自动检测并加载** `data/` 目录下的所有文档。

### 红蓝攻防实验

| 模式 | 操作 | 效果 |
|------|------|------|
| **🔴 红队攻击** | 开启开关 → 选择攻击载荷 → 输入正常问题 | 系统自动附加注入语句，测试模型安全性 |
| **🔵 蓝队防御** | 开启开关 → 输入攻击语句 | 系统检测并拦截可疑输入 |

### 🔌 MCP 协议攻防

切换到 **MCP 协议攻防** 页面，可体验：
- 正常 MCP Server 调用
- 真实 API Server（天气、IP 定位）
- 基础 MCP 攻击
- 真实 API 攻击（SSRF、参数注入等）
- 恶意 MCP 代理攻击（中间人篡改、响应篡改、数据外泄）

---

## 🛡️ 安全攻防实验指南

### 红队（攻击方）
1. 开启「🔴 红队攻击模式」
2. 在下拉菜单选择攻击载荷
3. 输入一个正常问题
4. 系统自动附加攻击语句，观察模型是否被攻破

### 蓝队（防御方）
1. 开启「🔵 蓝队防御模式」
2. 分析 `defense/input_filter.py` 中的规则
3. 尝试补充新的过滤规则或改进检测逻辑
4. 重新测试红队攻击，验证防御效果

---

## 🎯 课堂双机对抗演示

本项目支持真实的「攻击者电脑开热点 + 受害者电脑连接 + mitmproxy 中间人拦截」演示。

### 攻击模式

| 模式 | 命令 | 效果 |
|------|------|------|
| MCP 中间人攻击 | `.\start_attacker_en.ps1 -Mode mcp` | 拦截 MCP 真实 API 请求（Nanjing → Beijing） |
| Prompt 中间人注入 | `.\start_attacker_en.ps1 -Mode prompt` | 自动篡改 LLM API 请求中的用户 prompt |
| 同时启用 | `.\start_attacker_en.ps1 -Mode both` | 两种攻击同时生效 |

### 关键文件

- `课堂展示_双机对抗流程.md` —— 完整演示脚本与时间分配
- `docs/mitm_prompt_injection.md` —— Prompt 中间人注入详细指南
- `mitm_prompt_inject.py` —— mitmproxy 自动注入脚本

### 演示要点

1. **Prompt 中间人注入**：受害者正常提问，攻击者通过网络中间人偷偷追加恶意 prompt，诱导 LLM 泄露系统提示词。
2. **MCP 中间人攻击**：受害者调用天气工具，攻击者篡改真实 API 请求，让南京变北京。

> ⚠️ **法律与道德提示**：本实验仅用于授权的教学场景，所有参与者必须知情同意。

---

## ❓ 常见问题

### Q1: Embedding 模型下载很慢/失败？

HuggingFace 在国内访问不稳定，启动前设置镜像：

```bash
# Windows PowerShell
$env:HF_ENDPOINT="https://hf-mirror.com"
streamlit run app.py
```

### Q2: 启动时报错 `No module named 'torchvision'`？

```bash
pip install torchvision -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### Q3: API 报错 429（余额不足）？

你的 API Key 有效，但账户余额已用完。解决方式：
1. 登录相应平台费用中心
2. 检查是否有余额
3. 充值或更换 API Key

### Q4: 可以用其他大模型 API 代替吗？

可以。`backend/llm_client.py` 使用的是 OpenAI 兼容格式，修改 `base_url`、`api_key`、`model` 即可接入其他兼容服务。

### Q5: 模型下载到了哪里？

默认缓存位置：`C:\Users\你的用户名\.cache\torch\sentence_transformers`

如需换到别的磁盘，启动前设置：
```bash
$env:SENTENCE_TRANSFORMERS_HOME="A:\models\sentence_transformers"
```

---

## 📄 技术文档

详细的系统设计、RAG 原理、攻防模块说明见 `技术文档.md`。
