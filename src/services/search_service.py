"""
搜索服务
"""

from typing import List
from urllib.parse import quote
from ..api_client import api_client
from ..models import SearchResult
from ..logger import search_logger
from .format_utils import FormatUtils
from .permission_service import permission_service


class SearchService:
    """搜索管理服务"""
    
    def __init__(self):
        self.api_client = api_client
    
    async def search_knowledge_base_raw(self, dataset_id: str, query: str, limit: int = 10) -> List[SearchResult]:
        """
        搜索知识库并返回原始结果（用于其他服务调用）
        
        Args:
            dataset_id: 数据集ID
            query: 搜索查询
            limit: 结果限制
            
        Returns:
            搜索结果列表
        """
        try:
            search_logger.debug(f"原始搜索 | 数据集: {dataset_id[:8]}... | 查询: '{query}' | 限制: {limit}")
            
            results = await self.api_client.search_dataset(dataset_id, query, limit)
            
            search_logger.debug(f"原始搜索完成 | 找到 {len(results)} 个结果")
            return results
            
        except Exception as e:
            search_logger.error(f"原始搜索失败: {str(e)}", exc_info=True)
            return []
    
    async def search_knowledge_base(self, dataset_id: str, text: str, limit: int = 10, userid: str = None) -> str:
        """
        搜索知识库并格式化为Markdown
        
        Args:
            dataset_id: 数据集ID
            text: 搜索关键词
            limit: 结果数量限制
            userid: 用户ID（用于权限控制）
            
        Returns:
            格式化的Markdown文本
        """
        try:
            search_logger.info(f"开始搜索知识库 | 数据集: {dataset_id[:8]}... | 关键词: '{text}' | 限制: {limit}")
            
            # 检查权限
            if userid and not permission_service.has_dataset_access(userid, dataset_id):
                search_logger.warning(f"用户 {userid} 无权限访问受限数据集: {dataset_id}")
                return f"# ❌ 权限不足\n\n**数据集:** {dataset_id}\n\n您没有访问此数据集的权限。请联系管理员。"
            
            # 处理多关键词搜索
            search_results = await self._search_with_keywords(dataset_id, text, limit)
            
            if not search_results:
                return f"# 搜索结果\n\n**搜索关键词:** {text}\n\n**结果:** 未找到相关内容\n"
            
            # 格式化为Markdown
            markdown_content = await self._format_search_results_markdown(search_results, text)
            
            search_logger.info(f"搜索完成 | 找到 {len(search_results)} 个结果")
            return markdown_content
            
        except Exception as e:
            search_logger.error(f"搜索知识库失败: {str(e)}", exc_info=True)
            return f"# 搜索出错\n\n**错误信息:** {str(e)}\n"
    
    async def _search_with_keywords(self, dataset_id: str, text: str, limit: int) -> List[SearchResult]:
        """处理多关键词搜索"""
        # 处理空格分隔的搜索词
        if text and " " in text.strip():
            # 如果搜索词包含空格，分别搜索每个词然后合并结果
            keywords = [kw.strip() for kw in text.split() if kw.strip()]
            search_logger.debug(f"检测到多个搜索词: {keywords}")
            search_logger.debug("将分别搜索每个词并合并结果（MongoDB不支持空格OR搜索）")
            
            all_results = []
            seen_ids = set()
            
            for keyword in keywords:
                search_logger.debug(f"搜索关键词: '{keyword}' 在数据集 {dataset_id}")
                results = await self.api_client.search_dataset(dataset_id, keyword, limit)
                
                # 去重合并结果
                for item in results:
                    # 使用内容和来源的组合作为唯一标识
                    unique_id = f"{item.id}_{item.collection_id}"
                    if unique_id not in seen_ids:
                        all_results.append(item)
                        seen_ids.add(unique_id)
            
            search_logger.info(f"合并结果完成 | 找到 {len(all_results)} 个唯一结果")
            
            # 按评分排序并限制结果数量
            all_results.sort(key=lambda x: sum(s.get("value", 0) for s in x.score), reverse=True)
            return all_results[:limit]
        else:
            # 单个词搜索
            return await self.api_client.search_dataset(dataset_id, text, limit)
    
    async def _format_search_results_markdown(self, search_results: List[SearchResult], text: str) -> str:
        """格式化搜索结果为Markdown"""
        # 头部信息
        markdown_content = f"# 🔍 搜索结果\n\n**搜索关键词:** {text}\n\n**找到 {len(search_results)} 条结果**\n\n"
        
        for i, result in enumerate(search_results, 1):
            # 获取文件下载链接
            download_link = await self.api_client.get_file_download_link(result.collection_id)
            
            # 获取collection详细信息（用于准确的文件名）
            try:
                collection_detail = await self.api_client.get_collection_detail(result.collection_id)
            except:
                collection_detail = None
            
            # 使用统一的格式化工具
            result_item = FormatUtils.format_search_result_item(
                result=result,
                index=i,
                download_link=download_link,
                collection_detail=collection_detail
            )
            
            markdown_content += result_item
        
        return markdown_content 