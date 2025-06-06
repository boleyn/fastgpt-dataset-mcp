"""
文档分析服务

实现智能文档分析工作流：
1. 搜索定位相关文档
2. 查看文档全部内容
3. 分析多个文档
4. 生成综合答案
"""

from typing import List, Dict, Any, Set
from ..api_client import api_client
from ..models import SearchResult, DataChunk, CollectionInfo
from .search_service import SearchService
from .collection_service import CollectionService
from ..logger import analysis_logger


class DocumentAnalysisService:
    """文档分析服务"""
    
    def __init__(self):
        self.api_client = api_client
        self.search_service = SearchService()
        self.collection_service = CollectionService()
    
    async def analyze_documents_for_question(self, question: str, dataset_ids: List[str], 
                                           max_docs: int = 5, max_search_results: int = 20) -> str:
        """
        基于问题分析相关文档并生成答案
        
        工作流：
        1. 在多个数据集中搜索相关内容
        2. 识别最相关的文档（collection）
        3. 获取这些文档的完整内容
        4. 基于完整文档内容生成综合答案
        
        Args:
            question: 用户问题
            dataset_ids: 要搜索的数据集ID列表
            max_docs: 最大分析文档数量
            max_search_results: 每个数据集的最大搜索结果数
            
        Returns:
            包含搜索过程、文档分析和综合答案的Markdown文档
        """
        try:
            analysis_logger.info(f"开始文档分析 | 问题: '{question}' | 数据集数量: {len(dataset_ids)}")
            
            # 步骤1: 搜索定位相关文档
            search_results = await self._search_across_datasets(question, dataset_ids, max_search_results)
            
            if not search_results:
                return self._generate_no_results_response(question)
            
            # 步骤2: 识别最相关的文档
            relevant_collections = self._identify_relevant_collections(search_results, max_docs)
            
            # 步骤3: 获取文档完整内容
            document_contents = await self._get_document_contents(relevant_collections)
            
            # 步骤4: 生成综合答案
            return await self._generate_comprehensive_response(
                question, search_results, document_contents
            )
            
        except Exception as e:
            analysis_logger.error(f"文档分析失败: {str(e)}", exc_info=True)
            return f"# 文档分析错误\n\n分析过程中发生错误: {str(e)}"
    
    async def _search_across_datasets(self, question: str, dataset_ids: List[str], 
                                     max_results: int) -> Dict[str, List[SearchResult]]:
        """在多个数据集中搜索"""
        all_results = {}
        
        for dataset_id in dataset_ids:
            try:
                analysis_logger.debug(f"搜索数据集: {dataset_id[:8]}...")
                results = await self.api_client.search_dataset(dataset_id, question, max_results)
                if results:
                    all_results[dataset_id] = results
                    analysis_logger.debug(f"数据集 {dataset_id[:8]}... 找到 {len(results)} 个结果")
                else:
                    analysis_logger.debug(f"数据集 {dataset_id[:8]}... 没有找到结果")
            except Exception as e:
                error_msg = str(e)
                if "500" in error_msg:
                    analysis_logger.warning(f"搜索数据集 {dataset_id[:8]}... 失败: 服务器内部错误 (可能是数据集不可用)")
                else:
                    analysis_logger.warning(f"搜索数据集 {dataset_id[:8]}... 失败: {error_msg}")
                continue
        
        total_results = sum(len(results) for results in all_results.values())
        analysis_logger.info(f"搜索完成 | 总结果数: {total_results}")
        
        return all_results
    
    def _identify_relevant_collections(self, search_results: Dict[str, List[SearchResult]], 
                                     max_docs: int) -> List[Dict[str, Any]]:
        """识别最相关的文档集合"""
        collection_scores = {}
        collection_info = {}
        
        # 计算每个collection的相关性评分
        for dataset_id, results in search_results.items():
            for result in results:
                collection_id = result.collection_id
                
                # 计算评分
                score = sum(s.get("value", 0) for s in result.score)
                
                if collection_id not in collection_scores:
                    collection_scores[collection_id] = 0
                    collection_info[collection_id] = {
                        'dataset_id': dataset_id,
                        'source_name': result.source_name,
                        'sample_content': result.q[:200] + "..." if len(result.q) > 200 else result.q
                    }
                
                collection_scores[collection_id] += score
        
        # 按评分排序并选择前N个
        sorted_collections = sorted(
            collection_scores.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:max_docs]
        
        relevant_collections = []
        for collection_id, score in sorted_collections:
            info = collection_info[collection_id]
            relevant_collections.append({
                'collection_id': collection_id,
                'dataset_id': info['dataset_id'],
                'source_name': info['source_name'],
                'relevance_score': score,
                'sample_content': info['sample_content']
            })
        
        analysis_logger.info(f"识别到 {len(relevant_collections)} 个相关文档")
        return relevant_collections
    
    async def _get_document_contents(self, relevant_collections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """获取文档完整内容"""
        document_contents = []
        
        for collection_info in relevant_collections:
            collection_id = collection_info['collection_id']
            
            try:
                analysis_logger.debug(f"获取文档内容: {collection_info['source_name']}")
                
                # 获取collection详细信息
                detail = await self.api_client.get_collection_detail(collection_id)
                
                # 获取所有数据块
                all_chunks = []
                offset = 0
                page_size = 50
                
                while True:
                    chunks, has_more = await self.api_client.get_collection_chunks_page(
                        collection_id, offset, page_size
                    )
                    if not chunks:
                        break
                    all_chunks.extend(chunks)
                    if not has_more:
                        break
                    offset += page_size
                
                # 合并所有内容
                full_content = self._merge_chunks_content(all_chunks)
                
                document_contents.append({
                    'collection_id': collection_id,
                    'name': detail.name if detail else collection_info['source_name'],
                    'type': detail.type if detail else 'unknown',
                    'relevance_score': collection_info['relevance_score'],
                    'chunk_count': len(all_chunks),
                    'content': full_content,
                    'detail': detail
                })
                
                analysis_logger.debug(f"获取完成: {len(all_chunks)} 个数据块")
                
            except Exception as e:
                analysis_logger.warning(f"获取文档 {collection_id[:8]}... 内容失败: {str(e)}")
                continue
        
        analysis_logger.info(f"成功获取 {len(document_contents)} 个文档的完整内容")
        return document_contents
    
    def _merge_chunks_content(self, chunks: List[DataChunk]) -> str:
        """合并数据块内容"""
        content_parts = []
        
        for chunk in sorted(chunks, key=lambda x: x.chunk_index):
            if chunk.q.strip():
                content_parts.append(chunk.q.strip())
            if chunk.a.strip():
                content_parts.append(f"**答案**: {chunk.a.strip()}")
        
        return "\n\n".join(content_parts)
    
    async def _generate_comprehensive_response(self, question: str, 
                                             search_results: Dict[str, List[SearchResult]], 
                                             document_contents: List[Dict[str, Any]]) -> str:
        """生成综合响应"""
        
        # 构建响应文档
        response_parts = []
        
        # 1. 问题和概述
        response_parts.append(f"# 📖 智能文档分析结果")
        response_parts.append("")
        response_parts.append(f"## ❓ 分析问题")
        response_parts.append(f"> {question}")
        response_parts.append("")
        
        # 2. 分析概述
        total_search_results = sum(len(results) for results in search_results.values())
        response_parts.append(f"## 📊 分析概述")
        response_parts.append(f"- **搜索数据集数量**: {len(search_results)}")
        response_parts.append(f"- **搜索结果总数**: {total_search_results}")
        response_parts.append(f"- **分析文档数量**: {len(document_contents)}")
        response_parts.append("")
        
        # 3. 基于完整文档的综合答案
        if document_contents:
            response_parts.append(f"## 🎯 综合答案")
            response_parts.append("")
            
            # 简单的答案生成逻辑 - 可以后续集成更高级的AI答案生成
            answer = self._generate_simple_answer(question, document_contents)
            response_parts.append(answer)
            response_parts.append("")
        
        # 4. 相关文档详情
        response_parts.append(f"## 📋 相关文档列表")
        response_parts.append("")
        
        for i, doc in enumerate(document_contents, 1):
            response_parts.append(f"### 文档 {i}: {doc['name']}")
            response_parts.append("")
            response_parts.append(f"**文档类型**: {doc['type']}")
            response_parts.append(f"**相关性评分**: {doc['relevance_score']:.4f}")
            response_parts.append(f"**数据块数量**: {doc['chunk_count']}")
            response_parts.append("")
            
            # 显示部分内容
            content_preview = doc['content'][:500] + "..." if len(doc['content']) > 500 else doc['content']
            response_parts.append(f"**内容预览**:")
            response_parts.append("```")
            response_parts.append(content_preview)
            response_parts.append("```")
            response_parts.append("")
            response_parts.append("---")
            response_parts.append("")
        
        # 5. 搜索过程详情
        response_parts.append(f"## 🔍 搜索过程详情")
        response_parts.append("")
        
        for dataset_id, results in search_results.items():
            response_parts.append(f"### 数据集: {dataset_id[:8]}...")
            response_parts.append(f"**结果数量**: {len(results)}")
            response_parts.append("")
            
            for i, result in enumerate(results[:3], 1):  # 显示前3个结果
                response_parts.append(f"#### 搜索结果 {i}")
                response_parts.append(f"**来源**: {result.source_name}")
                response_parts.append(f"**内容**: {result.q[:150]}{'...' if len(result.q) > 150 else ''}")
                response_parts.append("")
        
        return "\n".join(response_parts)
    
    def _generate_simple_answer(self, question: str, document_contents: List[Dict[str, Any]]) -> str:
        """生成简单答案（基于关键词匹配和内容摘要）"""
        
        # 提取问题关键词
        question_keywords = set(question.lower().split())
        
        # 收集相关内容片段
        relevant_snippets = []
        
        for doc in document_contents:
            content = doc['content'].lower()
            
            # 查找包含关键词的段落
            paragraphs = doc['content'].split('\n\n')
            for paragraph in paragraphs:
                if any(keyword in paragraph.lower() for keyword in question_keywords):
                    if len(paragraph.strip()) > 50:  # 过滤太短的段落
                        relevant_snippets.append({
                            'content': paragraph.strip(),
                            'source': doc['name'],
                            'relevance': doc['relevance_score']
                        })
        
        # 按相关性排序
        relevant_snippets.sort(key=lambda x: x['relevance'], reverse=True)
        
        # 生成答案
        if not relevant_snippets:
            return "根据分析的文档内容，未能找到直接回答该问题的具体信息。建议查看下方的相关文档内容。"
        
        answer_parts = []
        answer_parts.append("基于对相关文档的全文分析，找到以下信息：")
        answer_parts.append("")
        
        # 添加最相关的片段
        for i, snippet in enumerate(relevant_snippets[:3], 1):
            answer_parts.append(f"**{i}. 来自《{snippet['source']}》:**")
            answer_parts.append("")
            answer_parts.append(snippet['content'])
            answer_parts.append("")
        
        if len(relevant_snippets) > 3:
            answer_parts.append(f"*（另有 {len(relevant_snippets) - 3} 个相关片段，详见下方文档内容）*")
            answer_parts.append("")
        
        return "\n".join(answer_parts)
    
    def _generate_no_results_response(self, question: str) -> str:
        """生成无结果响应"""
        return f"""# 📖 智能文档分析结果

## ❓ 分析问题
> {question}

## ❌ 分析结果
未能在指定的数据集中找到与该问题相关的文档内容。

## 💡 建议
1. 尝试使用不同的关键词重新搜索
2. 检查数据集是否包含相关内容
3. 扩大搜索范围或调整搜索参数
""" 