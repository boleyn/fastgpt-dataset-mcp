"""
目录树服务
"""

from typing import List, Dict, Any, Set
import asyncio
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
            search_value: 搜索关键词（支持空格分隔的多个关键词）
            deep: 目录深度
            
        Returns:
            格式化的Markdown文本
        """
        try:
            # 处理多关键词搜索
            keywords = self._parse_search_keywords(search_value)
            tree_logger.info(f"开始获取知识库目录树 | 父级ID: {parent_id[:8]}... | 搜索词: {keywords} | 深度: {deep}")
            
            if keywords:
                # 使用多关键词客户端过滤搜索
                tree_structure = await self._build_tree_with_client_filter(parent_id, keywords, deep)
            else:
                # 无搜索词，获取完整目录树
                tree_structure = await self._build_tree_recursively(parent_id, "", deep, 0)
            
            if not tree_structure:
                return f"# 📁 知识库目录树\n\n**搜索条件:** {search_value or '无'}\n**深度:** {deep}\n\n*未找到任何匹配的内容*\n"
            
            # 格式化为Markdown
            markdown_content = self._format_tree_markdown_recursive(tree_structure, search_value, deep)
            
            total_nodes = self._count_total_nodes(tree_structure)
            tree_logger.info(f"目录树获取完成 | 匹配节点数: {len(tree_structure)} | 总节点数(含子节点): {total_nodes}")
            return markdown_content
            
        except Exception as e:
            tree_logger.error(f"获取知识库目录树失败: {str(e)}", exc_info=True)
            return f"# ❌ 错误\n\n获取知识库目录树时发生错误: {str(e)}"
    
    def _parse_search_keywords(self, search_value: str) -> List[str]:
        """解析搜索关键词，支持空格分隔"""
        if not search_value or not search_value.strip():
            return []
        
        # 按空格分割并过滤空字符串
        keywords = [kw.strip() for kw in search_value.split() if kw.strip()]
        
        if len(keywords) > 1:
            tree_logger.info(f"检测到多个搜索关键词: {keywords}")
        
        return keywords
    
    async def _build_tree_with_client_filter(self, parent_id: str, keywords: List[str], max_depth: int) -> List[dict]:
        """使用客户端过滤实现多关键词搜索"""
        tree_logger.info(f"开始客户端多关键词搜索 | 关键词数: {len(keywords)}")
        
        # 先获取完整的目录树（不使用服务器端搜索，因为它不起作用）
        full_tree = await self._build_tree_recursively(parent_id, "", max_depth, 0)
        tree_logger.info(f"获取完整目录树 | 总节点数: {self._count_total_nodes(full_tree)}")
        
        # 客户端过滤：查找匹配任一关键词的节点
        filtered_nodes = self._filter_nodes_by_keywords(full_tree, keywords)
        
        tree_logger.info(f"客户端过滤完成 | 匹配节点数: {len(filtered_nodes)}")
        return filtered_nodes
    
    def _filter_nodes_by_keywords(self, tree_structure: List[dict], keywords: List[str]) -> List[dict]:
        """客户端过滤：根据关键词过滤节点"""
        filtered_nodes = []
        
        def node_matches_keywords(node: DatasetNode, keywords: List[str]) -> bool:
            """检查节点是否匹配任一关键词"""
            node_text = f"{node.name} {node.intro or ''}".lower()
            
            # 只要匹配任一关键词就算匹配
            for keyword in keywords:
                if keyword.lower() in node_text:
                    return True
            return False
        
        def filter_recursive(nodes: List[dict]) -> List[dict]:
            """递归过滤节点"""
            result = []
            
            for node_data in nodes:
                node = node_data['node']
                children = node_data['children']
                
                # 检查当前节点是否匹配
                node_matches = node_matches_keywords(node, keywords)
                
                # 递归过滤子节点
                filtered_children = filter_recursive(children) if children else []
                
                # 如果当前节点匹配，或者有匹配的子节点，则保留
                if node_matches or filtered_children:
                    result.append({
                        'node': node,
                        'depth': node_data['depth'],
                        'children': filtered_children
                    })
                    
                    # 记录匹配原因
                    if node_matches:
                        tree_logger.debug(f"节点匹配: {node.name}")
                    elif filtered_children:
                        tree_logger.debug(f"子节点匹配，保留父节点: {node.name}")
            
            return result
        
        filtered_nodes = filter_recursive(tree_structure)
        
        # 统计匹配信息
        total_matched = self._count_total_nodes(filtered_nodes)
        direct_matches = len(filtered_nodes)
        
        tree_logger.info(f"过滤结果 | 直接匹配: {direct_matches} 个 | 总计(含子节点): {total_matched} 个")
        
        # 记录每个关键词的匹配情况
        for keyword in keywords:
            keyword_matches = self._count_keyword_matches(filtered_nodes, keyword)
            tree_logger.debug(f"关键词 '{keyword}' 匹配了 {keyword_matches} 个节点")
        
        return filtered_nodes
    
    def _count_keyword_matches(self, tree_structure: List[dict], keyword: str) -> int:
        """统计特定关键词的匹配数量"""
        count = 0
        
        def count_recursive(nodes: List[dict]):
            nonlocal count
            for node_data in nodes:
                node = node_data['node']
                node_text = f"{node.name} {node.intro or ''}".lower()
                if keyword.lower() in node_text:
                    count += 1
                
                if node_data['children']:
                    count_recursive(node_data['children'])
        
        count_recursive(tree_structure)
        return count
    
    async def _build_tree_recursively(self, parent_id: str, search_value: str, max_depth: int, current_depth: int) -> List[dict]:
        """递归构建目录树结构"""
        if current_depth >= max_depth:
            return []
        
        try:
            # 获取当前层级的节点（不使用服务器端搜索，因为它不起作用）
            nodes = await self.api_client.get_dataset_tree(parent_id, "", 1)
            
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
        direct_matches = len(tree_structure)
        
        # 解析关键词用于展示
        keywords = self._parse_search_keywords(search_value)
        search_display = f"{keywords}" if keywords else "无"
        
        markdown_lines = [
            "# 📁 知识库目录树",
            "",
            f"**搜索条件:** {search_display}",
            f"**最大深度:** {max_depth}",
            f"**直接匹配节点数:** {direct_matches}",
            f"**总节点数(含子节点):** {total_nodes}",
            ""
        ]
        
        if keywords:
            markdown_lines.extend([
                "**搜索说明:** 支持多关键词搜索（空格分隔），使用客户端智能过滤",
                "**过滤逻辑:** 匹配节点名称和描述中的任意关键词，保留匹配节点及其父子节点",
                ""
            ])
        
        # 递归添加节点
        self._add_nodes_to_markdown(tree_structure, markdown_lines, 0, keywords)
        
        return '\n'.join(markdown_lines)
    
    def _add_nodes_to_markdown(self, tree_structure: List[dict], markdown_lines: List[str], depth: int, keywords: List[str] = None):
        """递归添加节点到Markdown，高亮匹配的关键词"""
        for node_data in tree_structure:
            node = node_data['node']
            children = node_data['children']
            
            # 计算缩进
            indent = "  " * depth
            
            # 确定图标
            icon = "📚" if node.type == "dataset" else "📁"
            
            # 高亮显示匹配的关键词
            name_display = node.name
            intro_display = node.intro or ""
            
            if keywords:
                # 检查是否匹配关键词
                node_text = f"{node.name} {node.intro or ''}".lower()
                matched_keywords = [kw for kw in keywords if kw.lower() in node_text]
                
                if matched_keywords:
                    # 添加匹配标识
                    match_indicator = f"🎯 **[匹配: {', '.join(matched_keywords)}]**"
                    name_display = f"{node.name} {match_indicator}"
            
            # 添加节点信息
            markdown_lines.append(f"{indent}- {icon} **{name_display}**")
            markdown_lines.append(f"{indent}  - ID: `{node.id}`")
            markdown_lines.append(f"{indent}  - 类型: {node.type}")
            
            # 显示描述（如果有）
            if intro_display.strip():
                markdown_lines.append(f"{indent}  - 描述: {intro_display}")
            
            markdown_lines.append("")
            
            # 递归添加子节点
            if children:
                self._add_nodes_to_markdown(children, markdown_lines, depth + 1, keywords)
    
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