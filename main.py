#!/usr/bin/env python3
"""
知识库管理MCP服务器

基于FastMCP构建的知识库管理工具，支持目录树查看、内容搜索和Collection查看功能。
重构版本，采用更好的架构设计和统一的API客户端。
"""

import os
import asyncio
from typing import List, Union, Annotated
from fastmcp import FastMCP, Context
from pydantic import Field

# 导入新的架构组件
from src.config import config
from src.services import TreeService, SearchService, CollectionService, FormatUtils, KeywordService

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
keyword_service = KeywordService()



@mcp.tool()
async def get_dataset_tree(
    search_value: Annotated[str, Field(description="过滤关键词（可选），支持多关键词空格分隔，如'** IPOSS'或'网络管理 系统'")] = "",
    deep: Annotated[int, Field(description="目录深度（1-10，默认4）", ge=1, le=10)] = 4,
    ctx: Context = None
) -> str:
    """
    获取知识库目录树
    
    浏览知识库的目录结构，查看所有可用的数据集和文件夹。
    用于了解知识库的组织架构，找到相关的数据集ID用于后续搜索。
    """
    parent_id = get_parent_id_from_context(ctx)
    
    # 打印调试信息
    from src.logger import server_logger
    server_logger.info(f"🔍 当前使用的parentId: {parent_id}")
    
    return await tree_service.get_knowledge_base_tree(parent_id, search_value, deep)

@mcp.tool()
async def search_dataset(
    dataset_id: Annotated[str, Field(description="数据集ID（通过get_dataset_tree获取）")],
    text: Annotated[str, Field(description="搜索关键词")],
    limit: Annotated[int, Field(description="结果数量（1-50，默认10）", ge=1, le=50)] = 10,
    ctx: Context = None
) -> str:
    """
    单数据集精确搜索
    
    在指定的单个数据集中搜索相关内容，返回最相关的文档片段。
    适用于已知目标数据集的精确搜索，找到特定文档的相关片段。
    """
    return await search_service.search_knowledge_base(dataset_id, text, limit)

@mcp.tool()
async def view_collection_content(
    collection_id: Annotated[str, Field(description="文档ID（从搜索结果中获取）")],
    page_size: Annotated[int, Field(description="每页数据块数量（10-100，默认50）", ge=10, le=100)] = 50,
    ctx: Context = None
) -> str:
    """
    查看文档完整内容
    
    获取指定文档（collection）的所有内容块，查看完整的文档内容。
    适用于查看搜索到的文档的完整信息。
    """
    return await collection_service.view_collection_content(collection_id, page_size)

@mcp.tool()
async def multi_dataset_search(
    dataset_ids: Annotated[str, Field(description="数据集ID的逗号分隔字符串，最多5个（如：'id1,id2,id3'）")],
    query: Annotated[str, Field(description="搜索关键词")],
    limit_per_dataset: Annotated[int, Field(description="每个数据集的结果数量（1-20，默认5）", ge=1, le=10)] = 5,
    ctx: Context = None
) -> str:
    """
    多数据集快速搜索
    
    在多个数据集中并行搜索，快速获取相关信息概览。
    适用于跨数据集的信息收集和比较分析。
    """
    from src.logger import server_logger
    
    # 记录原始输入参数
    server_logger.info(f"原始dataset_ids参数: {dataset_ids} (类型: {type(dataset_ids)})")
    
    # 处理逗号分隔的字符串
    if not isinstance(dataset_ids, str):
        server_logger.error(f"❌ dataset_ids必须是字符串类型: {type(dataset_ids)}")
        return f"❌ dataset_ids参数必须是字符串"
    
    # 按逗号分割并去除空白
    dataset_ids_list = [id.strip() for id in dataset_ids.split(",") if id.strip()]
    server_logger.info(f"检测到逗号分隔的dataset_ids，已分割为 {len(dataset_ids_list)} 个ID")
    
    # 验证每个dataset_id的格式
    for i, dataset_id in enumerate(dataset_ids_list):
        if len(dataset_id) == 0:
            server_logger.error(f"❌ dataset_ids[{i}] 为空字符串")
            return f"❌ 数据集ID不能为空"
        
        # 检查是否还包含逗号
        if "," in dataset_id:
            server_logger.error(f"❌ dataset_ids[{i}] 仍包含逗号: {dataset_id}")
            return f"❌ 数据集ID格式错误，不能包含逗号: {dataset_id}"
    
    if not dataset_ids_list:
        return "❌ 请提供至少一个数据集ID"
    
    if len(dataset_ids_list) > 5:
        return f"❌ 数据集数量超出限制，最多支持5个数据集，当前提供了{len(dataset_ids_list)}个"
    
    if not query.strip():
        return "❌ 请提供搜索关键词"
    
    # 确保limit_per_dataset是整数类型
    if isinstance(limit_per_dataset, str):
        try:
            limit_per_dataset = int(limit_per_dataset)
            server_logger.info(f"将limit_per_dataset从字符串转换为整数: {limit_per_dataset}")
        except ValueError:
            server_logger.error(f"❌ limit_per_dataset不是有效的数字: '{limit_per_dataset}'")
            return f"❌ limit_per_dataset必须是数字: '{limit_per_dataset}'"
    
    # 验证limit_per_dataset范围
    if not isinstance(limit_per_dataset, int) or limit_per_dataset < 1 or limit_per_dataset > 20:
        server_logger.error(f"❌ limit_per_dataset超出范围 (1-20): {limit_per_dataset}")
        return f"❌ limit_per_dataset必须在1-20之间: {limit_per_dataset}"
    
    server_logger.info(f"开始多数据集搜索 | 数据集数量: {len(dataset_ids_list)} | 关键词: '{query}' | 每个数据集限制: {limit_per_dataset}")
    
    # 并行搜索多个数据集
    async def search_single_dataset(dataset_id: str) -> tuple[str, str]:
        try:
            server_logger.info(f"正在搜索单个数据集: '{dataset_id}' (长度: {len(dataset_id)})")
            
            result = await search_service.search_knowledge_base(dataset_id, query, limit_per_dataset)
            return dataset_id, result
        except Exception as e:
            server_logger.error(f"搜索数据集 {dataset_id} 失败: {e}")
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
• 目标数据集: {len(dataset_ids_list)} 个
• 成功搜索: {successful_searches} 个
• 搜索关键词: "{query}"
• 每数据集限制: {limit_per_dataset} 条

📋 搜索结果:
{''.join(formatted_results)}

💡 提示: 如需查看完整文档内容，请使用 view_collection_content 工具
"""
    
    server_logger.info(f"多数据集搜索完成 | 成功: {successful_searches}/{len(dataset_ids_list)}")
    
    return summary

@mcp.tool()
async def expand_search_keywords(
    original_query: Annotated[str, Field(description="原始搜索关键词")],
    expansion_type: Annotated[str, Field(description="扩展类型 (basic/comprehensive/contextual，默认comprehensive)")] = "comprehensive",
    ctx: Context = None
) -> str:
    """
    智能关键词扩展工具
    
    根据原始查询词生成扩展关键词，支持多种扩展策略。
    用于实现prompt要求的"核心词 → 同义词 → 相关词 → 上下文词"扩展策略。
    """
    try:
        expanded_keywords = await keyword_service.expand_keywords(original_query, expansion_type)
        return keyword_service.format_expansion_result(original_query, expanded_keywords, expansion_type)
    except ValueError as e:
        return f"❌ {str(e)}"
    except Exception as e:
        from src.logger import server_logger
        server_logger.error(f"关键词扩展失败: {e}")
        return f"❌ 关键词扩展失败: {str(e)}"



@mcp.tool()
async def explore_folder_contents(
    folder_id: Annotated[str, Field(description="文件夹ID（从get_dataset_tree结果中获取）")],
    search_value: Annotated[str, Field(description="搜索关键词（可选），支持多关键词空格分隔")] = "",
    deep: Annotated[int, Field(description="探索深度（1-10，默认6）", ge=1, le=10)] = 6,
    ctx: Context = None
) -> str:
    """
    深入探索文件夹内容
    
    当get_dataset_tree返回文件夹时，使用此工具深入探索文件夹内部的所有知识库和子文件夹。
    支持更深层次的搜索，帮助发现文件夹深处的数据集。
    
    Args:
        folder_id: 文件夹ID（从get_dataset_tree结果中获取）
        search_value: 搜索关键词（可选），支持多关键词空格分隔
        deep: 探索深度（1-10，默认6）
    
    Returns:
        包含文件夹内所有知识库和子文件夹的详细报告，以及使用建议
    """
    return await tree_service.explore_folder_contents(folder_id, search_value, deep)

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
    server_logger.info("  🎯 expand_search_keywords - 智能关键词扩展")
    server_logger.info("  📂 explore_folder_contents - 深入探索文件夹内容")
    
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