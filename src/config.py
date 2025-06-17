"""
配置管理模块
"""

import os
import json
import re
from typing import Optional, Set, List
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
        self.default_parent_id = os.getenv("DEFAULT_PARENT_ID", "7777")
        
        # 搜索配置
        self.search_mode = "embedding"
        self.embedding_weight = 0.5
        self.using_rerank = True
        self.rerank_weight = 0.5
        
        # 权限配置（从JSON文件加载）
        self.special_access_users, self.restricted_datasets = self._load_permissions()
        
        # 动态生成正则表达式
        self._phone_regex = self._build_phone_regex()
        
        # 运行时parentId（从SSE URL参数设置）
        self._runtime_parent_id: Optional[str] = None
    
    def _parse_set_config(self, env_key: str, default_value: str) -> Set[str]:
        """解析环境变量配置为Set类型"""
        value = os.getenv(env_key, default_value)
        return {item.strip() for item in value.split(',') if item.strip()}
    
    def _load_permissions(self) -> tuple[Set[str], Set[str]]:
        """加载权限配置，优先从JSON文件读取，其次从环境变量"""
        # 1. 尝试从统一权限配置文件读取
        config_file = "config/permissions.json"
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                special_users = set(data.get("special_users", []))
                restricted_datasets = set(data.get("restricted_datasets", []))
                
                if special_users or restricted_datasets:
                    return special_users, restricted_datasets
            except Exception as e:
                print(f"⚠️  读取权限配置文件失败: {e}")
        
        # 2. 兜底：从环境变量读取（兼容旧配置）
        special_users = self._parse_set_config("SPECIAL_ACCESS_USERS", "")
        restricted_datasets = self._parse_set_config("RESTRICTED_DATASETS", "")
        
        return special_users, restricted_datasets
    
    def _build_phone_regex(self) -> str:
        """从手机号列表动态构建正则表达式"""
        if not self.special_access_users:
            return ""
        
        # 将手机号列表拼接成正则表达式
        phone_list = "|".join(self.special_access_users)
        return f"^(?:{phone_list})$"
    
    def _is_special_user_by_regex(self, userid: str) -> bool:
        """通过动态生成的正则表达式匹配特殊用户"""
        if not self._phone_regex:
            return False
        
        try:
            return bool(re.match(self._phone_regex, userid))
        except re.error as e:
            print(f"⚠️  正则表达式匹配错误: {e}")
            return False
    
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
    
    def set_runtime_parent_id(self, parent_id: str) -> None:
        """设置运行时的parentId（通常从SSE URL参数获取）"""
        self._runtime_parent_id = parent_id
    
    def get_parent_id(self, override: Optional[str] = None) -> str:
        """获取父级ID"""
        if override:
            return override
        
        # 优先使用运行时设置的parentId（来自SSE URL参数）
        if self._runtime_parent_id:
            return self._runtime_parent_id
            
        # 检查命令行参数
        import sys
        for i, arg in enumerate(sys.argv):
            if arg == "--parent-id" and i + 1 < len(sys.argv):
                return sys.argv[i + 1]
            elif arg.startswith("--parent-id="):
                return arg.split("=", 1)[1]
        
        # 检查环境变量
        return os.getenv("PARENT_ID") or self.default_parent_id

    def has_dataset_access(self, userid: str, dataset_id: str) -> bool:
        """检查用户是否有权限访问指定数据集"""
        # 如果不是受限数据集，所有用户都可以访问
        if dataset_id not in self.restricted_datasets:
            return True
        
        # 如果是受限数据集，检查是否为特殊用户
        return self.is_special_user(userid)

    def is_special_user(self, userid: str) -> bool:
        """检查是否为特殊用户（使用动态生成的正则表达式）"""
        # 使用动态生成的正则表达式匹配
        return self._is_special_user_by_regex(userid)

    def get_user_role(self, userid: str) -> str:
        """获取用户角色"""
        if self.is_special_user(userid):
            return "特殊用户"
        else:
            return "普通用户"


# 全局配置实例
config = Config() 