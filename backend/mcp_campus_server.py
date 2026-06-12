"""
校园 MCP Server 实现
提供正常的校园服务工具（图书馆查询、校园卡查询等）
"""

from backend.mcp_protocol import MCPServer, MCPTool, MCPResource


def create_campus_mcp_server() -> MCPServer:
    """
    创建正常的校园 MCP Server
    """
    server = MCPServer(
        name="seu-campus-helper",
        description="东南大学校园助手 MCP Server，提供图书馆、校园卡、课表等查询服务",
        version="1.0.0",
    )
    
    # === 工具1：查询图书馆藏书 ===
    server.register_tool(MCPTool(
        name="query_library_books",
        description="查询东南大学图书馆的馆藏图书信息",
        parameters={
            "book_name": {"type": "string", "description": "书名或关键词"},
            "campus": {"type": "string", "description": "校区（九龙湖/四牌楼/丁家桥）", "enum": ["九龙湖", "四牌楼", "丁家桥"]},
        },
        handler=lambda book_name, campus="九龙湖": {
            "campus": campus,
            "query": book_name,
            "results": [
                {"title": f"《{book_name}》", "location": f"{campus}校区图书馆3楼", "status": "可借阅"},
                {"title": f"《{book_name}（第2版）》", "location": f"{campus}校区图书馆5楼", "status": "已借出"},
            ],
            "total": 2,
        }
    ))
    
    # === 工具2：查询校园卡余额 ===
    server.register_tool(MCPTool(
        name="get_campus_card_balance",
        description="查询校园卡余额和最近消费记录",
        parameters={
            "card_id": {"type": "string", "description": "校园卡号（学号/工号）"},
        },
        handler=lambda card_id: {
            "card_id": card_id,
            "balance": 47.50,
            "recent_transactions": [
                {"time": "2024-01-15 12:30", "location": "桃园食堂", "amount": -15.00},
                {"time": "2024-01-15 08:15", "location": "橘园超市", "amount": -8.50},
                {"time": "2024-01-14 18:20", "location": "梅园食堂", "amount": -12.00},
            ]
        }
    ))
    
    # === 工具3：查询课表 ===
    server.register_tool(MCPTool(
        name="check_course_schedule",
        description="查询指定日期的课程安排",
        parameters={
            "student_id": {"type": "string", "description": "学号"},
            "date": {"type": "string", "description": "日期（YYYY-MM-DD）"},
        },
        handler=lambda student_id, date: {
            "student_id": student_id,
            "date": date,
            "courses": [
                {"time": "08:00-09:35", "name": "高等数学A", "room": "教一101", "teacher": "张教授"},
                {"time": "10:00-11:35", "name": "线性代数", "room": "教二305", "teacher": "李教授"},
                {"time": "14:00-15:35", "name": "Python程序设计", "room": "计算机楼A201", "teacher": "王教授"},
            ]
        }
    ))
    
    # === 工具4：查询校车时刻 ===
    server.register_tool(MCPTool(
        name="get_shuttle_schedule",
        description="查询四牌楼↔九龙湖校区班车时刻表",
        parameters={
            "direction": {"type": "string", "description": "方向", "enum": ["四牌楼→九龙湖", "九龙湖→四牌楼"]},
            "date": {"type": "string", "description": "日期（YYYY-MM-DD）"},
        },
        handler=lambda direction, date: {
            "direction": direction,
            "date": date,
            "schedules": [
                {"time": "07:30", "from": direction.split("→")[0].strip(), "to": direction.split("→")[1].strip(), "seats": "充足"},
                {"time": "12:00", "from": direction.split("→")[0].strip(), "to": direction.split("→")[1].strip(), "seats": "紧张"},
                {"time": "17:30", "from": direction.split("→")[0].strip(), "to": direction.split("→")[1].strip(), "seats": "充足"},
            ]
        }
    ))
    
    # === 资源1：校园地图 ===
    server.register_resource(MCPResource(
        uri="campus://map/jiulonghu",
        name="九龙湖校区地图",
        description="九龙湖校区平面图，标注主要建筑位置",
        content="""
【九龙湖校区地图】

主要区域：
- 教学区：教一~教八、图书馆、计算机楼
- 生活区：桃园、梅园、橘园宿舍区
- 运动区：体育馆、田径场、游泳馆
- 行政区：行政楼、金智楼

交通：
- 地铁3号线"东大九龙湖校区站"
- 校内班车循环线
""",
    ))
    
    # === 资源2：图书馆借阅规则 ===
    server.register_resource(MCPResource(
        uri="campus://library/borrow_rules",
        name="图书馆借阅规则",
        description="东南大学图书馆图书借阅相关规定",
        content="""
【图书借阅规则】

1. 本科生每次可借30册图书
2. 借期30天，可续借2次
3. 逾期罚款：中文图书0.05元/天，外文图书0.20元/天
4. 寒暑假内到期的图书，假期结束后7日内归还不算逾期
""",
    ))
    
    return server
