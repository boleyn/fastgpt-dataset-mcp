# 知识库管理MCP工具 - 架构说明

## 🏗️ 项目重构概述

为了更好地符合MCP项目最佳实践，我们对整个项目进行了重构，采用了分层架构设计，统一了API调用，并优化了代码组织结构。

## 📁 新的项目结构

```
dataset-mcp/
├── src/                          # 新的核心源代码目录
│   ├── __init__.py              # 包初始化
│   ├── config.py                # 统一配置管理
│   ├── models.py                # 数据模型定义
│   ├── api_client.py            # 统一API客户端
│   └── services/                # 业务服务层
│       ├── __init__.py
│       ├── tree_service.py      # 目录树服务
│       ├── search_service.py    # 搜索服务
│       └── collection_service.py # Collection服务
├── dataset/                     # 原有功能模块（保持兼容）
│   ├── enhanced_search.py       # 增强搜索功能
│   ├── planning.py              # 搜索计划生成
│   ├── answer_generation.py    # 答案生成
│   └── logger.py                # 日志模块
├── examples/                    # 示例代码
│   ├── collection_viewer_example.py
│   └── new_architecture_demo.py # 新架构演示
├── main.py                      # 原有主文件
├── main_new.py                  # 重构后主文件
└── README.md                    # 项目说明
```

## 🔧 架构设计原则

### 1. 分层架构 (Layered Architecture)

```
┌─────────────────────────────────┐
│         MCP Tool Layer          │  ← FastMCP工具接口层
├─────────────────────────────────┤
│        Service Layer            │  ← 业务逻辑服务层
├─────────────────────────────────┤
│       API Client Layer          │  ← 统一API客户端层
├─────────────────────────────────┤
│        Model Layer              │  ← 数据模型层
├─────────────────────────────────┤
│       Configuration Layer       │  ← 配置管理层
└─────────────────────────────────┘
```

### 2. 关注点分离 (Separation of Concerns)

- **配置管理** (`src/config.py`): 统一管理所有配置项
- **数据模型** (`src/models.py`): 定义所有数据结构
- **API客户端** (`src/api_client.py`): 封装所有HTTP请求
- **业务服务** (`src/services/`): 实现具体业务逻辑
- **MCP接口** (`main_new.py`): 提供工具接口

### 3. 依赖注入 (Dependency Injection)

- 服务层依赖统一的API客户端
- API客户端依赖配置管理
- 所有组件通过依赖注入进行组装

## 🆕 主要改进

### ✅ 统一的API客户端

**之前**: 每个模块都有自己的HTTP请求逻辑
```python
# 在search.py中
async with aiohttp.ClientSession() as session:
    async with session.post(url, headers=headers, json=payload) as response:
        # 处理响应...

# 在collection_viewer.py中
async with aiohttp.ClientSession() as session:
    async with session.post(url, headers=headers, json=payload) as response:
        # 重复的处理逻辑...
```

**现在**: 统一的API客户端处理所有请求
```python
# src/api_client.py
class APIClient:
    async def _make_request(self, method: str, endpoint: str, ...):
        # 统一的请求处理逻辑
    
    async def get_dataset_tree(self, ...):
        return await self._make_request("POST", "/api/core/dataset/tree", ...)
    
    async def search_dataset(self, ...):
        return await self._make_request("POST", "/api/core/dataset/searchTest", ...)
```

### ✅ 使用新的detail接口

**之前**: 使用read接口获取基本信息，文件名不准确
```python
# 旧接口返回: "name": "未知文档"
collection_info = await self.get_collection_info(collection_id)
```

**现在**: 使用detail接口获取详细信息，包括准确的文件名
```python
# 新接口返回: "name": "亚信国际2025产品手册V3.10402.pdf"
collection_detail = await self.api_client.get_collection_detail(collection_id)
```

### ✅ 配置集中管理

**之前**: 配置分散在各个模块中
```python
class SearchConfig:
    def __init__(self):
        self.base_url = os.getenv("KNOWLEDGE_BASE_URL", "http://...")

class CollectionConfig:
    def __init__(self):
        self.base_url = os.getenv("KNOWLEDGE_BASE_URL", "http://...")
```

**现在**: 统一的配置管理
```python
# src/config.py
class Config:
    def __init__(self):
        self.api_base_url = os.getenv("KNOWLEDGE_BASE_URL", "http://...")
        self.mcp_host = os.getenv('MCP_SERVER_HOST', '0.0.0.0')
        # 所有配置都在这里管理

config = Config()  # 全局配置实例
```

### ✅ 类型安全

使用Pydantic模型确保数据类型正确：
```python
class CollectionInfo(BaseModel):
    id: str = Field(alias="_id")
    name: str
    type: str
    raw_text_length: Optional[int] = Field(default=None, alias="rawTextLength")
```

## 🔄 向后兼容性

重构保持了与现有功能的完全兼容：

- 所有MCP工具接口保持不变
- 现有的高级功能（智能搜索、答案生成等）继续可用
- 原有的main.py文件仍然可以使用

## 🚀 使用新架构

### 启动重构后的服务器

```bash
# 使用新的主文件
python main_new.py --parent-id=your-parent-id

# 或使用环境变量
PARENT_ID=your-parent-id python main_new.py
```

### 直接使用服务层

```python
from src.services import TreeService, SearchService, CollectionService

# 创建服务实例
tree_service = TreeService()
search_service = SearchService()
collection_service = CollectionService()

# 使用服务
result = await collection_service.view_collection_content("collection_id", 50)
```

### 直接使用API客户端

```python
from src.api_client import api_client

# 获取collection详细信息
detail = await api_client.get_collection_detail("collection_id")
print(f"文件名: {detail.name}")
```

## 📊 性能优化

1. **连接复用**: 统一的API客户端减少了连接开销
2. **错误处理**: 统一的异常处理机制
3. **类型检查**: Pydantic模型提供运行时类型验证
4. **配置缓存**: 配置只在启动时加载一次

## 🎯 最佳实践符合度

- ✅ **单一职责原则**: 每个模块都有明确的职责
- ✅ **依赖倒置**: 高层模块不依赖低层模块
- ✅ **开闭原则**: 对扩展开放，对修改关闭
- ✅ **接口隔离**: 提供清晰的接口定义
- ✅ **配置外部化**: 配置与代码分离
- ✅ **错误处理**: 统一的异常处理策略

## 🔧 开发指南

### 添加新的API接口

1. 在 `src/api_client.py` 中添加新方法
2. 在 `src/models.py` 中定义数据模型
3. 在相应的服务类中添加业务逻辑
4. 在 `main_new.py` 中添加MCP工具接口

### 修改配置

在 `src/config.py` 中统一管理所有配置项，支持环境变量覆盖。

### 测试新功能

使用 `examples/new_architecture_demo.py` 测试新架构的各个组件。

## 📈 后续规划

1. **完全迁移**: 逐步将所有功能迁移到新架构
2. **性能监控**: 添加API调用监控和性能指标
3. **缓存机制**: 实现结果缓存以提高响应速度
4. **自动测试**: 为所有服务添加单元测试
5. **文档完善**: 补充API文档和使用示例 