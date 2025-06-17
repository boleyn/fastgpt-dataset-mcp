#!/usr/bin/env python3
"""
知识库管理MCP服务器

基于FastMCP构建的知识库管理工具，支持目录树查看、内容搜索和Collection查看功能。
"""

import os
import asyncio
from typing import List, Union, Annotated, Optional, Tuple
from fastmcp import FastMCP, Context
from pydantic import Field
from src.logger import server_logger
# 导入架构组件
from src.config import config
from src.services import TreeService, SearchService, CollectionService, FormatUtils, KeywordService

def get_session_data(ctx: Context) -> Tuple[Optional[str], Optional[str]]:
    """从session获取用户ID和parent_id"""
    if not ctx or not ctx.session:
        return None, None
    
    try:
        connection_id = str(id(ctx.session))
        server_logger.debug(f"获取session数据，connection_id: {connection_id}")
        
        # 从session中获取存储的数据
        user_id = getattr(ctx.session, '_user_id', None)
        parent_id = getattr(ctx.session, '_parent_id', None)
        
        server_logger.debug(f"session数据: user_id={user_id}, parent_id={parent_id}")
        return user_id, parent_id
    except Exception as e:
        server_logger.error(f"获取session数据失败: {e}")
        return None, None

def set_session_data(ctx: Context, user_id: str, parent_id: str = None):
    """设置session数据"""
    if not ctx or not ctx.session:
        server_logger.error("Context或session不可用")
        return False
    
    try:
        connection_id = str(id(ctx.session))
        effective_parent_id = parent_id or config.default_parent_id
        
        # 将数据存储到session对象中
        ctx.session._user_id = user_id
        ctx.session._parent_id = effective_parent_id
        
        server_logger.info(f"设置session数据成功，connection_id: {connection_id}, user_id: {user_id}, parent_id: {effective_parent_id}")
        return True
    except Exception as e:
        server_logger.error(f"设置session数据失败: {e}")
        return False

def get_parent_id_from_request(ctx: Context) -> str:
    """从HTTP请求参数获取parent_id"""
    try:
        # 尝试从HTTP请求获取parent_id参数
        if hasattr(ctx, 'get_http_request'):
            request = ctx.get_http_request()
            if hasattr(request, 'query_params'):
                parent_id = request.query_params.get('parent_id')
                if parent_id:
                    server_logger.debug(f"从HTTP请求获取parent_id: {parent_id}")
                    return parent_id
    except Exception as e:
        server_logger.debug(f"从HTTP请求获取parent_id失败: {e}")
    
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
async def set_user_context(
    userid: Annotated[str, Field(description="用户ID")],
    ctx: Context = None
) -> str:
    """
    设置用户上下文
    
    AI第一步调用此工具设置用户身份和根目录。
    """
    if not ctx:
        return "❌ Context不可用"
    
    connection_id = str(id(ctx.session)) if ctx.session else "无session"
    server_logger.info(f"设置用户上下文，connection_id: {connection_id}, userid: {userid}")
    
    # 如果没有提供parent_id，尝试从HTTP请求获取
    effective_parent_id = get_parent_id_from_request(ctx)
    
    # 设置用户信息到session
    if set_session_data(ctx, userid, effective_parent_id):
        if ctx:
            await ctx.info(f"用户 {userid} 上下文已设置")
        
        return f"""
✅ 用户上下文已设置

📋 用户信息:
• 用户ID: {userid}
• 会话ID: {connection_id}

💡 现在可以开始使用数据查询工具
"""
    else:
        return "❌ 设置用户上下文失败"

@mcp.tool()
async def get_dataset_tree(
    search_value: Annotated[str, Field(description="过滤关键词（可选）")] = "",
    deep: Annotated[int, Field(description="目录深度（1-10，默认4）", ge=1, le=10)] = 4,
    ctx: Context = None
) -> str:
    """
    获取知识库目录树
    """
    userid, parent_id = get_session_data(ctx)
    if not userid:
        return "❌ 请先设置用户上下文"
    
    # 如果session中没有parent_id，使用默认值
    if not parent_id:
        parent_id = config.default_parent_id
        
    if ctx:
        await ctx.info(f"用户 {userid} 正在获取知识库目录树")
    
    return await tree_service.get_knowledge_base_tree(parent_id, search_value, deep)

@mcp.tool()
async def search_dataset(
    dataset_id: Annotated[str, Field(description="数据集ID")],
    text: Annotated[str, Field(description="搜索关键词")],
    limit: Annotated[int, Field(description="结果数量（1-50，默认10）", ge=1, le=50)] = 10,
    ctx: Context = None
) -> str:
    """
    单数据集精确搜索
    """
    userid, _ = get_session_data(ctx)
    if not userid:
        return "❌ 请先设置用户上下文"
    
    if ctx:
        await ctx.info(f"用户 {userid} 正在搜索数据集: {dataset_id}")
    
    return await search_service.search_knowledge_base(dataset_id, text, limit)

@mcp.tool()
async def view_collection_content(
    collection_id: Annotated[str, Field(description="文档ID")],
    page_size: Annotated[int, Field(description="每页数据块数量（10-100，默认50）", ge=10, le=100)] = 50,
    ctx: Context = None
) -> str:
    """
    查看文档完整内容
    """
    userid, _ = get_session_data(ctx)
    if not userid:
        return "❌ 请先设置用户上下文"
    
    if ctx:
        await ctx.info(f"用户 {userid} 正在查看文档内容: {collection_id}")
    
    return await collection_service.view_collection_content(collection_id, page_size)

@mcp.tool()
async def multi_dataset_search(
    dataset_ids: Annotated[str, Field(description="数据集ID的逗号分隔字符串，最多5个")],
    query: Annotated[str, Field(description="搜索关键词")],
    limit_per_dataset: Annotated[int, Field(description="每个数据集的结果数量（1-20，默认5）", ge=1, le=20)] = 5,
    ctx: Context = None
) -> str:
    """
    多数据集快速搜索
    """
    userid, _ = get_session_data(ctx)
    if not userid:
        return "❌ 请先设置用户上下文"
    
    # 处理数据集ID列表
    dataset_ids_list = [id.strip() for id in dataset_ids.split(",") if id.strip()]
    
    if not dataset_ids_list:
        return "❌ 请提供至少一个数据集ID"
    
    if len(dataset_ids_list) > 5:
        return f"❌ 数据集数量超出限制，最多支持5个数据集"
    
    if ctx:
        await ctx.info(f"用户 {userid} 开始多数据集搜索，共 {len(dataset_ids_list)} 个数据集")
    
    # 并行搜索多个数据集
    async def search_single_dataset(dataset_id: str) -> tuple[str, str]:
        try:
            result = await search_service.search_knowledge_base(dataset_id, query, limit_per_dataset)
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
    expansion_type: Annotated[str, Field(description="扩展类型 (basic/comprehensive/contextual，默认comprehensive)")] = "comprehensive",
    ctx: Context = None
) -> str:
    """
    智能关键词扩展工具
    """
    userid, _ = get_session_data(ctx)
    if not userid:
        return "❌ 请先设置用户上下文"
    
    if ctx:
        await ctx.info(f"用户 {userid} 正在进行关键词扩展: {original_query}")
    
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
    folder_id: Annotated[str, Field(description="文件夹ID")],
    search_value: Annotated[str, Field(description="搜索关键词（可选）")] = "",
    deep: Annotated[int, Field(description="探索深度（1-10，默认6）", ge=1, le=10)] = 6,
    ctx: Context = None
) -> str:
    """
    深入探索文件夹内容
    """
    userid, _ = get_session_data(ctx)
    if not userid:
        return "❌ 请先设置用户上下文"
    
    if ctx:
        await ctx.info(f"用户 {userid} 正在探索文件夹: {folder_id}")
    
    return await tree_service.explore_folder_contents(folder_id, search_value, deep)


@mcp.tool()
async def clear_user_context(ctx: Context = None) -> str:
    """
    清理用户上下文
    
    清除当前会话中的用户身份信息，用于会话结束或重新设置用户身份。
    """
    if not ctx or not ctx.session:
        return "❌ 无可用会话"
    
    connection_id = str(id(ctx.session))
    server_logger.info(f"清理用户上下文，connection_id: {connection_id}")
    
    try:
        # 清除session中的用户数据
        if hasattr(ctx.session, '_user_id'):
            delattr(ctx.session, '_user_id')
        if hasattr(ctx.session, '_parent_id'):
            delattr(ctx.session, '_parent_id')
        
        if ctx:
            await ctx.info("用户上下文已清理")
        
        return f"""
✅ 用户上下文已清理

📋 清理详情:
• 会话ID: {connection_id}
• 用户身份: 已清除
• 根目录信息: 已清除
• 会话状态: 已重置

💡 下次使用前请重新调用 set_user_context 设置用户身份
"""
    except Exception as e:
        server_logger.error(f"清理用户上下文失败: {e}")
        return f"❌ 清理用户上下文失败: {str(e)}"

def main():
    """主函数"""
    server_logger.info("🚀 启动知识库管理MCP服务器")
    server_logger.info(f"📁 工作目录: {os.getcwd()}")
    server_logger.info("🌐 传输协议: Streamable HTTP")
    server_logger.info("📝 会话管理: 基于MCP Session机制")
    
    mcp.run(transport="streamable-http", host="0.0.0.0", port=18008)

if __name__ == "__main__":
    main() 