"""
Collection管理服务
"""

from typing import List
from urllib.parse import quote
from ..api_client import api_client
from ..models import DataChunk, CollectionInfo
from ..logger import collection_logger
from .format_utils import FormatUtils


class CollectionService:
    """Collection管理服务"""
    
    def __init__(self):
        self.api_client = api_client
    
    async def view_collection_content(self, collection_id: str, page_size: int = 50) -> str:
        """
        查看collection的所有内容并格式化为Markdown
        
        Args:
            collection_id: Collection ID
            page_size: 每页数据块数量
            
        Returns:
            格式化的Markdown文本
        """
        try:
            collection_logger.info(f"开始查看Collection内容 | ID: {collection_id[:8]}... | 页面大小: {page_size}")
            
            # 获取collection详细信息（使用新的detail接口）
            collection_detail = await self.api_client.get_collection_detail(collection_id)
            
            # 获取所有数据块
            chunks = await self._get_all_chunks(collection_id, page_size)
            
            # 获取文件下载链接
            download_link = await self.api_client.get_file_download_link(collection_id)
            
            if not chunks:
                markdown_content = f"# Collection内容查看\n\n**Collection ID:** `{collection_id}`\n\n"
                if collection_detail:
                    markdown_content += f"**名称:** {collection_detail.name}\n\n"
                markdown_content += "*此collection中没有数据块*\n\n"
                return markdown_content
            
            # 使用统一格式化工具生成文档头部（包含来源信息）
            header = FormatUtils.format_document_header(
                title="📄 Collection 完整内容",
                collection_id=collection_id,
                source_name=collection_detail.name if collection_detail else "Unknown",
                download_link=download_link,
                collection_detail=collection_detail,
                chunk_count=len(chunks),
                dataset_id=chunks[0].dataset_id if chunks else None
            )
            
            # 生成内容部分
            content_section = "## 📝 文档内容\n\n" + self._format_chunks_content(chunks)
            
            # 返回完整内容：头部 + 内容
            result = header + content_section
            
            collection_logger.info(f"Collection内容查看完成 | 总数据块: {len(chunks)}")
            return result
            
        except Exception as e:
            error_msg = str(e)
            collection_logger.error(f"查看collection内容失败: {error_msg}", exc_info=True)
            
            # 为不同类型的错误提供更友好的信息
            if "Collection不存在" in error_msg:
                return f"""# ❌ Collection不存在

**Collection ID:** `{collection_id}`

**错误信息:** Collection不存在，请检查Collection ID是否正确。

**建议解决方案:**
1. 确认Collection ID是否正确
2. 使用其他工具查看可用的Collection列表
3. 联系管理员确认Collection状态
"""
            elif "HTTP请求失败: 500" in error_msg:
                return f"""# ❌ 服务器内部错误

**Collection ID:** `{collection_id}`

**错误信息:** API服务器返回500内部错误

**建议解决方案:**
1. 稍后重试
2. 检查API服务器状态
3. 联系管理员检查服务器日志
"""
            else:
                return f"""# ❌ 查看Collection内容失败

**Collection ID:** `{collection_id}`

**错误信息:** {error_msg}

**建议解决方案:**
1. 检查网络连接
2. 确认API配置是否正确
3. 稍后重试
"""
    
    async def _get_all_chunks(self, collection_id: str, page_size: int) -> List[DataChunk]:
        """获取collection的所有数据块"""
        all_chunks = []
        offset = 0
        
        collection_logger.info(f"开始获取collection {collection_id} 的所有数据块")
        
        while True:
            # 获取当前页的数据
            chunks, has_more = await self.api_client.get_collection_chunks_page(collection_id, offset, page_size)
            
            if not chunks:
                break
            
            all_chunks.extend(chunks)
            collection_logger.debug(f"已获取 {len(all_chunks)} 个数据块 (当前页: {len(chunks)} 个)")
            
            if not has_more:
                break
                
            offset += page_size
        
        collection_logger.info(f"获取完成，总共 {len(all_chunks)} 个数据块")
        return all_chunks
    
    def _format_chunks_content(self, chunks: List[DataChunk]) -> str:
        """格式化数据块内容"""
        content_lines = []
        
        for i, chunk in enumerate(chunks, 1):
            content_lines.append(f"### 数据块 {i} (索引: {chunk.chunk_index})")
            content_lines.append("")
            
            # 内容
            if chunk.q.strip():
                # 将内容按行分割并添加
                chunk_content_lines = chunk.q.strip().split('\n')
                for line in chunk_content_lines:
                    content_lines.append(line)
                content_lines.append("")
            
            # 答案（如果有）
            if chunk.a.strip():
                content_lines.append("**答案:**")
                content_lines.append("")
                answer_lines = chunk.a.strip().split('\n')
                for line in answer_lines:
                    content_lines.append(line)
                content_lines.append("")
            
            content_lines.append("---")
            content_lines.append("")
        
        return '\n'.join(content_lines)
    
 