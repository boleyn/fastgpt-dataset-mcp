"""
格式化工具类

提供统一的来源信息格式化功能，确保所有搜索和查看结果都包含标准化的来源信息。
"""

from typing import Optional, Dict, Any
from urllib.parse import quote
from ..models import SearchResult, CollectionInfo


class FormatUtils:
    """统一格式化工具类"""
    
    @staticmethod
    def format_source_info_block(collection_id: str, source_name: str, 
                               download_link: Optional[str] = None,
                               collection_detail: Optional[CollectionInfo] = None,
                               dataset_id: Optional[str] = None,
                               additional_info: Optional[Dict[str, Any]] = None) -> str:
        """
        生成标准化的来源信息块
        
        Args:
            collection_id: Collection ID
            source_name: 来源文档名称
            download_link: 文件下载链接（可选）
            collection_detail: Collection详细信息（可选）
            dataset_id: 数据集ID（可选）
            additional_info: 额外信息字典（可选）
            
        Returns:
            标准化的Markdown格式来源信息块
        """
        info_lines = []
        info_lines.append("### 📄 来源信息")
        info_lines.append("")
        
        # Collection ID（必需）
        info_lines.append(f"**Collection ID:** `{collection_id}`")
        info_lines.append("")
        
        # 来源文档名称
        if collection_detail and collection_detail.name:
            # 使用详细信息中的准确名称
            display_name = collection_detail.name
            info_lines.append(f"**来源文档:** {display_name}")
        else:
            # 使用传入的名称
            info_lines.append(f"**来源文档:** {source_name}")
        info_lines.append("")
        
        # 文档类型
        if collection_detail and collection_detail.type:
            info_lines.append(f"**文档类型:** {collection_detail.type}")
            info_lines.append("")
        
        # 文档大小
        if collection_detail and collection_detail.raw_text_length:
            info_lines.append(f"**文档大小:** {collection_detail.raw_text_length:,} 字符")
            info_lines.append("")
        
        # 文件下载链接
        if download_link:
            display_name = collection_detail.name if collection_detail and collection_detail.name else source_name
            encoded_link = quote(download_link, safe=':/?#[]@!$&\'()*+,;=')
            info_lines.append(f"**文件链接:** [{display_name}]({encoded_link})")
            info_lines.append("")
        
        # 数据集ID
        if dataset_id:
            info_lines.append(f"**数据集ID:** `{dataset_id}`")
            info_lines.append("")
        
        # 额外信息
        if additional_info:
            for key, value in additional_info.items():
                info_lines.append(f"**{key}:** {value}")
                info_lines.append("")
        
        return "\n".join(info_lines)
    
    @staticmethod
    def format_search_result_item(result: SearchResult, index: int, 
                                download_link: Optional[str] = None,
                                collection_detail: Optional[CollectionInfo] = None) -> str:
        """
        格式化单个搜索结果项
        
        Args:
            result: 搜索结果
            index: 结果序号
            download_link: 文件下载链接（可选）
            collection_detail: Collection详细信息（可选）
            
        Returns:
            格式化的Markdown搜索结果项
        """
        lines = []
        lines.append(f"## 结果 {index}")
        lines.append("")
        
        # 内容
        lines.append(f"**内容:**")
        lines.append(result.q)
        lines.append("")
        
        # 答案（如果有）
        if result.a:
            lines.append(f"**答案:**")
            lines.append(result.a)
            lines.append("")
        
        # 评分信息
        lines.append("**相关性评分:**")
        for score in result.score:
            score_type = score.get("type", "unknown")
            score_value = score.get("value", 0)
            lines.append(f"- {score_type}: {score_value:.4f}")
        lines.append("")
        
        # Token信息
        lines.append(f"**Token数量:** {result.tokens}")
        lines.append("")
        
        # 统一的来源信息
        source_info = FormatUtils.format_source_info_block(
            collection_id=result.collection_id,
            source_name=result.source_name,
            download_link=download_link,
            collection_detail=collection_detail
        )
        lines.append(source_info)
        
        lines.append("---")
        lines.append("")
        
        return "\n".join(lines)
    
    @staticmethod
    def format_document_header(title: str, collection_id: str, source_name: str,
                             download_link: Optional[str] = None,
                             collection_detail: Optional[CollectionInfo] = None,
                             chunk_count: Optional[int] = None,
                             dataset_id: Optional[str] = None) -> str:
        """
        格式化文档头部信息
        
        Args:
            title: 文档标题
            collection_id: Collection ID
            source_name: 来源文档名称
            download_link: 文件下载链接（可选）
            collection_detail: Collection详细信息（可选）
            chunk_count: 数据块数量（可选）
            dataset_id: 数据集ID（可选）
            
        Returns:
            格式化的Markdown文档头部
        """
        lines = []
        lines.append(f"# {title}")
        lines.append("")
        
        # 统一的来源信息
        additional_info = {}
        if chunk_count is not None:
            additional_info["总数据块数量"] = chunk_count
        
        source_info = FormatUtils.format_source_info_block(
            collection_id=collection_id,
            source_name=source_name,
            download_link=download_link,
            collection_detail=collection_detail,
            dataset_id=dataset_id,
            additional_info=additional_info
        )
        lines.append(source_info)
        
        lines.append("---")
        lines.append("")
        
        return "\n".join(lines)
    
    @staticmethod
    def format_multi_search_summary(total_datasets: int, total_results: int, query: str) -> str:
        """
        格式化多数据集搜索摘要
        
        Args:
            total_datasets: 搜索的数据集数量
            total_results: 总结果数量
            query: 搜索查询
            
        Returns:
            格式化的搜索摘要
        """
        lines = []
        lines.append("# 🔍 多数据集搜索结果")
        lines.append("")
        lines.append("## 📝 搜索查询")
        lines.append(f"> {query}")
        lines.append("")
        lines.append("## 📊 搜索统计")
        lines.append(f"- **搜索数据集数量**: {total_datasets}")
        lines.append(f"- **总结果数量**: {total_results}")
        lines.append("")
        lines.append("## 🎯 各数据集结果")
        lines.append("")
        
        return "\n".join(lines) 