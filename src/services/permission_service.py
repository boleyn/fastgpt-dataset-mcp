"""
权限服务模块

提供用户权限验证和数据集访问控制功能
"""

from typing import List, Set
from ..config import config
from ..logger import server_logger


class PermissionService:
    """权限管理服务"""
    
    def __init__(self):
        self.config = config
        
    def is_special_user(self, userid: str) -> bool:
        """检查是否为特殊用户"""
        return self.config.is_special_user(userid)
    
    def has_dataset_access(self, userid: str, dataset_id: str) -> bool:
        """检查用户是否有权限访问指定数据集"""
        return self.config.has_dataset_access(userid, dataset_id)
    
    def filter_allowed_datasets(self, userid: str, dataset_ids: List[str]) -> List[str]:
        """
        过滤用户有权限访问的数据集列表
        
        Args:
            userid: 用户ID
            dataset_ids: 数据集ID列表
            
        Returns:
            过滤后的数据集ID列表
        """
        allowed_datasets = []
        
        for dataset_id in dataset_ids:
            if self.has_dataset_access(userid, dataset_id):
                allowed_datasets.append(dataset_id)
            else:
                server_logger.info(f"用户 {userid} 无权限访问受限数据集: {dataset_id}")
        
        return allowed_datasets
    
    def filter_dataset_nodes(self, userid: str, nodes: List) -> List:
        """
        过滤数据集节点列表，移除无权限访问的受限数据集
        
        Args:
            userid: 用户ID
            nodes: 数据集节点列表
            
        Returns:
            过滤后的节点列表
        """
        if not nodes:
            return nodes
            
        filtered_nodes = []
        restricted_count = 0
        
        for node in nodes:
            # 检查是否为数据集类型且是受限数据集
            if hasattr(node, 'type') and node.type == 'dataset':
                if hasattr(node, 'id') and node.id in self.config.restricted_datasets:
                    # 是受限数据集，检查用户权限
                    if not self.is_special_user(userid):
                        restricted_count += 1
                        server_logger.info(f"过滤受限数据集: {node.id[:8]}... (用户 {userid} 无权限)")
                        continue
            
            filtered_nodes.append(node)
        
        if restricted_count > 0:
            server_logger.info(f"权限过滤完成: 过滤了 {restricted_count} 个受限数据集")
        
        return filtered_nodes
    
    def check_dataset_permission(self, userid: str, dataset_id: str) -> bool:
        """检查数据集权限（装饰器使用）"""
        return self.has_dataset_access(userid, dataset_id)
    
    def check_tool_permission(self, userid: str, tool_name: str) -> bool:
        """检查工具权限（装饰器使用）"""
        # 目前所有工具都允许访问，主要通过数据集权限控制
        return True
    
    def validate_search_limit(self, userid: str, limit: int) -> int:
        """验证搜索限制（装饰器使用）"""
        # 特殊用户无限制，普通用户最多50条
        if self.is_special_user(userid):
            return limit
        else:
            return min(limit, 50)
    
    def can_view_collections(self, userid: str) -> bool:
        """检查是否可以查看集合内容（装饰器使用）"""
        return True
    
    def can_explore_folders(self, userid: str) -> bool:
        """检查是否可以探索文件夹（装饰器使用）"""
        return True
    
    def get_user_role(self, userid: str) -> str:
        """获取用户角色"""
        return self.config.get_user_role(userid)


# 创建全局权限服务实例
permission_service = PermissionService() 