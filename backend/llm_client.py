from openai import OpenAI
from backend.config import KIMI_API_KEY, KIMI_BASE_URL, KIMI_MODEL


class KimiClient:
    """Kimi API 客户端（OpenAI 兼容格式）"""

    def __init__(self):
        if not KIMI_API_KEY:
            raise ValueError("❌ KIMI_API_KEY 未设置！请复制 .env.example 为 .env 并填入你的 API Key")
        self.client = OpenAI(api_key=KIMI_API_KEY, base_url=KIMI_BASE_URL)
        self.model = KIMI_MODEL

    def chat(self, system_prompt: str, user_prompt: str, temperature: float = 0.7) -> str:
        """
        调用 Kimi API 进行对话
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                stream=False
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"[Kimi API 调用错误] {e}"

    def chat_stream(self, system_prompt: str, user_prompt: str, temperature: float = 0.7):
        """
        流式调用 Kimi API（用于 Web 前端实时显示）
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        try:
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                stream=True
            )
            for chunk in stream:
                content = chunk.choices[0].delta.content
                if content:
                    yield content
        except Exception as e:
            yield f"[Kimi API 调用错误] {e}"
