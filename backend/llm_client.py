from backend.config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL


def _is_anthropic_endpoint(url: str) -> bool:
    """判断是否为 Anthropic 兼容端点
    
    以 /v1 结尾的通常走 OpenAI 兼容格式（包括 Mimo 的 OpenAI 端点）
    只有明确包含 anthropic 关键字且不是 /v1 端点才走 Anthropic 格式
    """
    url_lower = url.lower()
    if "/v1" in url_lower:
        return False
    return "anthropic" in url_lower


class LLMClient:
    """通用 LLM 客户端，自动适配 OpenAI / Anthropic 格式"""

    def __init__(self):
        if not LLM_API_KEY:
            raise ValueError("❌ LLM_API_KEY 未设置！请复制 .env.example 为 .env 并填入你的 API Key")

        self.is_anthropic = _is_anthropic_endpoint(LLM_BASE_URL)
        self.model = LLM_MODEL

        if self.is_anthropic:
            from anthropic import Anthropic
            # Mimo 可能需要 Bearer Token 而不是 x-api-key
            self.client = Anthropic(
                base_url=LLM_BASE_URL,
                default_headers={"Authorization": f"Bearer {LLM_API_KEY}"}
            )
        else:
            from openai import OpenAI
            self.client = OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)

    def chat(self, system_prompt: str, user_prompt: str, temperature: float = 0.7) -> str:
        """调用 LLM API 进行对话"""
        try:
            if self.is_anthropic:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=4096,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}],
                    temperature=temperature,
                )
                return response.content[0].text
            else:
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    stream=False
                )
                return response.choices[0].message.content
        except Exception as e:
            return f"[LLM API 调用错误] {e}"

    def chat_stream(self, system_prompt: str, user_prompt: str, temperature: float = 0.7):
        """流式调用 LLM API（用于 Web 前端实时显示）"""
        try:
            if self.is_anthropic:
                with self.client.messages.stream(
                    model=self.model,
                    max_tokens=4096,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}],
                    temperature=temperature,
                ) as stream:
                    for text in stream.text_stream:
                        if text:
                            yield text
            else:
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
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
            yield f"[LLM API 调用错误] {e}"
