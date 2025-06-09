#!/usr/bin/env python3
"""
知识库管理MCP服务器

基于FastMCP构建的知识库管理工具，支持目录树查看、内容搜索和Collection查看功能。
重构版本，采用更好的架构设计和统一的API客户端。
"""

import os
import asyncio
from typing import List
from fastmcp import FastMCP, Context

# 导入新的架构组件
from src.config import config
from src.services import TreeService, SearchService, CollectionService, FormatUtils

# 会话级别的parentId存储 - 使用session_id作为key
SESSION_PARENT_IDS = {}

def get_parent_id_from_context(ctx: Context) -> str:
    """从Context中获取或设置parentId"""
    from src.logger import server_logger
    
    # 获取会话标识
    session_id = getattr(ctx, 'client_id', None) or getattr(ctx, 'request_id', None) or 'default'
    
    # 首先尝试从HTTP请求中提取parentId（SSE连接时）
    current_url_parent_id = None
    try:
        # 使用新的依赖函数获取HTTP请求
        from fastmcp.server.dependencies import get_http_request
        request = get_http_request()
        
        if request and hasattr(request, 'query_params'):
            query_params = request.query_params
            if 'parentId' in query_params:
                parent_id = query_params['parentId']
                if parent_id and parent_id.strip():
                    current_url_parent_id = parent_id.strip()
    except Exception as e:
        server_logger.debug(f"无法获取HTTP请求或提取URL参数: {e}")
    
    # 如果URL中有parentId，检查是否与会话中存储的不同
    if current_url_parent_id:
        stored_parent_id = SESSION_PARENT_IDS.get(session_id)
        
        if stored_parent_id != current_url_parent_id:
            # URL中的parentId与存储的不同，更新存储
            SESSION_PARENT_IDS[session_id] = current_url_parent_id
            server_logger.info(f"🔄 检测到parentId变化，已更新: {current_url_parent_id[:8]}... (session: {session_id[:8]}...)")
            return current_url_parent_id
        else:
            # URL中的parentId与存储的相同
            server_logger.info(f"🔑 使用会话存储的parentId: {stored_parent_id[:8]}... (session: {session_id[:8]}...)")
            return stored_parent_id
    
    # 检查是否已经有存储的parentId（没有URL参数的情况）
    if session_id in SESSION_PARENT_IDS:
        parent_id = SESSION_PARENT_IDS[session_id]
        server_logger.info(f"🔑 使用会话存储的parentId: {parent_id[:8]}... (session: {session_id[:8]}...)")
        return parent_id
    
    # 使用默认配置
    default_parent_id = config.default_parent_id
    SESSION_PARENT_IDS[session_id] = default_parent_id
    server_logger.info(f"🔑 使用默认parentId: {default_parent_id[:8]}... (session: {session_id[:8]}...)")
    return default_parent_id

# 创建FastMCP实例
mcp = FastMCP("知识库管理工具 v2.0")

# 创建服务实例
tree_service = TreeService()
search_service = SearchService()
collection_service = CollectionService()



@mcp.tool("get_dataset_tree")
async def get_kb_tree(search_value: str = "", deep: int = 4, ctx: Context = None) -> str:
    """
    获取知识库目录树
    
    浏览知识库的目录结构，查看所有可用的数据集和文件夹。
    用于了解知识库的组织架构，找到相关的数据集ID用于后续搜索。
    
    Args:
        search_value: 过滤关键词（可选），支持多关键词空格分隔，如"** IPOSS"或"网络管理 系统"
        deep: 目录深度（1-10，默认4）
    
    Returns:
        包含数据集ID、名称、类型的目录树结构
    """
    parent_id = get_parent_id_from_context(ctx)
    
    # 打印调试信息
    from src.logger import server_logger
    server_logger.info(f"🔍 当前使用的parentId: {parent_id}")
    
    return await tree_service.get_knowledge_base_tree(parent_id, search_value, deep)

@mcp.tool("search_dataset")
async def search_kb(dataset_id: str, text: str, limit: int = 10, ctx: Context = None) -> str:
    """
    单数据集精确搜索
    
    在指定的单个数据集中搜索相关内容，返回最相关的文档片段。
    适用于已知目标数据集的精确搜索，找到特定文档的相关片段。
    
    Args:
        dataset_id: 数据集ID（通过get_dataset_tree获取）
        text: 搜索关键词
        limit: 结果数量（1-50，默认10）
    
    Returns:
        包含文档片段、相关性评分、collectionId、文件名和下载链接的搜索结果
    """
    return await search_service.search_knowledge_base(dataset_id, text, limit)

@mcp.tool("view_collection_content")
async def view_collection_content_tool(collection_id: str, page_size: int = 50, ctx: Context = None) -> str:
    """
    查看文档完整内容
    
    获取指定文档（collection）的所有内容块，查看完整的文档内容。
    适用于查看搜索到的文档的完整信息。
    
    Args:
        collection_id: 文档ID（从搜索结果中获取）
        page_size: 每页数据块数量（10-100，默认50）
    
    Returns:
        包含完整文档内容、文件信息和下载链接的详细报告
    """
    return await collection_service.view_collection_content(collection_id, page_size)

@mcp.tool("multi_dataset_search")
async def multi_dataset_search(dataset_ids: List[str], query: str, limit_per_dataset: int = 5, ctx: Context = None) -> str:
    """
    多数据集快速搜索
    
    在多个数据集中并行搜索，快速获取相关信息概览。
    适用于跨数据集的信息收集和比较分析。
    
    Args:
        dataset_ids: 数据集ID列表
        query: 搜索关键词
        limit_per_dataset: 每个数据集的结果数量（1-20，默认5）
    
    Returns:
        按数据集分组的搜索结果汇总，包含collectionId、文件名和下载链接
    """
    from src.logger import server_logger
    
    if not dataset_ids:
        return "❌ 请提供至少一个数据集ID"
    
    if not query.strip():
        return "❌ 请提供搜索关键词"
    
    server_logger.info(f"开始多数据集搜索 | 数据集数量: {len(dataset_ids)} | 关键词: '{query}' | 每个数据集限制: {limit_per_dataset}")
    
    # 并行搜索多个数据集
    async def search_single_dataset(dataset_id: str) -> tuple[str, str]:
        try:
            result = await search_service.search_knowledge_base(dataset_id, query, limit_per_dataset)
            return dataset_id, result
        except Exception as e:
            server_logger.error(f"搜索数据集 {dataset_id} 失败: {e}")
            return dataset_id, f"❌ 搜索失败: {str(e)}"
    
    # 执行并行搜索
    tasks = [search_single_dataset(dataset_id) for dataset_id in dataset_ids]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # 整理结果
    formatted_results = []
    successful_searches = 0
    
    for result in results:
        if isinstance(result, Exception):
            formatted_results.append(f"❌ 搜索异常: {str(result)}")
        else:
            dataset_id, search_result = result
            if "❌" not in search_result:
                successful_searches += 1
            
            formatted_results.append(f"\n📁 数据集: {dataset_id[:8]}...\n{search_result}")
    
    # 生成汇总报告
    summary = f"""
🔍 多数据集搜索完成

📊 搜索统计:
• 目标数据集: {len(dataset_ids)} 个
• 成功搜索: {successful_searches} 个
• 搜索关键词: "{query}"
• 每数据集限制: {limit_per_dataset} 条

📋 搜索结果:
{''.join(formatted_results)}

💡 提示: 如需查看完整文档内容，请使用 view_collection_content 工具
"""
    
    server_logger.info(f"多数据集搜索完成 | 成功: {successful_searches}/{len(dataset_ids)}")
    
    return summary

def main():
    """主函数"""
    from src.logger import server_logger
    
    server_logger.info("🚀 启动知识库管理MCP服务器 v2.0")
    server_logger.info(f"📁 当前工作目录: {os.getcwd()}")
    
    # 显示工具信息
    server_logger.info("🛠️  已注册的MCP工具:")
    server_logger.info("  📁 get_dataset_tree - 获取知识库目录树")
    server_logger.info("  🔍 search_dataset - 单数据集精确搜索")
    server_logger.info("  📄 view_collection_content - 查看文档完整内容")
    server_logger.info("  🔍 multi_dataset_search - 多数据集快速搜索")
    
    # 启动信息
    server_logger.info("🌐 启动SSE服务器: http://0.0.0.0:18007")
    server_logger.info("🔗 SSE端点: http://0.0.0.0:18007/sse")
    server_logger.info("⚙️  MCP客户端配置:")
    server_logger.info('  "url": "http://0.0.0.0:18007/sse"')
    server_logger.info("💡 提示: URL参数parentId会自动检测变化并更新会话存储")
    server_logger.info("=" * 60)
    
    # 使用FastMCP原生SSE支持
    mcp.run(transport="sse", host="0.0.0.0", port=18007)

if __name__ == "__main__":
    main() 