"""
数据模型定义
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class DatasetNode(BaseModel):
    """数据集节点模型"""
    id: str = Field(alias="_id")
    name: str
    type: str  # dataset, folder
    intro: Optional[str] = None
    avatar: Optional[str] = None
    permission: Optional[Dict[str, Any]] = None  # permission是一个复杂对象
    can_write: bool = Field(default=False, alias="canWrite")


class SearchResult(BaseModel):
    """搜索结果数据模型"""
    id: str
    q: str  # 搜索到的内容
    a: str  # 答案（可能为空）
    source_name: str = Field(alias="sourceName")
    collection_id: str = Field(alias="collectionId")
    score: List[Dict[str, Any]]
    tokens: int
    chunk_index: int = Field(alias="chunkIndex")


class DataChunk(BaseModel):
    """数据块模型"""
    id: str = Field(alias="_id")
    dataset_id: str = Field(alias="datasetId")
    collection_id: str = Field(alias="collectionId")
    q: str  # 问题/内容
    a: str  # 答案
    chunk_index: int = Field(alias="chunkIndex")


class CollectionInfo(BaseModel):
    """Collection详细信息模型"""
    id: str = Field(alias="_id")
    parent_id: Optional[str] = Field(default=None, alias="parentId")
    team_id: str = Field(alias="teamId")
    tmb_id: str = Field(alias="tmbId")
    dataset_id: str = Field(alias="datasetId")
    type: str
    name: str
    file_id: Optional[str] = Field(default=None, alias="fileId")
    raw_text_length: Optional[int] = Field(default=None, alias="rawTextLength")
    hash_raw_text: Optional[str] = Field(default=None, alias="hashRawText")
    metadata: Optional[Dict[str, Any]] = None


class CollectionFileInfo(BaseModel):
    """Collection文件信息模型（用于下载链接）"""
    id: Optional[str] = Field(default=None, alias="_id")
    type: str
    name: Optional[str] = None
    value: str  # 文件路径或URL


# MCP工具请求模型
class KnowledgeBaseTreeRequest(BaseModel):
    """知识库目录树请求参数"""
    search_value: str = Field(
        default="", 
        description="MongoDB查询条件，用于过滤知识库内容。应使用单个关键词（如'亚信'），不能使用多个空格分隔的词。留空则获取所有内容。"
    )
    deep: int = Field(
        default=4, 
        description="目录树的最大深度层级，默认为4",
        ge=1, 
        le=10
    )


class KnowledgeBaseSearchRequest(BaseModel):
    """知识库搜索请求参数"""
    dataset_id: str = Field(
        description="知识库数据集ID，必需参数"
    )
    text: str = Field(
        description="搜索关键词，要查找的内容"
    )
    limit: int = Field(
        default=10,
        description="返回结果数量限制，默认为10",
        ge=1,
        le=50
    )


class CollectionViewRequest(BaseModel):
    """Collection查看请求参数"""
    collection_id: str = Field(
        description="Collection ID，要查看的集合标识符"
    )
    page_size: int = Field(
        default=50,
        description="每页数据块数量，默认为50",
        ge=10,
        le=100
    )


class IntelligentSearchRequest(BaseModel):
    """智能搜索请求参数"""
    question: str = Field(
        description="用户问题，系统将自动分析并生成搜索计划"
    )
    available_datasets: List[str] = Field(
        description="可用的数据集ID列表，用于搜索范围限定"
    )
    generate_answer: bool = Field(
        default=True,
        description="是否生成综合答案，默认为True"
    )


class MultiDatasetSearchRequest(BaseModel):
    """多数据集搜索请求参数"""
    dataset_ids: List[str] = Field(
        description="数据集ID列表"
    )
    query: str = Field(
        description="搜索查询"
    )
    limit_per_dataset: int = Field(
        default=5,
        description="每个数据集的结果限制，默认为5",
        ge=1,
        le=20
    )


class DocumentAnalysisRequest(BaseModel):
    """文档分析请求参数"""
    question: str = Field(
        description="要分析的问题"
    )
    dataset_ids: List[str] = Field(
        description="要搜索的数据集ID列表"
    )
    max_docs: int = Field(
        default=5,
        description="最大分析文档数量，默认为5",
        ge=1,
        le=10
    )
    max_search_results: int = Field(
        default=20,
        description="每个数据集的最大搜索结果数，默认为20",
        ge=5,
        le=50
    ) 