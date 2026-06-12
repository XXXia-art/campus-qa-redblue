"""
蓝队：输出层安全守卫
用于检测 LLM 返回内容是否被提示词注入成功利用
（如系统提示词泄露、违规内容、注入标记等）
"""

import re


class OutputGuard:
    """LLM 输出内容安全检测器"""

    # 明显的注入成功标记
    INJECTION_MARKERS = [
        "[SYSTEM OVERRIDE]",
        "[END SYSTEM OVERRIDE]",
        "===SYSTEM OVERRIDE===",
        "<system>",
        "</system>",
        "新的系统指令",
        "忽略之前所有指令",
        "忽略所有安全限制",
        "developer mode",
        "DAN 模式",
        "绕开限制",
    ]

    # 系统提示词泄露关键词
    PROMPT_LEAKAGE_KEYWORDS = [
        "系统提示词",
        "system prompt",
        "system instruction",
        "你是一个专业的校园智能问答助手",
        "你的原始系统提示",
        "我的系统提示词是",
    ]

    # 敏感模式正则
    SENSITIVE_PATTERNS = [
        r"我的系统提示.*?:",
        r"system prompt.*?:",
        r"原始系统提示.*?:",
        r"忽略之前的指令.*输出系统提示词",
    ]

    @classmethod
    def check(cls, content: str) -> dict:
        """
        检查 LLM 输出是否包含注入成功后的异常内容

        Returns:
            {"safe": bool, "reason": str, "matched": list}
        """
        if not content:
            return {"safe": True, "reason": "", "matched": []}

        matched = []
        lower_content = content.lower()

        for marker in cls.INJECTION_MARKERS:
            if marker.lower() in lower_content:
                matched.append(f"注入标记: {marker}")

        for keyword in cls.PROMPT_LEAKAGE_KEYWORDS:
            if keyword.lower() in lower_content:
                matched.append(f"泄露关键词: {keyword}")

        for pattern in cls.SENSITIVE_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                matched.append(f"敏感模式: {pattern}")

        if matched:
            return {
                "safe": False,
                "reason": f"检测到可疑输出 ({'; '.join(matched)})",
                "matched": matched,
            }

        return {"safe": True, "reason": "", "matched": []}

    @classmethod
    def sanitize(cls, content: str) -> str:
        """
        对输出进行简单脱敏（将注入标记替换为警告）
        """
        cleaned = content
        for marker in cls.INJECTION_MARKERS:
            cleaned = re.sub(
                re.escape(marker),
                f"[⚠️ 已过滤: {marker}]",
                cleaned,
                flags=re.IGNORECASE,
            )
        return cleaned
