"""
权限检查装饰器

用于MCP工具函数的权限控制，基于userid参数进行权限验证
"""

import functools
from typing import Callable, Any
from fastmcp import Context
from src.services.permission_service import permission_service
from src.logger import server_logger


def require_permission(tool_name: str = None):
    """
    权限检查装饰器
    
    Args:
        tool_name: 工具名称，如果不提供则使用函数名
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # 从kwargs中提取userid和context
            userid = kwargs.get('userid')
            ctx = kwargs.get('ctx')
            
            # 如果没有userid参数，记录警告但允许执行（向后兼容）
            if userid is None:
                server_logger.warning(f"⚠️  工具 {func.__name__} 缺少userid参数，跳过权限检查")
                return await func(*args, **kwargs)
            
            # 获取实际的工具名称
            actual_tool_name = tool_name or func.__name__
            
            # 检查工具权限
            if not permission_service.check_tool_permission(userid, actual_tool_name):
                error_msg = f"🚫 用户 {userid} 无权限使用工具: {actual_tool_name}"
                server_logger.error(error_msg)
                
                # 如果有context，记录到客户端日志
                if ctx:
                    await ctx.error(f"权限不足：无法使用工具 {actual_tool_name}")
                
                return f"❌ 权限不足：您没有使用工具 '{actual_tool_name}' 的权限。请联系管理员获取相应权限。"
            
            # 记录权限检查通过
            server_logger.debug(f"✅ 用户 {userid} 权限检查通过: {actual_tool_name}")
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def validate_dataset_access(func: Callable) -> Callable:
    """
    数据集访问验证装饰器
    
    检查用户是否有权限访问指定的数据集
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        userid = kwargs.get('userid')
        dataset_id = kwargs.get('dataset_id')
        dataset_ids = kwargs.get('dataset_ids')
        ctx = kwargs.get('ctx')
        
        # 如果没有userid，跳过检查
        if userid is None:
            server_logger.warning(f"⚠️  工具 {func.__name__} 缺少userid参数，跳过数据集访问检查")
            return await func(*args, **kwargs)
        
        # 检查单个数据集权限
        if dataset_id:
            if not permission_service.check_dataset_permission(userid, dataset_id):
                error_msg = f"🚫 用户 {userid} 无权限访问数据集: {dataset_id}"
                server_logger.error(error_msg)
                
                if ctx:
                    await ctx.error(f"权限不足：无法访问数据集 {dataset_id}")
                
                return f"❌ 权限不足：您没有访问数据集 '{dataset_id}' 的权限。"
        
        # 检查多个数据集权限并过滤
        if dataset_ids:
            # 如果dataset_ids是字符串，先分割
            if isinstance(dataset_ids, str):
                dataset_list = [id.strip() for id in dataset_ids.split(",") if id.strip()]
            else:
                dataset_list = dataset_ids
            
            # 过滤允许访问的数据集
            allowed_datasets = permission_service.filter_allowed_datasets(userid, dataset_list)
            
            if not allowed_datasets:
                error_msg = f"🚫 用户 {userid} 无权限访问任何指定的数据集"
                server_logger.error(error_msg)
                
                if ctx:
                    await ctx.error("权限不足：无法访问任何指定的数据集")
                
                return "❌ 权限不足：您没有访问任何指定数据集的权限。"
            
            # 更新参数为过滤后的数据集列表
            if isinstance(dataset_ids, str):
                kwargs['dataset_ids'] = ",".join(allowed_datasets)
            else:
                kwargs['dataset_ids'] = allowed_datasets
        
        return await func(*args, **kwargs)
    
    return wrapper


def validate_search_limit(func: Callable) -> Callable:
    """
    搜索限制验证装饰器
    
    确保用户的搜索限制不超过其权限允许的最大值
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        userid = kwargs.get('userid')
        limit = kwargs.get('limit')
        limit_per_dataset = kwargs.get('limit_per_dataset')
        ctx = kwargs.get('ctx')
        
        # 如果没有userid，跳过检查
        if userid is None:
            return await func(*args, **kwargs)
        
        # 验证搜索限制
        if limit is not None:
            validated_limit = permission_service.validate_search_limit(userid, limit)
            if validated_limit != limit:
                kwargs['limit'] = validated_limit
                if ctx:
                    await ctx.warning(f"搜索限制已调整为 {validated_limit}")
        
        # 验证每个数据集的搜索限制
        if limit_per_dataset is not None:
            validated_limit = permission_service.validate_search_limit(userid, limit_per_dataset)
            if validated_limit != limit_per_dataset:
                kwargs['limit_per_dataset'] = validated_limit
                if ctx:
                    await ctx.warning(f"每个数据集的搜索限制已调整为 {validated_limit}")
        
        return await func(*args, **kwargs)
    
    return wrapper


def validate_collection_access(func: Callable) -> Callable:
    """
    集合访问验证装饰器
    
    检查用户是否有权限查看集合内容
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        userid = kwargs.get('userid')
        ctx = kwargs.get('ctx')
        
        # 如果没有userid，跳过检查
        if userid is None:
            return await func(*args, **kwargs)
        
        # 检查是否允许查看集合
        if not permission_service.can_view_collections(userid):
            error_msg = f"🚫 用户 {userid} 无权限查看集合内容"
            server_logger.error(error_msg)
            
            if ctx:
                await ctx.error("权限不足：无法查看集合内容")
            
            return "❌ 权限不足：您没有查看集合内容的权限。"
        
        return await func(*args, **kwargs)
    
    return wrapper


def validate_folder_exploration(func: Callable) -> Callable:
    """
    文件夹探索验证装饰器
    
    检查用户是否有权限探索文件夹
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        userid = kwargs.get('userid')
        ctx = kwargs.get('ctx')
        
        # 如果没有userid，跳过检查
        if userid is None:
            return await func(*args, **kwargs)
        
        # 检查是否允许探索文件夹
        if not permission_service.can_explore_folders(userid):
            error_msg = f"🚫 用户 {userid} 无权限探索文件夹"
            server_logger.error(error_msg)
            
            if ctx:
                await ctx.error("权限不足：无法探索文件夹")
            
            return "❌ 权限不足：您没有探索文件夹的权限。"
        
        return await func(*args, **kwargs)
    
    return wrapper 