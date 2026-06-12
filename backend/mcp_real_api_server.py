"""
真实外部 API MCP Server
调用无需 API Key 的公开接口
"""

import requests
from backend.mcp_protocol import MCPServer, MCPTool


def create_real_api_mcp_server() -> MCPServer:
    """
    创建真实外部 API MCP Server
    工具调用时会发出真实的 HTTP 请求
    """
    server = MCPServer(
        name="real-api-gateway",
        description="真实外部 API 网关：天气查询、IP 定位等",
        version="1.0.0",
    )
    
    # === 工具1：查询天气（wttr.in）===
    def get_weather(city: str = "Nanjing", format_type: str = "json") -> dict:
        """
        调用 wttr.in 查询指定城市天气
        https://github.com/chubin/wttr.in
        """
        try:
            # wttr.in 支持中文城市名，但需要 URL 编码
            url = f"https://wttr.in/{city}?format=j1"
            headers = {"User-Agent": "curl/7.68.0"}  # wttr.in 对 curl 友好
            resp = requests.get(url, headers=headers, timeout=15, verify=False)
            resp.raise_for_status()
            data = resp.json()
            
            # 提取关键信息
            current = data.get("current_condition", [{}])[0]
            weather = {
                "city": city,
                "query_time": current.get("localObsDateTime", "unknown"),
                "temperature_c": current.get("temp_C"),
                "temperature_f": current.get("temp_F"),
                "feels_like_c": current.get("FeelsLikeC"),
                "weather_desc": current.get("lang_zh", [{}])[0].get("value") if current.get("lang_zh") else current.get("weatherDesc", [{}])[0].get("value"),
                "humidity": current.get("humidity"),
                "wind_speed": current.get("windspeedKmph"),
                "wind_dir": current.get("winddir16Point"),
                "visibility": current.get("visibility"),
                "pressure": current.get("pressure"),
                "uv_index": current.get("uvIndex"),
                "forecast_3days": [],
            }
            
            # 未来3天预报
            for day in data.get("weather", [])[:3]:
                weather["forecast_3days"].append({
                    "date": day.get("date"),
                    "max_temp_c": day.get("maxtempC"),
                    "min_temp_c": day.get("mintempC"),
                    "avg_temp_c": day.get("avgtempC"),
                    "condition": day.get("hourly", [{}])[0].get("lang_zh", [{}])[0].get("value") if day.get("hourly") else "unknown",
                })
            
            return {
                "success": True,
                "source": "wttr.in",
                "data": weather,
            }
        except requests.exceptions.Timeout:
            return {"success": False, "error": "请求超时，请稍后重试"}
        except requests.exceptions.ConnectionError:
            return {"success": False, "error": "网络连接失败，请检查网络/代理设置"}
        except Exception as e:
            return {"success": False, "error": f"请求失败: {str(e)}"}
    
    server.register_tool(MCPTool(
        name="get_weather",
        description="查询指定城市的实时天气和未来3天预报（数据来源：wttr.in）",
        parameters={
            "city": {"type": "string", "description": "城市名（支持中文，如：南京、北京、上海）"},
        },
        handler=get_weather,
    ))
    
    # === 工具2：IP 地理位置查询 ===
    def get_ip_location(ip: str = "") -> dict:
        """
        调用 ip-api.com 查询 IP 地理位置
        """
        try:
            target = ip if ip else "check"
            url = f"http://ip-api.com/json/{target}?lang=zh-CN"
            resp = requests.get(url, timeout=10, verify=False)
            resp.raise_for_status()
            data = resp.json()
            
            if data.get("status") != "success":
                return {"success": False, "error": data.get("message", "查询失败")}
            
            return {
                "success": True,
                "source": "ip-api.com",
                "data": {
                    "ip": data.get("query"),
                    "country": data.get("country"),
                    "region": data.get("regionName"),
                    "city": data.get("city"),
                    "district": data.get("district", ""),
                    "zip": data.get("zip"),
                    "lat": data.get("lat"),
                    "lon": data.get("lon"),
                    "timezone": data.get("timezone"),
                    "isp": data.get("isp"),
                    "org": data.get("org"),
                }
            }
        except requests.exceptions.Timeout:
            return {"success": False, "error": "请求超时"}
        except requests.exceptions.ConnectionError:
            return {"success": False, "error": "网络连接失败"}
        except Exception as e:
            return {"success": False, "error": f"请求失败: {str(e)}"}
    
    server.register_tool(MCPTool(
        name="get_ip_location",
        description="查询指定 IP 地址的地理位置（留空查询本机）",
        parameters={
            "ip": {"type": "string", "description": "IP 地址（如：8.8.8.8），留空查本机"},
        },
        handler=get_ip_location,
    ))
    
    # === 工具3：校园周边天气（结合校园场景）===
    def get_campus_weather(campus: str = "九龙湖") -> dict:
        """
        查询东南大学各校区所在区域的天气
        """
        campus_locations = {
            "九龙湖": "Nanjing",
            "四牌楼": "Nanjing",
            "丁家桥": "Nanjing",
            "无锡": "Wuxi",
            "苏州": "Suzhou",
        }
        city = campus_locations.get(campus, "Nanjing")
        return get_weather(city)
    
    server.register_tool(MCPTool(
        name="get_campus_weather",
        description="查询东南大学各校区（南京/无锡/苏州）的实时天气",
        parameters={
            "campus": {"type": "string", "description": "校区名", "enum": ["九龙湖", "四牌楼", "丁家桥", "无锡", "苏州"]},
        },
        handler=get_campus_weather,
    ))
    
    return server
