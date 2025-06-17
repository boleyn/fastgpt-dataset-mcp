"""
统一日志配置模块
"""

import logging
import sys
from pathlib import Path

# 创建logs目录
logs_dir = Path("logs")
logs_dir.mkdir(exist_ok=True)

# 配置日志格式
log_format = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """获取配置好的日志器"""
    logger = logging.getLogger(name)
    
    if not logger.handlers:  # 避免重复添加handler
        logger.setLevel(level)
        
        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(log_format)
        logger.addHandler(console_handler)
        
        # 文件处理器
        file_handler = logging.FileHandler(logs_dir / f"{name}.log", encoding='utf-8')
        file_handler.setFormatter(log_format)
        logger.addHandler(file_handler)
    
    return logger

# 预定义的日志器
search_logger = get_logger("search")
server_logger = get_logger("server", level=logging.DEBUG)  # 设置为DEBUG级别以显示详细信息
api_logger = get_logger("api")
collection_logger = get_logger("collection")
tree_logger = get_logger("tree")
analysis_logger = get_logger("analysis") 