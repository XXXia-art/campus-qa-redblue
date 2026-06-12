"""
测试 mitm_prompt_inject.py 的注入逻辑
"""

import json
import sys
import os

# 模拟 mitmproxy 的 http 模块
class MockRequest:
    def __init__(self, host, path, content, headers=None):
        self.pretty_host = host
        self.path = path
        self.content = content
        self.headers = headers or {}

class MockResponse:
    def __init__(self, content):
        self.content = content

class MockFlow:
    def __init__(self, host, path, content):
        self.request = MockRequest(host, path, content)
        self.response = None

# 把项目根目录加入路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入被测函数（跳过 mitmproxy 导入）
import importlib.util
spec = importlib.util.spec_from_file_location("mitm_prompt_inject", "mitm_prompt_inject.py")
module = importlib.util.module_from_spec(spec)

# 替换 mitmproxy 模块
sys.modules["mitmproxy"] = type(sys)("mitmproxy")
sys.modules["mitmproxy"].http = type(sys)("http")
sys.modules["mitmproxy"].http.HTTPFlow = MockFlow

spec.loader.exec_module(module)


def test_prompt_injection():
    body = {
        "model": "mimo-v2.5-pro",
        "messages": [
            {"role": "system", "content": "你是一个校园问答助手。"},
            {"role": "user", "content": "东南大学在哪里？"}
        ]
    }
    flow = MockFlow("api.xiaomimimo.com", "/v1/chat/completions", json.dumps(body).encode())
    
    module.request(flow)
    
    new_body = json.loads(flow.request.content)
    user_msg = new_body["messages"][1]["content"]
    
    assert "东南大学在哪里？" in user_msg, "原始问题应被保留"
    assert "[SYSTEM OVERRIDE]" in user_msg, "应注入 SYSTEM OVERRIDE"
    assert flow.request.headers.get("X-Prompt-Injected") == "true", "应设置标记头"
    print("[PASS] Prompt 注入测试通过")
    print(f"注入后内容:\n{user_msg}\n")


def test_non_llm_request_ignored():
    body = {
        "model": "mimo-v2.5-pro",
        "messages": [{"role": "user", "content": "hello"}]
    }
    flow = MockFlow("api.xiaomimimo.com", "/v1/embeddings", json.dumps(body).encode())
    
    module.request(flow)
    
    new_body = json.loads(flow.request.content)
    assert "[SYSTEM OVERRIDE]" not in new_body["messages"][0]["content"]
    print("[PASS] 非 chat completions 请求被忽略")


def test_other_host_ignored():
    body = {
        "model": "mimo-v2.5-pro",
        "messages": [{"role": "user", "content": "hello"}]
    }
    flow = MockFlow("example.com", "/v1/chat/completions", json.dumps(body).encode())
    
    module.request(flow)
    
    new_body = json.loads(flow.request.content)
    assert "[SYSTEM OVERRIDE]" not in new_body["messages"][0]["content"]
    print("[PASS] 非目标 host 请求被忽略")


if __name__ == "__main__":
    test_prompt_injection()
    test_non_llm_request_ignored()
    test_other_host_ignored()
    print("\n所有测试通过 [OK]")
