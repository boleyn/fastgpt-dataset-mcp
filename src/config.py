"""
配置管理模块
"""

import os
from typing import Optional
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class Config:
    """应用配置类"""
    
    def __init__(self):
        # API配置
        self.api_base_url = os.getenv("KNOWLEDGE_BASE_URL", "http://10.21.8.6:13000")
        self.api_token = os.getenv("KNOWLEDGE_BASE_TOKEN", "aichat-pkBusvYZJAqYoDlXLGtw4KhFF6y8AJOdYwpMzbmlm5zfCSiBICmOAv")
        
        # MCP服务器配置
        self.mcp_host = os.getenv('MCP_SERVER_HOST', '0.0.0.0')
        self.mcp_port = int(os.getenv('MCP_SERVER_PORT', '8000'))
        
        # 知识库配置
        self.default_parent_id = os.getenv("DEFAULT_PARENT_ID", "683462ea7420db05db65b810")
        
        # 搜索配置
        self.search_mode = "embedding"
        self.embedding_weight = 0.5
        self.using_rerank = True
        self.rerank_weight = 0.5
    
    @property
    def api_headers(self) -> dict:
        """获取API请求头"""
        return {
            'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_token}',
            'Accept': '*/*',
            'Host': self.api_base_url.split('//')[-1],
            'Connection': 'keep-alive'
        }
    
    def get_parent_id(self, override: Optional[str] = None) -> str:
        """获取父级ID"""
        if override:
            return override
            
        # 检查命令行参数
        import sys
        for i, arg in enumerate(sys.argv):
            if arg == "--parent-id" and i + 1 < len(sys.argv):
                return sys.argv[i + 1]
            elif arg.startswith("--parent-id="):
                return arg.split("=", 1)[1]
        
        # 检查环境变量
        return os.getenv("PARENT_ID") or self.default_parent_id


# 全局配置实例
config = Config() 