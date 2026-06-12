"""
蓝队：网络层 Prompt 注入防御 addon（mitmproxy）

部署位置：攻击者代理下游的可信安全网关。
流量路径示例：
    受害者 App → 攻击者 mitmproxy（可能注入） → 蓝队 mitmproxy（本 addon） → LLM API

当检测到 .blue_team_enabled 标志时，对 LLM API 请求进行：
- 检测最后一条 user 消息中是否包含已知的注入标记
- 模式为 sanitize：剥离注入载荷后放行
- 模式为 block：直接返回 403/拦截响应
"""

import json
import os
import re
from mitmproxy import http


TARGET_HOSTS = [
    "api.xiaomimimo.com",
    "api.moonshot.cn",
    "api.openai.com",
    "api.anthropic.com",
]

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
BLUE_FLAG_FILE = os.path.join(PROJECT_DIR, ".blue_team_enabled")
BLUE_MODE_FILE = os.path.join(PROJECT_DIR, ".blue_team_mode")

# 注入标记/关键词（与 defense/output_guard.py 保持一致）
INJECTION_MARKERS = [
    "[SYSTEM OVERRIDE]",
    "[END SYSTEM OVERRIDE]",
    "===SYSTEM OVERRIDE===",
    "<system>",
    "</system>",
    "新的系统指令",
    "忽略之前所有指令",
    "忽略之前的指令",
    "忽略所有安全限制",
    "developer mode",
    "DAN 模式",
    "绕开限制",
    "jailbreak",
    "system prompt",
    "系统提示词",
]

# 明显的注入模式正则
INJECTION_PATTERNS = [
    r"忽略.*指令",
    r"忽略.*提示",
    r"不再是一个.*AI",
    r"不再受.*限制",
    r"角色扮演.*没有.*限制",
]


def _is_blue_team_enabled() -> bool:
    return os.path.exists(BLUE_FLAG_FILE)


def _load_mode() -> str:
    if os.path.exists(BLUE_MODE_FILE):
        try:
            with open(BLUE_MODE_FILE, "r", encoding="utf-8") as f:
                mode = f.read().strip().lower()
                if mode in ("sanitize", "block"):
                    return mode
        except Exception:
            pass
    return "sanitize"


def _detect_injection(text: str) -> tuple:
    """检测文本中是否包含注入标记，返回 (是否注入, 命中的标记列表)"""
    matched = []
    lower_text = text.lower()

    for marker in INJECTION_MARKERS:
        if marker.lower() in lower_text:
            matched.append(marker)

    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            matched.append(f"模式: {pattern}")

    return bool(matched), matched


def _strip_injection(text: str) -> str:
    """从第一个注入标记处截断，移除后续载荷"""
    lower_text = text.lower()
    cut_pos = len(text)

    for marker in INJECTION_MARKERS:
        idx = lower_text.find(marker.lower())
        if idx != -1 and idx < cut_pos:
            cut_pos = idx

    for pattern in INJECTION_PATTERNS:
        m = re.search(pattern, text, re.IGNORECASE)
        if m and m.start() < cut_pos:
            cut_pos = m.start()

    if cut_pos < len(text):
        return text[:cut_pos].rstrip()
    return text


def _build_block_response(matched: list) -> bytes:
    """构造一个合成的 OpenAI 格式拦截响应"""
    reason = "; ".join(matched[:3]) if matched else "检测到提示词注入"
    body = {
        "id": "blue-team-block",
        "object": "chat.completion",
        "created": 0,
        "model": "blue-team-defense",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": (
                        f"🛡️ 【网络层防御拦截】蓝队代理检测到提示词注入攻击，"
                        f"已阻断该请求。\n\n命中规则：{reason}"
                    ),
                },
                "finish_reason": "stop",
            }
        ],
    }
    return json.dumps(body, ensure_ascii=False).encode("utf-8")


def request(flow: http.HTTPFlow) -> None:
    if not _is_blue_team_enabled():
        return

    if not any(target in flow.request.pretty_host for target in TARGET_HOSTS):
        return

    if "/chat/completions" not in flow.request.path:
        return

    try:
        body = json.loads(flow.request.content or "{}")
    except Exception:
        return

    messages = body.get("messages", [])
    if not messages:
        return

    # 定位最后一条 user 消息（这也是 MITM 注入通常修改的位置）
    last_user_idx = -1
    for i in range(len(messages) - 1, -1, -1):
        if messages[i].get("role") == "user":
            last_user_idx = i
            break

    if last_user_idx == -1:
        return

    original_content = messages[last_user_idx].get("content", "")
    is_injection, matched = _detect_injection(original_content)

    if not is_injection:
        return

    mode = _load_mode()

    if mode == "block":
        flow.response = http.Response.make(
            200,
            _build_block_response(matched),
            {"Content-Type": "application/json"},
        )
        return

    # sanitize 模式：清洗后放行
    cleaned_content = _strip_injection(original_content)
    messages[last_user_idx]["content"] = cleaned_content
    body["messages"] = messages
    flow.request.content = json.dumps(body, ensure_ascii=False).encode("utf-8")
    flow.request.headers["X-Blue-Team-Sanitized"] = "true"
    flow.request.headers["X-Blue-Team-Matched"] = "; ".join(matched[:3])
