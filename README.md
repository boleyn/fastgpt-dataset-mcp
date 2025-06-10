# 知识库管理MCP服务器 v2.0

一个专为 **FastGPT** 设计的知识库管理工具，基于 FastMCP 构建，提供智能的知识库搜索和管理功能。支持自适应查找知识，帮助 AI 助手更好地理解和检索相关信息。

## 🌟 核心特性

### 🎯 自适应知识查找
- **智能关键词扩展**: 自动将核心词扩展为同义词、相关词、上下文词
- **多层级搜索策略**: 从精确匹配到模糊搜索的渐进式查找
- **跨数据集并行搜索**: 同时在多个知识库中查找相关信息
- **深度文件夹探索**: 自动发现深层目录中的知识库资源

### 🔧 丰富的工具集
- **目录树浏览**: 快速了解知识库结构和可用数据集
- **精确搜索**: 在指定数据集中进行高精度内容检索
- **批量搜索**: 跨多个数据集的并行搜索和结果汇总
- **完整内容查看**: 获取文档的完整内容和详细信息
- **文件夹深度探索**: 发现和访问嵌套文件夹中的资源

## 🚀 快速开始

### 1. 安装依赖

本项目使用 `uv` 进行依赖管理：

```bash
# 安装 uv（如果尚未安装）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 安装项目依赖
uv sync
```

### 2. 配置环境

复制配置文件并根据需要修改：

```bash
cp config.env.example .env
```

在 `.env` 文件中配置您的设置：

```bash
# 知识库配置
DEFAULT_PARENT_ID=your-parent-id

# API配置
API_BASE_URL=http://your-api-domain.com
API_TOKEN=your-api-token

# MCP服务器配置
MCP_SERVER_HOST=0.0.0.0
MCP_SERVER_PORT=18007
```

### 3. 启动服务器

```bash
# 使用 uv 运行
uv run python main.py

# 或者激活虚拟环境后运行
source .venv/bin/activate  # Linux/Mac
# 或 .venv\Scripts\activate  # Windows
python main.py
```

服务器将在配置的端口启动（默认 `http://0.0.0.0:18007`），SSE端点为 `http://0.0.0.0:18007/sse`

## 🔗 FastGPT 集成配置

### MCP 客户端配置

在 FastGPT 的 MCP 配置中添加以下设置：

```json
{
  "name": "知识库管理工具",
  "url": "http://0.0.0.0:18007/sse?parentId=YOUR_PARENT_ID",
  "description": "智能知识库搜索和管理工具"
}
```

### 🔑 ParentId 配置说明

`parentId` 是知识库访问的关键标识符，有两种配置方式：

#### 方式1: URL参数配置（推荐）
在 MCP 配置的 URL 中直接指定：
```
http://0.0.0.0:18007/sse?parentId=your-specific-parent-id
```

#### 方式2: 默认配置
在 `.env` 文件中设置默认值：
```bash
DEFAULT_PARENT_ID=your-default-parent-id
```

**智能切换机制**:
- 系统会自动检测 URL 中的 `parentId` 参数变化
- 支持会话级别的 `parentId` 存储和管理
- 当 URL 参数变化时，自动更新当前会话的知识库访问权限

## 🛠️ 可用工具

### 1. 📁 get_dataset_tree
获取知识库目录树，浏览所有可用的数据集和文件夹。

```python
# 基础用法
get_dataset_tree()

# 带过滤的用法
get_dataset_tree(search_value="网络管理 系统", deep=6)
```

### 2. 🔍 search_dataset
在指定数据集中进行精确搜索。

```python
search_dataset(
    dataset_id="dataset-123",
    text="用户权限管理",
    limit=10
)
```

### 3. 🔍 multi_dataset_search
跨多个数据集的并行搜索。

```python
multi_dataset_search(
    dataset_ids=["dataset-1", "dataset-2", "dataset-3"],
    query="系统配置",
    limit_per_dataset=5
)
```

### 4. 📄 view_collection_content
查看文档的完整内容。

```python
view_collection_content(
    collection_id="collection-456",
    page_size=50
)
```

### 5. 🎯 expand_search_keywords
智能关键词扩展，提升搜索效果。

```python
expand_search_keywords(
    original_query="用户管理",
    expansion_type="comprehensive"
)
```

### 6. 📂 explore_folder_contents
深入探索文件夹内容，发现嵌套资源。

```python
explore_folder_contents(
    folder_id="folder-789",
    search_value="配置文档",
    deep=8
)
```

## 🧠 智能搜索策略

### 自适应查找流程

1. **关键词扩展**: 使用 `expand_search_keywords` 生成相关词汇
2. **目录探索**: 通过 `get_dataset_tree` 发现相关数据集
3. **精确搜索**: 使用 `search_dataset` 在目标数据集中搜索
4. **批量搜索**: 通过 `multi_dataset_search` 扩大搜索范围
5. **深度查看**: 使用 `view_collection_content` 获取完整信息

### 最佳实践

```python
# 1. 首先扩展关键词
expanded = expand_search_keywords("用户权限", "comprehensive")

# 2. 探索相关数据集
tree = get_dataset_tree("用户 权限 管理", deep=5)

# 3. 多数据集并行搜索
results = multi_dataset_search(
    dataset_ids=["found-dataset-1", "found-dataset-2"],
    query="用户权限管理配置",
    limit_per_dataset=8
)

# 4. 查看详细内容
content = view_collection_content("relevant-collection-id")
```

## 📊 功能特点

### 🎯 智能化
- 自动关键词扩展和语义理解
- 渐进式搜索策略，从精确到模糊
- 智能结果排序和相关性评分

### ⚡ 高性能
- 并行搜索多个数据集
- 异步处理提升响应速度
- 智能缓存和会话管理

### 🔧 易用性
- 统一的API接口设计
- 详细的错误提示和日志
- 灵活的参数配置

### 🛡️ 可靠性
- 完善的异常处理机制
- 会话级别的状态管理
- 自动重试和容错处理

## 📝 日志和调试

服务器提供详细的日志信息，包括：
- 🔑 ParentId 使用和切换记录
- 🔍 搜索请求和结果统计
- ⚡ 性能监控和错误追踪
- 📊 工具使用情况分析

## 🤝 与 FastGPT 的协同

这个工具专为 FastGPT 设计，提供：

1. **智能知识检索**: 帮助 AI 快速找到相关信息
2. **上下文理解**: 通过关键词扩展提升理解能力
3. **多源信息整合**: 跨数据集搜索提供全面视角
4. **动态知识库切换**: 通过 parentId 灵活访问不同知识库

## 🔧 技术架构

- **框架**: FastMCP (基于 FastAPI)
- **传输协议**: Server-Sent Events (SSE)
- **异步处理**: asyncio 并发处理
- **会话管理**: 基于客户端ID的状态存储
- **API集成**: RESTful API 客户端

## 📞 支持和反馈

如有问题或建议，请通过以下方式联系：
- 查看日志文件获取详细错误信息
- 检查 `.env` 配置文件是否正确
- 确认 API 连接和 parentId 设置
- 使用 `uv run python main.py` 启动服务器

---

**让 AI 更智能地管理和检索知识！** 🚀
