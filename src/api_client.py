"""
统一的API客户端
"""

import aiohttp
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import quote

from .config import config
from .models import (
    DatasetNode, SearchResult, DataChunk, 
    CollectionInfo, CollectionFileInfo
)
from .logger import api_logger


class APIClient:
    """统一的API客户端"""
    
    def __init__(self):
        self.base_url = config.api_base_url
        self.headers = config.api_headers
    
    async def _make_request(self, method: str, endpoint: str, params: Optional[dict] = None, 
                           json_data: Optional[dict] = None) -> dict:
        """发起HTTP请求的通用方法"""
        url = f"{self.base_url}{endpoint}"
        
        async with aiohttp.ClientSession() as session:
            async with session.request(
                method=method,
                url=url,
                headers=self.headers,
                params=params,
                json=json_data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("code") == 200:
                        return result.get("data", {})
                    else:
                        raise Exception(f"API错误: {result.get('message', '未知错误')}")
                else:
                    raise Exception(f"HTTP请求失败: {response.status}")
    
    async def get_dataset_tree(self, parent_id: str, search_value: str = "", deep: int = 4) -> List[DatasetNode]:
        """获取数据集目录树"""
        endpoint = "/api/core/dataset/list"
        json_data = {
            "parentId": parent_id,
            "searchValue": search_value,
            "deep": deep
        }
        
        result = await self._make_request("POST", endpoint, json_data=json_data)
        
        nodes = []
        for item in result:
            nodes.append(DatasetNode(**item))
        
        return nodes
    
    async def search_dataset(self, dataset_id: str, text: str, limit: int = 10) -> List[SearchResult]:
        """搜索数据集"""
        endpoint = "/api/core/dataset/searchTest"
        json_data = {
            "datasetId": dataset_id,
            "text": text,
            "searchMode": config.search_mode,
            "embeddingWeight": config.embedding_weight,
            "usingReRank": config.using_rerank,
            "rerankWeight": config.rerank_weight,
            "limit": limit
        }
        
        result = await self._make_request("POST", endpoint, json_data=json_data)
        
        search_results = []
        for item in result.get("list", []):
            search_results.append(SearchResult(**item))
        
        return search_results
    
    async def get_collection_chunks_page(self, collection_id: str, offset: int, page_size: int) -> Tuple[List[DataChunk], bool]:
        """获取collection数据块分页"""
        endpoint = "/api/core/dataset/data/v2/list"
        json_data = {
            "offset": offset,
            "pageSize": page_size,
            "collectionId": collection_id,
            "searchText": ""
        }
        
        result = await self._make_request("POST", endpoint, json_data=json_data)
        chunks_data = result.get("list", [])
        
        # 转换为DataChunk对象
        chunks = []
        for item in chunks_data:
            chunks.append(DataChunk(**item))
        
        # 判断是否还有更多数据
        has_more = len(chunks_data) == page_size
        
        return chunks, has_more
    
    async def get_collection_detail(self, collection_id: str) -> Optional[CollectionInfo]:
        """获取collection详细信息（使用新的detail接口）"""
        endpoint = "/api/core/dataset/collection/detail"
        params = {"id": collection_id}
        
        try:
            result = await self._make_request("GET", endpoint, params=params)
            return CollectionInfo(**result)
        except Exception as e:
            api_logger.warning(f"获取collection详细信息失败: {str(e)}")
            return None
    
    async def get_collection_file_info(self, collection_id: str) -> Optional[CollectionFileInfo]:
        """获取collection文件信息（用于下载链接）"""
        endpoint = "/api/core/dataset/collection/read"
        json_data = {"collectionId": collection_id}
        
        try:
            result = await self._make_request("POST", endpoint, json_data=json_data)
            return CollectionFileInfo(**result)
        except Exception as e:
            api_logger.warning(f"获取collection文件信息失败: {str(e)}")
            return None
    
    async def get_file_download_link(self, collection_id: str) -> Optional[str]:
        """获取文件下载链接"""
        file_info = await self.get_collection_file_info(collection_id)
        
        if file_info and file_info.type == "url":
            return f"{self.base_url}{file_info.value}"
        
        return None


# 全局API客户端实例
api_client = APIClient() 