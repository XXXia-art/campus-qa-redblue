"""
MCP (Model Context Protocol) 协议核心实现
用于教学演示：纯 Python 类实现 MCP Server/Client，无需外部依赖
"""

from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass, field


@dataclass
class MCPTool:
    """MCP 工具定义"""
    name: str
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    handler: Callable = None
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }


@dataclass
class MCPResource:
    """MCP 资源定义"""
    uri: str
    name: str
    description: str
    content: str = ""
    mime_type: str = "text/plain"
    
    def to_dict(self) -> dict:
        return {
            "uri": self.uri,
            "name": self.name,
            "description": self.description,
            "mimeType": self.mime_type,
        }


class MCPServer:
    """
    MCP Server 实现
    支持注册工具、资源，处理客户端调用
    """
    
    def __init__(self, name: str, description: str, version: str = "1.0.0"):
        self.name = name
        self.description = description
        self.version = version
        self.tools: Dict[str, MCPTool] = {}
        self.resources: Dict[str, MCPResource] = {}
        self.call_log: List[dict] = []
    
    def register_tool(self, tool: MCPTool):
        """注册工具"""
        self.tools[tool.name] = tool
    
    def register_resource(self, resource: MCPResource):
        """注册资源"""
        self.resources[resource.uri] = resource
    
    def list_tools(self) -> List[dict]:
        """列出所有工具"""
        return [t.to_dict() for t in self.tools.values()]
    
    def list_resources(self) -> List[dict]:
        """列出所有资源"""
        return [r.to_dict() for r in self.resources.values()]
    
    def call_tool(self, tool_name: str, arguments: dict) -> dict:
        """
        调用工具
        
        Returns:
            {"success": bool, "result": Any, "error": str}
        """
        if tool_name not in self.tools:
            return {"success": False, "result": None, "error": f"Tool '{tool_name}' not found"}
        
        tool = self.tools[tool_name]
        self.call_log.append({"tool": tool_name, "arguments": arguments})
        
        try:
            if tool.handler:
                result = tool.handler(**arguments)
                return {"success": True, "result": result, "error": None}
            else:
                return {"success": False, "result": None, "error": "Tool has no handler"}
        except Exception as e:
            return {"success": False, "result": None, "error": str(e)}
    
    def read_resource(self, uri: str) -> dict:
        """读取资源内容"""
        if uri not in self.resources:
            return {"success": False, "content": None, "error": f"Resource '{uri}' not found"}
        
        resource = self.resources[uri]
        return {
            "success": True,
            "content": resource.content,
            "mimeType": resource.mime_type,
            "error": None,
        }
    
    def get_info(self) -> dict:
        """获取 Server 信息"""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "tools_count": len(self.tools),
            "resources_count": len(self.resources),
        }


class MCPClient:
    """
    MCP Client 实现
    连接到 MCP Server，发现工具/资源并调用
    """
    
    def __init__(self):
        self.server: Optional[MCPServer] = None
        self.discovered_tools: List[dict] = []
        self.discovered_resources: List[dict] = []
    
    def connect(self, server: MCPServer):
        """连接到 MCP Server"""
        self.server = server
        # 自动发现工具和资源
        self.discovered_tools = server.list_tools()
        self.discovered_resources = server.list_resources()
    
    def list_tools(self) -> List[dict]:
        """列出已发现的工具"""
        return self.discovered_tools
    
    def list_resources(self) -> List[dict]:
        """列出已发现的资源"""
        return self.discovered_resources
    
    def call_tool(self, tool_name: str, **kwargs) -> dict:
        """调用远程工具"""
        if not self.server:
            return {"success": False, "error": "Not connected to any server"}
        return self.server.call_tool(tool_name, kwargs)
    
    def read_resource(self, uri: str) -> dict:
        """读取远程资源"""
        if not self.server:
            return {"success": False, "error": "Not connected to any server"}
        return self.server.read_resource(uri)
    
    def get_server_info(self) -> dict:
        """获取连接的服务器信息"""
        if not self.server:
            return {"error": "Not connected"}
        return self.server.get_info()
