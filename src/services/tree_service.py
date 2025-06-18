"""
目录树服务
"""

from typing import List, Dict, Any, Set
import asyncio
from ..api_client import api_client
from ..models import DatasetNode
from ..logger import tree_logger
from .permission_service import permission_service


class TreeService:
    """目录树管理服务"""
    
    def __init__(self):
        self.api_client = api_client
    
    async def get_knowledge_base_tree(self, parent_id: str, search_value: str = "", deep: int = 4, userid: str = None) -> str:
        """
        获取知识库目录树并格式化为Markdown
        
        Args:
            parent_id: 父级目录ID
            search_value: 搜索关键词（支持空格分隔的多个关键词）
            deep: 目录深度
            userid: 用户ID（用于权限控制）
            
        Returns:
            格式化的Markdown文本
        """
        try:
            # 处理多关键词搜索
            keywords = self._parse_search_keywords(search_value)
            tree_logger.info(f"开始获取知识库目录树 | 父级ID: {parent_id[:8]}... | 搜索词: {keywords} | 深度: {deep}")
            
            if keywords:
                # 使用并发API调用搜索多关键词
                tree_structure = await self._build_tree_with_concurrent_search(parent_id, keywords, deep)
            else:
                # 无搜索词，获取完整目录树
                tree_structure = await self._build_tree_recursively(parent_id, "", deep, 0)
            
            # 应用权限过滤
            if userid and tree_structure:
                tree_structure = self._apply_permission_filter(tree_structure, userid)
            
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
    
    async def _build_tree_with_concurrent_search(self, parent_id: str, keywords: List[str], max_depth: int) -> List[dict]:
        """使用并发API调用实现多关键词搜索"""
        tree_logger.info(f"开始并发多关键词搜索 | 关键词数: {len(keywords)}")
        
        # 并发调用后端API，每个关键词单独请求
        async def search_single_keyword(keyword: str) -> List[dict]:
            try:
                tree_logger.info(f"搜索关键词: '{keyword}'")
                # 调用后端API搜索单个关键词
                nodes = await self.api_client.get_dataset_tree(parent_id, keyword, max_depth)
                
                # 转换为树结构格式
                tree_structure = []
                for node in nodes:
                    node_data = {
                        'node': node,
                        'depth': 0,  # API返回的是扁平结构，深度设为0
                        'children': []
                    }
                    tree_structure.append(node_data)
                
                tree_logger.info(f"关键词 '{keyword}' 搜索到 {len(nodes)} 个节点")
                return tree_structure
                
            except Exception as e:
                tree_logger.error(f"搜索关键词 '{keyword}' 失败: {e}")
                return []
        
        # 并发执行所有关键词搜索
        import asyncio
        tasks = [search_single_keyword(keyword) for keyword in keywords]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 合并所有结果，去重
        merged_nodes = {}  # 使用字典去重，key为node.id
        total_found = 0
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                tree_logger.error(f"关键词 '{keywords[i]}' 搜索异常: {result}")
                continue
            
            if isinstance(result, list):
                for node_data in result:
                    node_id = node_data['node'].id
                    if node_id not in merged_nodes:
                        merged_nodes[node_id] = node_data
                        total_found += 1
        
        # 转换为列表
        final_results = list(merged_nodes.values())
        
        tree_logger.info(f"并发搜索完成 | 总找到: {total_found} 个唯一节点 | 去重后: {len(final_results)} 个")
        
        return final_results
    
    def _filter_nodes_by_keywords(self, tree_structure: List[dict], keywords: List[str]) -> List[dict]:
        """客户端过滤：根据关键词过滤节点"""
        filtered_nodes = []
        
        def node_matches_keywords(node: DatasetNode, keywords: List[str]) -> bool:
            """检查节点是否匹配任一关键词"""
            node_text = f"{node.name} {node.intro or ''}".lower()
            
            # 只要匹配任一关键词就算匹配
            for keyword in keywords:
                if keyword.lower() in node_text:
                    tree_logger.debug(f"节点匹配成功: '{node.name}' 匹配关键词 '{keyword}'")
                    return True
            
            # 调试：记录未匹配的节点（仅记录前几个，避免日志过多）
            if len(keywords) <= 10:  # 只在关键词不太多时记录
                tree_logger.debug(f"节点未匹配: '{node.name}' (文本: '{node_text[:50]}...') 未匹配关键词: {keywords[:3]}...")
            
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
        
        # 记录每个关键词在原始树结构中的匹配情况（用于调试）
        if direct_matches == 0:
            tree_logger.info("🔍 调试信息：在原始树结构中检查关键词匹配情况:")
            for keyword in keywords:
                original_matches = self._count_keyword_matches(tree_structure, keyword)
                tree_logger.info(f"  关键词 '{keyword}' 在原始树中匹配了 {original_matches} 个节点")
            
            # 显示前3个节点样本
            if len(tree_structure) > 0:
                tree_logger.info("🔍 前3个节点样本:")
                sample_count = min(3, len(tree_structure))
                for i in range(sample_count):
                    node = tree_structure[i]['node']
                    node_text = f"{node.name} {node.intro or ''}".lower()
                    tree_logger.info(f"  样本{i+1}: '{node.name}' (类型: {node.type}) (文本: '{node_text[:100]}...')")
        
        # 记录过滤后的匹配情况
        for keyword in keywords:
            keyword_matches = self._count_keyword_matches(filtered_nodes, keyword)
            tree_logger.info(f"关键词 '{keyword}' 在过滤结果中匹配了 {keyword_matches} 个节点")
        
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
    
    async def explore_folder_contents(self, folder_id: str, search_value: str = "", deep: int = 6, userid: str = None) -> str:
        """
        深入探索指定文件夹的内容
        
        专门用于探索文件夹内部的所有知识库和子文件夹，支持更深层次的搜索。
        当get_dataset_tree返回文件夹时，使用此工具进一步探索文件夹内容。
        
        Args:
            folder_id: 文件夹ID（从get_dataset_tree结果中获取）
            search_value: 搜索关键词（可选）
            deep: 探索深度（1-10，默认6，比普通目录树更深）
            userid: 用户ID（用于权限控制）
            
        Returns:
            格式化的文件夹内容报告
        """
        try:
            # 参数验证
            if not folder_id or not folder_id.strip():
                return "❌ 请提供有效的文件夹ID"
            
            if deep < 1 or deep > 10:
                deep = 6
                tree_logger.warning(f"深度参数超出范围，已调整为默认值: {deep}")
            
            tree_logger.info(f"开始探索文件夹内容 | 文件夹ID: {folder_id[:8]}... | 搜索词: '{search_value}' | 深度: {deep}")
            
            # 首先验证文件夹是否存在
            try:
                # 尝试获取文件夹信息（深度1）
                folder_info = await self.api_client.get_dataset_tree(folder_id, "", 1)
                if not folder_info:
                    return f"❌ 文件夹不存在或无权限访问\n\n**文件夹ID:** `{folder_id}`"
            except Exception as e:
                tree_logger.error(f"验证文件夹失败: {e}")
                return f"❌ 无法访问指定文件夹: {str(e)}\n\n**文件夹ID:** `{folder_id}`"
            
            # 处理搜索关键词
            keywords = self._parse_search_keywords(search_value)
            
            # 构建文件夹内容树
            folder_contents = []
            search_fallback_used = False
            
            if keywords:
                # 有搜索词，使用并发API搜索
                folder_contents = await self._build_tree_with_concurrent_search(folder_id, keywords, deep)
                
                # 智能回退：如果搜索结果为空，可能是文件夹名匹配但内容不匹配
                # 这时自动移除搜索关键词，获取完整内容
                if not folder_contents:
                    tree_logger.info(f"搜索关键词 '{search_value}' 无匹配结果，启用智能回退获取完整内容")
                    folder_contents = await self._build_tree_recursively(folder_id, "", deep, 0)
                    search_fallback_used = True
            else:
                # 无搜索词，获取完整内容
                folder_contents = await self._build_tree_recursively(folder_id, "", deep, 0)
            
            # 应用权限过滤
            if userid and folder_contents:
                folder_contents = self._apply_permission_filter(folder_contents, userid)
            
            if not folder_contents:
                search_info = f"搜索条件: '{search_value}'" if search_value else "无搜索条件"
                return f"""# 📁 文件夹内容探索

**文件夹ID:** `{folder_id}`
**{search_info}**
**探索深度:** {deep}

*此文件夹为空或没有匹配的内容*

💡 **建议:**
- 尝试减少搜索关键词或使用更通用的词汇
- 增加探索深度参数
- 检查文件夹权限设置
"""
            
            # 格式化为详细报告
            report = self._format_folder_exploration_report(folder_id, folder_contents, search_value, deep, search_fallback_used)
            
            total_nodes = self._count_total_nodes(folder_contents)
            fallback_info = " (智能回退)" if search_fallback_used else ""
            tree_logger.info(f"文件夹探索完成{fallback_info} | 文件夹ID: {folder_id[:8]}... | 找到节点: {len(folder_contents)} | 总计: {total_nodes}")
            
            return report
            
        except Exception as e:
            tree_logger.error(f"探索文件夹内容失败: {str(e)}", exc_info=True)
            return f"# ❌ 探索失败\n\n**文件夹ID:** `{folder_id}`\n**错误信息:** {str(e)}\n\n请检查文件夹ID是否正确，或联系管理员。"
    
    def _format_folder_exploration_report(self, folder_id: str, folder_contents: List[dict], search_value: str, deep: int, search_fallback_used: bool = False) -> str:
        """
        格式化文件夹探索报告
        
        Args:
            folder_id: 文件夹ID
            folder_contents: 文件夹内容树结构
            search_value: 搜索条件
            deep: 探索深度
            search_fallback_used: 是否使用了智能回退
            
        Returns:
            格式化的探索报告
        """
        total_nodes = self._count_total_nodes(folder_contents)
        direct_items = len(folder_contents)
        
        # 统计不同类型的节点
        datasets_count = 0
        folders_count = 0
        
        def count_by_type(nodes: List[dict]):
            nonlocal datasets_count, folders_count
            for node_data in nodes:
                if node_data['node'].type == "dataset":
                    datasets_count += 1
                elif node_data['node'].type == "folder":
                    folders_count += 1
                
                if node_data['children']:
                    count_by_type(node_data['children'])
        
        count_by_type(folder_contents)
        
        # 解析关键词
        keywords = self._parse_search_keywords(search_value)
        search_display = f"'{search_value}'" if search_value else "无"
        
        # 生成报告头部
        report_lines = [
            "# 📁 文件夹内容深度探索",
            "",
            f"**目标文件夹ID:** `{folder_id}`",
            f"**搜索条件:** {search_display}",
            f"**探索深度:** {deep} 层",
        ]
        
        # 如果使用了智能回退，添加说明
        if search_fallback_used:
            report_lines.extend([
                "",
                "🔄 **智能回退说明:**",
                f"- 原搜索条件 '{search_value}' 在此文件夹内无匹配结果",
                "- 已自动移除搜索限制，显示文件夹完整内容",
                "- 这通常发生在文件夹名匹配但内容不匹配的情况",
            ])
        
        report_lines.extend([
            "",
            "## 📊 探索统计",
            f"- **直接子项:** {direct_items} 个",
            f"- **总计项目:** {total_nodes} 个",
            f"- **知识库数量:** {datasets_count} 个 📚",
            f"- **文件夹数量:** {folders_count} 个 📁",
            ""
        ])
        
        if keywords and not search_fallback_used:
            report_lines.extend([
                "## 🔍 搜索说明",
                f"- **关键词:** {', '.join(keywords)}",
                "- **匹配逻辑:** 节点名称或描述包含任一关键词",
                "- **结果包含:** 匹配节点及其完整父子关系",
                ""
            ])
        
        # 添加内容详情
        if folder_contents:
            report_lines.extend([
                "## 📋 详细内容",
                ""
            ])
            
            # 递归添加节点信息
            self._add_nodes_to_markdown(folder_contents, report_lines, 0, keywords)
        
        # 添加使用建议
        report_lines.extend([
            "",
            "## 💡 使用建议",
            ""
        ])
        
        if datasets_count > 0:
            report_lines.extend([
                f"### 📚 发现 {datasets_count} 个知识库",
                "- 使用 `search_dataset(dataset_id, text)` 在特定知识库中搜索",
                "- 使用 `multi_dataset_search([dataset_ids], query)` 跨多个知识库搜索",
                ""
            ])
        
        if folders_count > 0:
            report_lines.extend([
                f"### 📁 发现 {folders_count} 个子文件夹", 
                "- 使用 `explore_folder_contents(folder_id)` 进一步探索子文件夹",
                "- 可以增加深度参数获取更深层次的内容",
                ""
            ])
        
        report_lines.extend([
            "### 🔍 搜索优化",
            "- 如果结果太多，添加更具体的搜索关键词",
            "- 如果结果太少，尝试更通用的关键词或减少关键词数量",
            "- 使用 `expand_search_keywords(query)` 获取关键词扩展建议",
            ""
        ])
        
        return '\n'.join(report_lines)
    
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
    
    def _apply_permission_filter(self, tree_structure: List[dict], userid: str) -> List[dict]:
        """
        应用权限过滤，移除用户无权限访问的受限数据集
        
        Args:
            tree_structure: 树结构数据
            userid: 用户ID
            
        Returns:
            过滤后的树结构
        """
        if not tree_structure or not userid:
            return tree_structure
        
        filtered_structure = []
        
        for node_data in tree_structure:
            node = node_data['node']
            children = node_data['children']
            
            # 检查当前节点权限
            if node.type == 'dataset' and node.id in permission_service.config.restricted_datasets:
                # 是受限数据集，检查用户权限
                if not permission_service.is_special_user(userid):
                    tree_logger.info(f"权限过滤: 用户 {userid} 无权限访问受限数据集 {node.id[:8]}...")
                    continue  # 跳过这个受限数据集
            
            # 递归过滤子节点
            filtered_children = []
            if children:
                filtered_children = self._apply_permission_filter(children, userid)
            
            # 添加过滤后的节点
            filtered_structure.append({
                'node': node,
                'depth': node_data['depth'],
                'children': filtered_children
            })
        
        return filtered_structure 