"""
蓝队：输入过滤防御模块
用于检测和拦截潜在的提示词注入攻击
"""

import re


class InputFilter:
    """输入安全过滤器"""

    # 危险关键词列表
    DANGEROUS_KEYWORDS = [
        "忽略之前的指令",
        "忽略以上",
        "忽略所有",
        "system prompt",
        "系统提示",
        "内部配置",
        "jailbreak",
        "绕开限制",
        "绕过网站",
        "DAN 模式",
        "developer mode",
    ]

    # 危险模式正则
    DANGEROUS_PATTERNS = [
        r"忽略.*指令",
        r"忽略.*提示",
        r"忽略.*(?:规则|任务|参考资料)",
        r"不再是一个.*AI",
        r"不再受.*限制",
        r"角色扮演.*没有.*限制",
        r"不受限制的.*助手",
        r"(?:逐字输出|披露).*(?:提示词|配置|安全策略)",
    ]

    @classmethod
    def check(cls, user_input: str) -> dict:
        """
        检查用户输入是否安全
        
        Returns:
            {"safe": bool, "reason": str, "matched": list}
        """
        matched = []
        normalized_input = re.sub(r"\s+", "", user_input)
        lower_input = normalized_input.lower()

        # 关键词匹配
        for keyword in cls.DANGEROUS_KEYWORDS:
            if keyword.lower() in lower_input:
                matched.append(f"关键词: '{keyword}'")

        # 正则模式匹配
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, normalized_input, re.IGNORECASE):
                matched.append(f"模式: '{pattern}'")

        if matched:
            return {
                "safe": False,
                "reason": f"检测到可疑输入 ({'; '.join(matched)})",
                "matched": matched
            }

        return {"safe": True, "reason": "", "matched": []}

    @classmethod
    def sanitize(cls, user_input: str) -> str:
        """
        对输入进行简单的清洗（转义特殊标记）
        """
        # 替换可能用于截断/注入的分隔符
        sanitized = user_input.replace("---", "—")
        sanitized = sanitized.replace("```", "")
        return sanitized
