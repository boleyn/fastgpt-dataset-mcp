"""
目录树服务
"""

from typing import List
from ..api_client import api_client
from ..models import DatasetNode
from ..logger import tree_logger


class TreeService:
    """目录树管理服务"""
    
    def __init__(self):
        self.api_client = api_client
    
    async def get_knowledge_base_tree(self, parent_id: str, search_value: str = "", deep: int = 4) -> str:
        """
        获取知识库目录树并格式化为Markdown
        
        Args:
            parent_id: 父级目录ID
            search_value: 搜索关键词
            deep: 目录深度
            
        Returns:
            格式化的Markdown文本
        """
        try:
            tree_logger.info(f"开始获取知识库目录树 | 父级ID: {parent_id[:8]}... | 搜索词: '{search_value}' | 深度: {deep}")
            
            # 递归获取目录树数据
            tree_structure = await self._build_tree_recursively(parent_id, search_value, deep, 0)
            
            if not tree_structure:
                return f"# 📁 知识库目录树\n\n**搜索条件:** {search_value or '无'}\n**深度:** {deep}\n\n*未找到任何内容*\n"
            
            # 格式化为Markdown
            markdown_content = self._format_tree_markdown_recursive(tree_structure, search_value, deep)
            
            total_nodes = self._count_total_nodes(tree_structure)
            tree_logger.info(f"目录树获取完成 | 总节点数: {total_nodes}")
            return markdown_content
            
        except Exception as e:
            tree_logger.error(f"获取知识库目录树失败: {str(e)}", exc_info=True)
            return f"# ❌ 错误\n\n获取知识库目录树时发生错误: {str(e)}"
    
    async def _build_tree_recursively(self, parent_id: str, search_value: str, max_depth: int, current_depth: int) -> List[dict]:
        """递归构建目录树结构"""
        if current_depth >= max_depth:
            return []
        
        try:
            # 获取当前层级的节点（deep=1 只获取直接子节点）
            nodes = await self.api_client.get_dataset_tree(parent_id, search_value, 1)
            
            tree_structure = []
            for node in nodes:
                node_data = {
                    'node': node,
                    'depth': current_depth,
                    'children': []
                }
                
                # 如果是文件夹且未达到最大深度，递归获取子节点
                if node.type == "folder" and current_depth < max_depth - 1:
                    node_data['children'] = await self._build_tree_recursively(
                        node.id, search_value, max_depth, current_depth + 1
                    )
                
                tree_structure.append(node_data)
            
            return tree_structure
            
        except Exception as e:
            tree_logger.warning(f"获取层级 {current_depth} 节点失败: {str(e)}")
            return []
    
    def _format_tree_markdown_recursive(self, tree_structure: List[dict], search_value: str, max_depth: int) -> str:
        """递归格式化目录树为Markdown"""
        total_nodes = self._count_total_nodes(tree_structure)
        
        markdown_lines = [
            "# 📁 知识库目录树",
            "",
            f"**搜索条件:** {search_value or '无'}",
            f"**最大深度:** {max_depth}",
            f"**总节点数:** {total_nodes}",
            ""
        ]
        
        # 递归添加节点
        self._add_nodes_to_markdown(tree_structure, markdown_lines, 0)
        
        return '\n'.join(markdown_lines)
    
    def _add_nodes_to_markdown(self, tree_structure: List[dict], markdown_lines: List[str], depth: int):
        """递归添加节点到Markdown"""
        for node_data in tree_structure:
            node = node_data['node']
            children = node_data['children']
            
            # 计算缩进
            indent = "  " * depth
            
            # 确定图标
            icon = "📚" if node.type == "dataset" else "📁"
            
            # 添加节点信息（简化格式）
            markdown_lines.append(f"{indent}- {icon} **{node.name}**")
            markdown_lines.append(f"{indent}  - ID: `{node.id}`")
            markdown_lines.append(f"{indent}  - 类型: {node.type}")
            
            # 只显示描述（如果有）
            if node.intro and node.intro.strip():
                markdown_lines.append(f"{indent}  - 描述: {node.intro}")
            
            markdown_lines.append("")
            
            # 递归添加子节点
            if children:
                self._add_nodes_to_markdown(children, markdown_lines, depth + 1)
    
    def _count_total_nodes(self, tree_structure: List[dict]) -> int:
        """计算总节点数"""
        total = len(tree_structure)
        for node_data in tree_structure:
            total += self._count_total_nodes(node_data['children'])
        return total
    
    def _format_tree_markdown(self, nodes: List[DatasetNode], search_value: str) -> str:
        """格式化目录树为Markdown（已废弃，保留兼容性）"""
        markdown_lines = [
            "# 📁 知识库目录树",
            "",
            f"**搜索条件:** {search_value or '无'}",
            f"**找到项目数量:** {len(nodes)}",
            ""
        ]
        
        for node in nodes:
            # 确定图标
            icon = "📚" if node.type == "dataset" else "📁"
            
            # 添加节点信息（简化格式，去掉权限等冗余信息）
            markdown_lines.append(f"- {icon} **{node.name}**")
            markdown_lines.append(f"  - ID: `{node.id}`")
            markdown_lines.append(f"  - 类型: {node.type}")
            
            # 只显示描述（如果有）
            if node.intro and node.intro.strip():
                markdown_lines.append(f"  - 描述: {node.intro}")
            
            markdown_lines.append("")
        
        return '\n'.join(markdown_lines) 