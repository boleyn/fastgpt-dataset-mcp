#!/usr/bin/env python3
"""
知识库管理MCP服务器

基于FastMCP构建的知识库管理工具，支持目录树查看、内容搜索和Collection查看功能。
重构版本，采用更好的架构设计和统一的API客户端。
"""

import os
import asyncio
from typing import List
from fastmcp import FastMCP

# 导入新的架构组件
from src.config import config
from src.services import TreeService, SearchService, CollectionService, DocumentAnalysisService, FormatUtils

# 注意：传统工具依赖已移除，部分功能可能不可用

# 加载日志配置
try:
    from dotenv import load_dotenv
    load_dotenv("config/logging.env")
except:
    pass  # 如果日志配置文件不存在，使用默认设置

# 创建FastMCP实例
mcp = FastMCP("知识库管理工具 v2.0")

# 创建服务实例
tree_service = TreeService()
search_service = SearchService()
collection_service = CollectionService()
document_analysis_service = DocumentAnalysisService()


@mcp.tool("get_dataset_tree")
async def get_kb_tree(search_value: str = "", deep: int = 4) -> str:
    """
    📁 获取知识库目录树
    
    浏览知识库的目录结构，查看所有可用的数据集和文件夹。
    用于了解知识库的组织架构，找到相关的数据集ID用于后续搜索。
    
    参数:
        - search_value: 过滤关键词（可选），支持多关键词空格分隔，如"亚信 IPOSS"或"网络管理 系统"
        - deep: 目录深度（1-10，默认4）
    
    返回: 包含数据集ID、名称、类型的目录树结构
    
    💡 使用场景: 在进行文档搜索前，先了解有哪些可用的数据集
    🔍 搜索增强: 支持多关键词并发搜索，自动去重合并结果
    """
    parent_id = config.get_parent_id()
    return await tree_service.get_knowledge_base_tree(parent_id, search_value, deep)


@mcp.tool("search_dataset")
async def search_kb(dataset_id: str, text: str, limit: int = 10) -> str:
    """
    🔍 单数据集精确搜索
    
    在指定的单个数据集中搜索相关内容，返回最相关的文档片段。
    适用于已知目标数据集的精确搜索，找到特定文档的相关片段。
    
    参数:
        - dataset_id: 数据集ID（通过get_dataset_tree获取）
        - text: 搜索关键词
        - limit: 结果数量（1-50，默认10）
    
    返回: 包含文档片段、相关性评分和来源信息的搜索结果
    
    💡 使用场景: 定位特定数据集中的相关文档片段
    """
    return await search_service.search_knowledge_base(dataset_id, text, limit)


@mcp.tool("view_collection_content")
async def view_collection_content_tool(collection_id: str, page_size: int = 50) -> str:
    """
    📄 查看文档完整内容
    
    获取指定文档（collection）的所有内容块，查看完整的文档内容。
    适用于查看搜索到的文档的完整信息。
    
    参数:
        - collection_id: 文档ID（从搜索结果中获取）
        - page_size: 每页数据块数量（10-100，默认50）
    
    返回: 包含完整文档内容、文件信息和下载链接的详细报告
    
    💡 使用场景: 查看搜索定位到的文档的完整内容
    """
    return await collection_service.view_collection_content(collection_id, page_size)


@mcp.tool("intelligent_search_and_answer")
async def intelligent_search_and_answer(question: str, available_datasets: List[str], generate_answer: bool = True) -> str:
    """
    🤖 传统智能搜索问答
    
    基于关键词和搜索计划的传统智能问答系统。
    主要基于搜索片段进行分析，不获取完整文档内容。
    
    参数:
        - question: 用户问题
        - available_datasets: 可用数据集ID列表  
        - generate_answer: 是否生成综合答案（默认True）
    
    返回: 基于搜索片段的分析结果和答案
    
    💡 建议: 优先使用 smart_document_analysis 获得更准确的全文分析
    """
    # 使用新的智能文档分析服务作为替代实现
    if not generate_answer:
        # 如果不生成答案，则进行多数据集搜索
        return await multi_dataset_search(available_datasets, question, limit_per_dataset=10)
    
    # 默认情况下使用智能文档分析
    result = await document_analysis_service.analyze_documents_for_question(
        question,
        available_datasets,
        max_docs=5,
        max_search_results=20
    )
    
    # 添加说明，告知用户使用了升级版功能
    enhanced_result = f"""# 🔄 智能搜索问答结果
> **注意**: 传统功能已升级为更强大的智能文档分析，提供完整文档内容分析

{result}

---
💡 **功能升级说明**: 本次搜索使用了升级版的文档分析功能，相比传统的片段搜索，能够：
- 📄 获取完整文档内容（而非仅片段）
- 🎯 提供更准确的综合分析
- 📊 详细的搜索和分析过程报告
"""
    
    return enhanced_result


@mcp.tool("generate_search_plan")
async def generate_search_plan_tool(question: str, available_datasets: List[str]) -> str:
    """
    📋 生成搜索计划
    
    分析用户问题并生成详细的搜索策略和任务列表。
    主要用于了解搜索策略，不执行实际搜索。
    
    参数:
        - question: 用户问题
        - available_datasets: 可用数据集ID列表
    
    返回: 详细的搜索计划和策略
    
    💡 使用场景: 了解搜索策略，配合其他工具使用
    """
    # 分析问题并生成搜索计划
    import re
    
    # 提取关键词
    question_clean = re.sub(r'[^\w\s]', ' ', question)
    keywords = [word for word in question_clean.split() if len(word) > 1]
    
    # 生成搜索计划
    plan = f"""# 📋 智能搜索计划

## 🎯 问题分析
**原问题**: {question}

**提取的关键词**: {', '.join(keywords)}

## 📊 数据集信息
**可用数据集数量**: {len(available_datasets)}
**数据集列表**:
"""
    
    for i, dataset_id in enumerate(available_datasets, 1):
        plan += f"  {i}. `{dataset_id[:12]}...`\n"
    
    plan += f"""

## 🔍 搜索策略

### 1. 多关键词搜索策略
- **主要关键词**: {keywords[:3] if len(keywords) >= 3 else keywords}
- **次要关键词**: {keywords[3:] if len(keywords) > 3 else '无'}

### 2. 数据集搜索优先级
- **优先级**: 按数据集ID顺序搜索
- **搜索深度**: 每个数据集返回20个结果
- **结果筛选**: 基于相关性评分排序

### 3. 结果合并策略
- **去重机制**: 基于文档ID去重
- **排序方式**: 按相关性评分降序
- **最大结果数**: 5个最相关文档

## 🛠️ 执行步骤

### 步骤1: 多数据集搜索
```
multi_dataset_search(
    dataset_ids={available_datasets},
    query="{question}",
    limit_per_dataset=20
)
```

### 步骤2: 获取完整文档内容
基于搜索结果获取最相关的5个文档的完整内容

### 步骤3: 智能分析
使用AI对完整文档内容进行分析，生成综合答案

## 💡 推荐执行方案

**方案A: 一键智能分析（推荐）**
```
smart_document_analysis(
    question="{question}",
    dataset_ids={available_datasets},
    max_docs=5,
    max_search_results=20
)
```

**方案B: 分步执行**
1. 先执行 `multi_dataset_search` 了解搜索结果分布
2. 再使用 `view_collection_content` 查看具体文档
3. 最后手动分析整合信息

---
⚡ **建议**: 直接使用方案A进行一键智能分析，效率更高且结果更准确。
"""
    
    return plan


@mcp.tool("smart_document_analysis")
async def smart_document_analysis(question: str, dataset_ids: List[str], max_docs: int = 5, max_search_results: int = 20) -> str:
    """
    🧠 智能文档分析
    
    **推荐使用的核心工具** - 实现完整的智能文档分析工作流：
    1. 🔍 多数据集搜索定位相关文档
    2. 📄 获取定位文档的完整内容
    3. 🎯 分析多个文档内容
    4. ✨ 生成综合性答案
    
    参数:
        - question: 要分析的问题
        - dataset_ids: 要搜索的数据集ID列表
        - max_docs: 最大分析文档数量（1-10，默认5）
        - max_search_results: 每个数据集的最大搜索结果数（5-50，默认20）
    
    返回: 包含综合答案、相关文档内容和搜索过程的完整分析报告
    
    💡 使用场景: 基于问题智能分析多个文档并生成综合答案的首选工具
    """
    return await document_analysis_service.analyze_documents_for_question(
        question,
        dataset_ids,
        max_docs,
        max_search_results
    )


@mcp.tool("multi_dataset_search")
async def multi_dataset_search(dataset_ids: List[str], query: str, limit_per_dataset: int = 5) -> str:
    """
    🔍 多数据集搜索
    
    在多个数据集中同时搜索相同查询，快速定位相关文档片段。
    适用于跨多个数据集的初步搜索。
    
    参数:
        - dataset_ids: 数据集ID列表
        - query: 搜索关键词
        - limit_per_dataset: 每个数据集的结果限制（默认5）
    
    返回: 各数据集的搜索结果汇总
    
    💡 使用场景: 快速了解多个数据集中的相关内容分布
    """
    # 使用新架构的搜索服务
    try:
        results_by_dataset = {}
        total_results = 0
        
        # 在每个数据集中搜索
        for dataset_id in dataset_ids:
            try:
                # 使用新架构的搜索服务
                dataset_results = await search_service.search_knowledge_base_raw(
                    dataset_id, 
                    query, 
                    limit_per_dataset
                )
                results_by_dataset[dataset_id] = dataset_results
                total_results += len(dataset_results)
            except Exception as e:
                results_by_dataset[dataset_id] = []
                
        # 使用统一格式化工具生成头部
        markdown = FormatUtils.format_multi_search_summary(len(dataset_ids), total_results, query)
        
        for dataset_id, results in results_by_dataset.items():
            markdown += f"""### 数据集: {dataset_id[:8]}...
**结果数量**: {len(results)}

"""
            if results:
                for i, result in enumerate(results[:3], 1):  # 显示前3个结果
                    score = sum(s.get("value", 0) for s in result.score) if result.score else 0
                    
                    # 获取文件下载链接和详细信息
                    try:
                        download_link = await search_service.api_client.get_file_download_link(result.collection_id)
                        collection_detail = await search_service.api_client.get_collection_detail(result.collection_id)
                    except:
                        download_link = None
                        collection_detail = None
                    
                    markdown += f"""#### 结果 {i}
**内容**: {result.q[:200]}{'...' if len(result.q) > 200 else ''}

**相关性评分**: {score:.4f}

"""
                    
                    # 使用统一格式化工具生成来源信息
                    source_info = FormatUtils.format_source_info_block(
                        collection_id=result.collection_id,
                        source_name=result.source_name,
                        download_link=download_link,
                        collection_detail=collection_detail
                    )
                    markdown += source_info
                    
                    markdown += f"""💡 *可使用Collection ID查看完整文档: `view_collection_content(collection_id="{result.collection_id}")`*

---

"""
            else:
                markdown += "未找到相关结果\n\n"
        
        return markdown
        
    except Exception as e:
        return f"# 多数据集搜索错误\n\n{str(e)}"


def main():
    """主函数"""
    from src.logger import server_logger
    
    server_logger.info("🚀 启动知识库管理MCP服务器 v2.0")
    server_logger.info(f"📁 当前工作目录: {os.getcwd()}")
    server_logger.info(f"🔑 配置的父级目录ID: {config.get_parent_id()[:8]}...")
    
    # 显示可用的工具
    server_logger.info("🛠️  已注册的MCP工具:")
    server_logger.info("  📁 get_dataset_tree - 获取知识库目录树")
    server_logger.info("  🔍 search_dataset - 单数据集精确搜索") 
    server_logger.info("  📄 view_collection_content - 查看文档完整内容")
    server_logger.info("  🧠 smart_document_analysis - 【推荐】智能文档分析（搜索→全文→答案）")
    server_logger.info("  🔍 multi_dataset_search - 多数据集快速搜索")
    server_logger.info("  🤖 intelligent_search_and_answer - 传统智能搜索问答")
    server_logger.info("  📋 generate_search_plan - 生成搜索计划")
    
    server_logger.info(f"🌐 启动SSE服务器: http://{config.mcp_host}:{config.mcp_port}")
    server_logger.info(f"🔗 SSE端点: http://{config.mcp_host}:{config.mcp_port}/sse")
    server_logger.info("⚙️  MCP客户端配置:")
    server_logger.info(f'  "url": "http://{config.mcp_host}:{config.mcp_port}/sse?parentId={config.get_parent_id()}"')
    server_logger.info("=" * 60)
    
    # 启动MCP服务器
    mcp.run(transport="sse", host=config.mcp_host, port=config.mcp_port)


if __name__ == "__main__":
    main() 