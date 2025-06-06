"""
Collection管理服务
"""

from typing import List
from urllib.parse import quote
from ..api_client import api_client
from ..models import DataChunk, CollectionInfo
from ..logger import collection_logger


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
            
            # 生成统一的内容文本
            main_content = self._format_chunks_content(chunks)
            
            # 构建来源信息
            source_info = self._format_source_info(collection_id, collection_detail, download_link, chunks)
            
            # 返回完整内容：主要内容 + 来源信息
            result = main_content + source_info
            
            collection_logger.info(f"Collection内容查看完成 | 总数据块: {len(chunks)}")
            return result
            
        except Exception as e:
            collection_logger.error(f"查看collection内容失败: {str(e)}", exc_info=True)
            return f"# 错误\n\n查看collection内容时发生错误: {str(e)}"
    
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
    
    def _format_source_info(self, collection_id: str, collection_detail: CollectionInfo, 
                           download_link: str, chunks: List[DataChunk]) -> str:
        """格式化来源信息"""
        source_info = "\n\n## 📄 来源信息\n\n"
        source_info += f"**Collection ID:** `{collection_id}`\n\n"
        
        if collection_detail:
            # 使用新的detail接口获取的准确文件名
            source_name = collection_detail.name
            source_info += f"**来源文档:** {source_name}\n\n"
            source_info += f"**文档类型:** {collection_detail.type}\n\n"
            
            # 添加文件大小信息
            if collection_detail.raw_text_length:
                source_info += f"**文档大小:** {collection_detail.raw_text_length:,} 字符\n\n"
            
            # 添加文件下载链接
            if download_link:
                encoded_link = quote(download_link, safe=':/?#[]@!$&\'()*+,;=')
                source_info += f"**文件链接:** [{source_name}]({encoded_link})\n\n"
        
        source_info += f"**总数据块数量:** {len(chunks)}\n\n"
        source_info += f"**数据集ID:** `{chunks[0].dataset_id if chunks else 'N/A'}`\n\n"
        
        return source_info 