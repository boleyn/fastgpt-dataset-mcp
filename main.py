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

# 全局 chat_id 会话存储
_chat_sessions: Dict[str, Dict[str, str]] = {}

def get_session_data(ctx: Context) -> Tuple[Optional[str], Optional[str]]:
    """从全局chat_id存储获取用户ID和parent_id"""
    try:
        # 获取chat_id作为会话标识符
        chat_id = get_chat_id_from_headers()
        if not chat_id:
            server_logger.debug("未获取到chat_id")
            return None, None
            
        server_logger.debug(f"获取session数据，chat_id: {chat_id}")
        
        # 从全局存储中获取数据
        session_data = _chat_sessions.get(chat_id, {})
        user_id = session_data.get('user_id')
        parent_id = session_data.get('parent_id')
        
        server_logger.debug(f"session数据: chat_id={chat_id}, user_id={user_id}, parent_id={parent_id}")
        return user_id, parent_id
    except Exception as e:
        server_logger.error(f"获取session数据失败: {e}")
        return None, None

def set_session_data(ctx: Context, user_id: str, parent_id: str = None):
    """设置chat_id会话数据到全局存储"""
    try:
        # 获取chat_id作为会话标识符
        chat_id = get_chat_id_from_headers()
        if not chat_id:
            server_logger.error("未获取到chat_id，无法设置session数据")
            return False
            
        effective_parent_id = parent_id or config.default_parent_id
        
        # 将数据存储到全局存储中
        _chat_sessions[chat_id] = {
            'user_id': user_id,
            'parent_id': effective_parent_id,
            'chat_id': chat_id
        }
        
        server_logger.info(f"设置session数据成功，chat_id: {chat_id}, user_id: {user_id}, parent_id: {effective_parent_id}")
        server_logger.debug(f"当前全局会话存储: {list(_chat_sessions.keys())}")
        return True
    except Exception as e:
        server_logger.error(f"设置session数据失败: {e}")
        return False

def get_parent_id_from_request() -> str:
    """从HTTP请求参数获取parent_id"""
    try:
        # 使用新的方式获取HTTP请求
        request = get_http_request()
        if hasattr(request, 'query_params'):
            parent_id = request.query_params.get('parent_id')
            if parent_id:
                server_logger.debug(f"从HTTP请求参数获取parent_id: {parent_id}")
                return parent_id
    except Exception as e:
        server_logger.debug(f"从HTTP请求参数获取parent_id失败: {e}")
    
    return config.default_parent_id

def get_chat_id_from_headers() -> Optional[str]:
    """从HTTP请求头部获取chat_id"""
    try:
        # 使用新的方式获取HTTP请求
        request = get_http_request()
        if hasattr(request, 'headers'):
            chat_id = request.headers.get('x-chat-id')
            if chat_id:
                server_logger.debug(f"从HTTP请求头部获取chat_id: {chat_id}")
                return chat_id
    except Exception as e:
        server_logger.debug(f"从HTTP请求头部获取chat_id失败: {e}")
    
    return None

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
    设置用户上下文（必须首先调用）
    """
    chat_id = get_chat_id_from_headers()
    if not chat_id:
        return "❌ 未获取到Chat ID，无法设置用户上下文"
    
    server_logger.info(f"设置用户上下文，chat_id: {chat_id}, userid: {userid}")
    
    # 如果没有提供parent_id，尝试从HTTP请求获取
    effective_parent_id = get_parent_id_from_request()
    
    # 设置用户信息到全局存储
    if set_session_data(ctx, userid, effective_parent_id):
        if ctx:
            await ctx.info(f"用户 {userid} 上下文已设置")
        
        return f"""
✅ 用户上下文已设置

📋 用户信息:
• 用户ID: {userid}
• Chat ID: {chat_id}


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
    获取知识库目录树（获取有效的数据集ID）
    """
    userid, parent_id = get_session_data(ctx)
    if not userid:
        return "❌ 请先设置用户上下文"
    
    # 如果session中没有parent_id，使用默认值
    if not parent_id:
        parent_id = config.default_parent_id
        
    if ctx:
        await ctx.info(f"用户 {userid} 正在获取知识库目录树")
    
    return await tree_service.get_knowledge_base_tree(parent_id, search_value, deep, userid)

@mcp.tool()
async def search_dataset(
    dataset_id: Annotated[str, Field(description="数据集ID（必须来自get_dataset_tree）")],
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
    
    return await search_service.search_knowledge_base(dataset_id, text, limit, userid)

@mcp.tool()
async def view_collection_content(
    collection_id: Annotated[str, Field(description="文档ID（来自搜索结果）")],
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
    dataset_ids: Annotated[str, Field(description="数据集ID列表，逗号分隔（必须来自get_dataset_tree）")],
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
    
    # 权限过滤：只保留用户有权限访问的数据集
    from src.services import permission_service
    allowed_datasets = permission_service.filter_allowed_datasets(userid, dataset_ids_list)
    
    if not allowed_datasets:
        return "❌ 权限不足：您没有访问任何指定数据集的权限。"
    
    # 更新为过滤后的数据集列表
    dataset_ids_list = allowed_datasets
    
    if len(dataset_ids_list) > 5:
        return f"❌ 数据集数量超出限制，最多支持5个数据集"
    
    if ctx:
        await ctx.info(f"用户 {userid} 开始多数据集搜索，共 {len(dataset_ids_list)} 个数据集")
    
    # 并行搜索多个数据集
    async def search_single_dataset(dataset_id: str) -> tuple[str, str]:
        try:
            result = await search_service.search_knowledge_base(dataset_id, query, limit_per_dataset, userid)
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
    智能关键词扩展（搜索结果不理想时使用）
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
    folder_id: Annotated[str, Field(description="文件夹ID（必须来自get_dataset_tree）")],
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
    
    return await tree_service.explore_folder_contents(folder_id, search_value, deep, userid)


@mcp.tool()
async def clear_user_context(ctx: Context = None) -> str:
    """
    清理用户上下文
    """
    chat_id = get_chat_id_from_headers()
    if not chat_id:
        return "❌ 未获取到Chat ID，无法清理用户上下文"
    
    server_logger.info(f"清理用户上下文，chat_id: {chat_id}")
    
    try:
        # 从全局存储中清除用户数据
        if chat_id in _chat_sessions:
            del _chat_sessions[chat_id]
            server_logger.debug(f"已清理chat_id: {chat_id}，剩余会话: {list(_chat_sessions.keys())}")
        
        if ctx:
            await ctx.info("用户上下文已清理")
        
        return f"""
✅ 用户上下文已清理

📋 清理详情:
• Chat ID: {chat_id}
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
    server_logger.info("📝 会话管理: 基于Chat ID机制")
    server_logger.info(f"🔧 服务配置: {config.mcp_host}:{config.mcp_port}")
    
    mcp.run(transport="streamable-http", host=config.mcp_host, port=config.mcp_port)

if __name__ == "__main__":
    main() 