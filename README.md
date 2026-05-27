# 🎓 校园智能问答机器人（Kimi API + RAG）

基于 **Kimi API** 和 **RAG 检索增强技术** 构建的简易智能问答机器人，用于 AI 智能体安全攻防实验。

---

## 📁 项目结构

```
kimi_chat/
├── app.py                  # Web 界面入口（Streamlit）
├── cli.py                  # 命令行入口
├── requirements.txt        # pip 依赖
├── .env.example            # 环境变量模板
├── data/                   # 校园公开数据（可替换为你自己的）
│   ├── sample_campus.txt
│   ├── security_policy.txt
│   └── seu_campus.txt
├── backend/                # 后端核心模块
│   ├── config.py           # 配置管理
│   ├── llm_client.py       # Kimi API 客户端
│   ├── document_loader.py  # 文档加载与切分
│   ├── vector_store.py     # 向量数据库（ChromaDB）
│   └── rag_engine.py       # RAG 问答引擎
├── attack/                 # 🔴 红队攻击模块
│   └── prompt_injection.py # 提示词注入载荷库
├── defense/                # 🔵 蓝队防御模块
│   └── input_filter.py     # 输入安全过滤器
├── docs/
│   └── MCP_SECURITY_EXPERIMENT.md # MCP 受控安全实验方案
└── tests/                  # 安全提示词与载荷回归测试
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

编辑 `.env` 文件，填入你的 Kimi API Key（以 `sk-` 开头）。

### 4. 启动

```bash
streamlit run app.py
```

浏览器会自动打开 `http://localhost:8501`。

---

## ⚙️ 配置说明

### 获取 Kimi API Key

1. 访问 [Kimi 开放平台](https://platform.moonshot.cn)
2. 注册/登录 →「API Key 管理」→「创建」
3. 复制 `sk-` 开头的 Key 粘贴到 `.env` 文件的 `KIMI_API_KEY=` 后面

> **注意**：Kimi 网页版/App 会员与 API 额度是两套独立系统。新账号通常赠送 15 元免费额度；用完需在「费用中心」充值（充 5~10 元足够实验使用）。

### 可选参数（.env 文件）

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `KIMI_API_KEY` | Kimi API 密钥 | 必填 |
| `KIMI_MODEL` | 模型名称 | `moonshot-v1-8k` |
| `EMBEDDING_MODEL` | 本地 Embedding 模型 | `BAAI/bge-small-zh-v1.5` |
| `CHUNK_SIZE` | 文档切分片段长度 | `500` |
| `CHUNK_OVERLAP` | 切分重叠长度 | `50` |
| `TOP_K` | 检索返回的片段数 | `3` |

---

## 🖥️ 使用指南

### 启动后自动加载数据

启动 Web 界面后，系统会**自动检测并加载** `data/` 目录下的所有文档。左侧会显示：

> 当前知识库片段数: **XX**

### 上传自定义文档

1. 在左侧「知识库管理」点击 **Upload**，选择校园文档（支持 txt / md / pdf）
2. 点击 **加入知识库**
3. 系统自动切分、向量化并存入知识库

### 提问与 RAG 检索

在下方输入框输入问题，例如：
- "东南大学图书馆本科生最多能借几本书？"
- "校园卡丢了怎么补办？"
- "九龙湖校区有哪些食堂？"

点击回答下方的 **「查看检索到的参考片段」**，可以看到系统从知识库中检索到的原文片段及来源文件。

### 红蓝攻防实验

| 模式 | 操作 | 效果 |
|------|------|------|
| **🔴 红队攻击** | 开启开关 → 选择攻击案例 → 输入正常问题 | 展示攻击目标、成功信号及载荷，并自动附加测试文本 |
| **🔵 蓝队防御** | 开启开关 → 输入攻击语句 | 系统检测并拦截可疑输入；RAG prompt 另外隔离不可信资料 |

---

## 🛡️ 安全攻防实验指南

### 红队（攻击方）
1. 开启「🔴 红队攻击模式」
2. 在下拉菜单选择攻击载荷（如 `direct_prompt_leak`）
3. 输入一个正常问题（如"你好"）
4. 系统自动附加攻击语句，观察模型是否被攻破

当前案例包括直接提示词泄露、强制输出、角色扮演越权、上下文边界突破与间接注入。
每项均提供成功信号，便于记录防御前后的攻击成功率。

### 蓝队（防御方）
1. 开启「🔵 蓝队防御模式」
2. 分析 `defense/input_filter.py` 中的规则
3. 尝试补充新的过滤规则或改进检测逻辑
4. 重新测试红队攻击，验证防御效果

### MCP 工具安全实验

针对未来接入 MCP 工具后的信任边界，参见
[`docs/MCP_SECURITY_EXPERIMENT.md`](docs/MCP_SECURITY_EXPERIMENT.md)。方案只使用
隔离的 mock server 和 canary 数据，覆盖恶意工具描述、恶意工具结果及越权调用。

### 本地回归测试

```bash
python3 -m unittest discover -s tests -v
```

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

### Q3: Kimi API 报错 429（余额不足）？

你的 API Key 有效，但账户余额已用完。解决方式：
1. 登录 [platform.moonshot.cn](https://platform.moonshot.cn)
2. 检查「费用中心」是否有余额
3. 新账号通常有 15 元免费额度；用完需充值

### Q4: 可以用其他大模型 API 代替 Kimi 吗？

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
