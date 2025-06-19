#!/usr/bin/env python3
"""
知识库管理MCP服务器

基于FastMCP构建的知识库管理工具，支持目录树查看、内容搜索和Collection查看功能。
"""

import os
import asyncio
from typing import List, Union, Annotated, Optional, Tuple, Dict
from fastmcp import FastMCP, Context
from fastmcp.server.dependencies import get_http_request
from pydantic import Field
from src.logger import server_logger
# 导入架构组件
from src.config import config
from src.services import TreeService, SearchService, CollectionService, FormatUtils, KeywordService

def get_user_id_from_headers() -> Optional[str]:
    """从HTTP请求头部获取userId"""
    try:
        request = get_http_request()
        if hasattr(request, 'headers'):
            user_id = request.headers.get('user_id')
            if user_id:
                server_logger.debug(f"从HTTP请求头部获取user_id: {user_id}")
                return user_id
    except Exception as e:
        server_logger.debug(f"从HTTP请求头部获取user_id失败: {e}")
    
    return None

def get_chat_id_from_headers() -> Optional[str]:
    """从HTTP请求头部获取chat_id（用于日志）"""
    try:
        request = get_http_request()
        if hasattr(request, 'headers'):
            chat_id = request.headers.get('x-chat-id')
            if chat_id:
                server_logger.debug(f"从HTTP请求头部获取chat_id: {chat_id}")
                return chat_id
    except Exception as e:
        server_logger.debug(f"从HTTP请求头部获取chat_id失败: {e}")
    
    return None

def get_parent_id_from_request() -> str:
    """从HTTP请求参数获取parent_id"""
    try:
        request = get_http_request()
        if hasattr(request, 'query_params'):
            parent_id = request.query_params.get('parent_id')
            if parent_id:
                server_logger.debug(f"从HTTP请求参数获取parent_id: {parent_id}")
                return parent_id
    except Exception as e:
        server_logger.debug(f"从HTTP请求参数获取parent_id失败: {e}")
    
    return config.default_parent_id

# 创建FastMCP实例
mcp = FastMCP("知识库管理工具")

# 创建服务实例
tree_service = TreeService()
search_service = SearchService()
collection_service = CollectionService()
keyword_service = KeywordService()

# 工具定义

@mcp.tool()
async def get_dataset_tree(
    search_value: Annotated[str, Field(description="过滤关键词（可选）")] = "",
    deep: Annotated[int, Field(description="目录深度（1-10，默认4）", ge=1, le=10)] = 4,
    ctx: Context = None
) -> str:
    """
    【第一步工具】获取知识库目录树和数据集列表
    
    使用场景：
    - 用户想了解有哪些数据集可用时
    - 开始任何搜索操作前，必须先调用此工具获取有效的数据集ID
    - 查看知识库的整体结构
    
    重要：所有其他搜索工具都需要使用此工具返回的数据集ID
    """
    user_id = get_user_id_from_headers()
    chat_id = get_chat_id_from_headers()
    
    if not user_id:
        return "❌ 请在请求头中提供user-id"
    
    parent_id = get_parent_id_from_request()
        
    if ctx:
        await ctx.info(f"用户 {user_id} 正在获取知识库目录树")
    
    server_logger.info(f"用户 {user_id} 获取知识库目录树，chat_id: {chat_id}")
    
    return await tree_service.get_knowledge_base_tree(parent_id, search_value, deep, user_id)

@mcp.tool()
async def search_dataset(
    dataset_id: Annotated[str, Field(description="数据集ID（必须来自get_dataset_tree工具的返回结果）")],
    text: Annotated[str, Field(description="搜索关键词")],
    limit: Annotated[int, Field(description="结果数量（1-50，默认10）", ge=1, le=50)] = 10,
    ctx: Context = None
) -> str:
    """
    【单数据集搜索】在指定数据集中精确搜索内容
    
    使用场景：
    - 用户明确知道要在哪个特定数据集中搜索
    - 需要在单个数据集中获得详细的搜索结果
    - 对搜索精度要求较高时
    
    前置条件：必须先调用get_dataset_tree获取有效的dataset_id
    """
    user_id = get_user_id_from_headers()
    chat_id = get_chat_id_from_headers()
    
    if not user_id:
        return "❌ 请在请求头中提供user-id"
    
    if ctx:
        await ctx.info(f"用户 {user_id} 正在搜索数据集: {dataset_id}")
    
    server_logger.info(f"用户 {user_id} 搜索数据集 {dataset_id}，chat_id: {chat_id}")
    
    return await search_service.search_knowledge_base(dataset_id, text, limit, user_id)

@mcp.tool()
async def view_collection_content(
    collection_id: Annotated[str, Field(description="文档ID（必须来自search_dataset或multi_dataset_search的搜索结果）")],
    page_size: Annotated[int, Field(description="每页数据块数量（10-100，默认50）", ge=10, le=100)] = 50,
    ctx: Context = None
) -> str:
    """
    【查看文档详情】查看搜索结果中某个文档的完整内容
    
    使用场景：
    - 用户对搜索结果中的某个文档感兴趣，想查看完整内容
    - 需要深入了解文档的详细信息
    - 搜索结果的片段信息不够详细时
    
    前置条件：必须先进行搜索获得collection_id
    """
    user_id = get_user_id_from_headers()
    chat_id = get_chat_id_from_headers()
    
    if not user_id:
        return "❌ 请在请求头中提供user-id"
    
    if ctx:
        await ctx.info(f"用户 {user_id} 正在查看文档内容: {collection_id}")
    
    server_logger.info(f"用户 {user_id} 查看文档内容 {collection_id}，chat_id: {chat_id}")
    
    return await collection_service.view_collection_content(collection_id, page_size)

@mcp.tool()
async def multi_dataset_search(
    dataset_ids: Annotated[str, Field(description="数据集ID列表，逗号分隔（如：id1,id2,id3，必须来自get_dataset_tree）")],
    query: Annotated[str, Field(description="搜索关键词")],
    limit_per_dataset: Annotated[int, Field(description="每个数据集的结果数量（1-20，默认5）", ge=1, le=20)] = 5,
    ctx: Context = None
) -> str:
    """
    【多数据集搜索】同时在多个数据集中快速搜索
    
    使用场景：
    - 用户不确定信息在哪个数据集中
    - 需要跨多个数据集进行综合搜索
    - 进行主题相关的广泛搜索
    
    前置条件：必须先调用get_dataset_tree获取有效的数据集ID列表
    限制：最多支持5个数据集同时搜索
    """
    user_id = get_user_id_from_headers()
    chat_id = get_chat_id_from_headers()
    
    if not user_id:
        return "❌ 请在请求头中提供user-id"
    
    # 处理数据集ID列表
    dataset_ids_list = [id.strip() for id in dataset_ids.split(",") if id.strip()]
    
    if not dataset_ids_list:
        return "❌ 请提供至少一个数据集ID"
    
    # 权限过滤：只保留用户有权限访问的数据集
    from src.services import permission_service
    allowed_datasets = permission_service.filter_allowed_datasets(user_id, dataset_ids_list)
    
    if not allowed_datasets:
        return "❌ 权限不足：您没有访问任何指定数据集的权限。"
    
    # 更新为过滤后的数据集列表
    dataset_ids_list = allowed_datasets
    
    if len(dataset_ids_list) > 5:
        return f"❌ 数据集数量超出限制，最多支持5个数据集"
    
    if ctx:
        await ctx.info(f"用户 {user_id} 开始多数据集搜索，共 {len(dataset_ids_list)} 个数据集")
    
    server_logger.info(f"用户 {user_id} 开始多数据集搜索，共 {len(dataset_ids_list)} 个数据集，chat_id: {chat_id}")
    
    # 并行搜索多个数据集
    async def search_single_dataset(dataset_id: str) -> tuple[str, str]:
        try:
            result = await search_service.search_knowledge_base(dataset_id, query, limit_per_dataset, user_id)
            return dataset_id, result
        except Exception as e:
            return dataset_id, f"❌ 搜索失败: {str(e)}"
    
    # 执行并行搜索
    tasks = [search_single_dataset(dataset_id) for dataset_id in dataset_ids_list]
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
• 搜索数据集: {len(dataset_ids_list)} 个
• 成功搜索: {successful_searches} 个
• 搜索关键词: "{query}"
• 每数据集限制: {limit_per_dataset} 条

📋 搜索结果:
{''.join(formatted_results)}

💡 提示: 如需查看完整文档内容，请使用 view_collection_content 工具
"""
    
    return summary

@mcp.tool()
async def expand_search_keywords(
    original_query: Annotated[str, Field(description="原始搜索关键词")],
    expansion_type: Annotated[str, Field(description="扩展类型：basic(基础扩展)/comprehensive(全面扩展)/contextual(上下文扩展)，默认comprehensive")] = "comprehensive",
    ctx: Context = None
) -> str:
    """
    【关键词优化】当搜索结果不理想时，智能扩展搜索关键词
    
    使用场景：
    - 搜索结果数量太少或质量不高
    - 用户的搜索词可能不够准确
    - 需要找到更多相关的搜索词组合
    
    建议使用时机：在search_dataset或multi_dataset_search结果不满意后使用
    """
    user_id = get_user_id_from_headers()
    chat_id = get_chat_id_from_headers()
    
    if not user_id:
        return "❌ 请在请求头中提供user-id"
    
    if ctx:
        await ctx.info(f"用户 {user_id} 正在进行关键词扩展: {original_query}")
    
    server_logger.info(f"用户 {user_id} 进行关键词扩展: {original_query}，chat_id: {chat_id}")
    
    try:
        expanded_keywords = await keyword_service.expand_keywords(original_query, expansion_type)
        return keyword_service.format_expansion_result(original_query, expanded_keywords, expansion_type)
    except ValueError as e:
        return f"❌ {str(e)}"
    except Exception as e:
        server_logger.error(f"关键词扩展失败: {e}")
        return f"❌ 关键词扩展失败: {str(e)}"

@mcp.tool()
async def explore_folder_contents(
    folder_id: Annotated[str, Field(description="文件夹ID（必须来自get_dataset_tree工具返回的folder类型节点）")],
    search_value: Annotated[str, Field(description="搜索关键词（可选）")] = "",
    deep: Annotated[int, Field(description="探索深度（1-10，默认6）", ge=1, le=10)] = 6,
    ctx: Context = None
) -> str:
    """
    【文件夹探索】深入查看文件夹内部的详细结构和内容
    
    使用场景：
    - 用户想了解某个文件夹内部的详细结构
    - 需要查看文件夹下的子文件夹和文件列表
    - 在层级较深的目录中寻找特定内容
    
    前置条件：folder_id必须来自get_dataset_tree中type为"folder"的节点
    """
    user_id = get_user_id_from_headers()
    chat_id = get_chat_id_from_headers()
    
    if not user_id:
        return "❌ 请在请求头中提供user-id"
    
    if ctx:
        await ctx.info(f"用户 {user_id} 正在探索文件夹: {folder_id}")
    
    server_logger.info(f"用户 {user_id} 探索文件夹: {folder_id}，chat_id: {chat_id}")
    
    return await tree_service.explore_folder_contents(folder_id, search_value, deep, user_id)

def main():
    """主函数"""
    server_logger.info("🚀 启动知识库管理MCP服务器")
    server_logger.info(f"📁 工作目录: {os.getcwd()}")
    server_logger.info("🌐 传输协议: Streamable HTTP")
    server_logger.info("📝 用户认证: 基于请求头user-id")
    server_logger.info("📝 日志追踪: 基于Chat ID机制")
    server_logger.info(f"🔧 服务配置: {config.mcp_host}:{config.mcp_port}")
    
    mcp.run(transport="streamable-http", host=config.mcp_host, port=config.mcp_port)

if __name__ == "__main__":
    main() 