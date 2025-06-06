# 🧠 智能知识库管理MCP工具 v2.0

基于FastMCP构建的新一代智能知识库管理工具，支持目录树查看、内容搜索和**智能文档分析**功能。

## ✨ 新功能亮点

### 🧠 智能文档分析 (推荐)
**一键完成：搜索 → 全文 → 答案**
- 🔍 自动搜索多数据集定位相关文档
- 📄 获取文档完整内容（非片段）
- 🎯 基于全文内容智能分析
- ✨ 生成综合性答案

### 🏗️ 全新架构设计
- 📁 统一API客户端封装所有接口调用
- 🔧 分层架构设计（配置、模型、服务、工具层）
- 🎯 新的detail接口获取准确文件名
- 🛡️ 类型安全的Pydantic模型
- 📊 统一的日志系统

## 🚀 快速开始

### 启动MCP SSE服务器
```bash
# 指定parentId并启动服务器
python main.py --parent-id=1567e6250b82f952efaba4ebba47e229

# 或使用环境变量
PARENT_ID=1567e6250b82f952efaba4ebba47e229 python main.py

# 自定义端口和主机
MCP_SERVER_HOST=127.0.0.1 MCP_SERVER_PORT=9000 python main.py --parent-id=你的ID
```

### MCP客户端配置
```json
{
  "mcpServers": {
    "knowledge-base": {
      "type": "sse",
      "url": "http://localhost:8000/sse?parentId=1567e6250b82f952efaba4ebba47e229"
    }
  }
}
```

**注意**: 
- 服务器使用SSE协议，在 `/sse` 端点提供服务
- parentId通过URL参数传递
- 支持通过环境变量 `MCP_SERVER_HOST` 和 `MCP_SERVER_PORT` 配置服务器地址

## 🛠️ 可用工具

### 🧠 smart_document_analysis ⭐ **推荐**
**智能文档分析 - 一键完成全流程**

实现完整的智能文档分析工作流：搜索定位 → 获取全文 → 生成答案

**参数:**
- `question` (必需): 要分析的问题
- `dataset_ids` (必需): 要搜索的数据集ID列表
- `max_docs` (可选): 最大分析文档数量，默认5
- `max_search_results` (可选): 每个数据集的最大搜索结果数，默认20

**示例:**
```json
{
  "question": "**科技的主要产品有哪些？",
  "dataset_ids": ["数据集ID1", "数据集ID2"],
  "max_docs": 5,
  "max_search_results": 20
}
```

### 📁 get_dataset_tree
**获取知识库目录树**

浏览知识库结构，查看可用数据集

**参数:**
- `search_value` (可选): 过滤关键词
- `deep` (可选): 目录深度，默认4

### 🔍 search_dataset
**单数据集精确搜索**

在指定数据集中搜索相关内容片段

**参数:**
- `dataset_id` (必需): 数据集ID
- `text` (必需): 搜索关键词
- `limit` (可选): 结果数量，默认10

### 📄 view_collection_content
**查看文档完整内容**

获取搜索到的文档的完整内容

**参数:**
- `collection_id` (必需): 文档ID
- `page_size` (可选): 每页数据块数量，默认50

### 🔍 multi_dataset_search
**多数据集快速搜索**

在多个数据集中同时搜索

**参数:**
- `dataset_ids` (必需): 数据集ID列表
- `query` (必需): 搜索关键词
- `limit_per_dataset` (可选): 每个数据集的结果限制，默认5

### 🤖 intelligent_search_and_answer
**传统智能搜索问答**

基于关键词的传统智能问答（推荐使用smart_document_analysis）

### 📋 generate_search_plan
**生成搜索计划**

分析问题并生成搜索策略

## 🔧 环境变量配置

复制配置文件：
```bash
cp config.env.example .env
```

主要配置项：
- `PARENT_ID`: 父级目录ID
- `KNOWLEDGE_BASE_URL`: API基础URL，默认http://10.21.8.6:13000
- `KNOWLEDGE_BASE_TOKEN`: 认证token
- `MCP_SERVER_HOST`: 服务器主机，默认0.0.0.0
- `MCP_SERVER_PORT`: 服务器端口，默认8000

## 🚀 项目重构

### 新架构特点

- ✅ **统一API客户端**: 所有HTTP请求都通过统一的客户端处理
- ✅ **分层架构**: 配置、模型、服务层清晰分离
- ✅ **新detail接口**: 使用新的collection detail接口获取准确文件名
- ✅ **类型安全**: 使用Pydantic模型确保数据类型正确
- ✅ **配置集中管理**: 所有配置项统一管理
- ✅ **向后兼容**: 保持与现有功能的完全兼容

### 使用重构后的版本

```bash
# 启动重构后的MCP服务器
python main_new.py --parent-id=your-parent-id

# 查看架构演示
python examples/new_architecture_demo.py
```

详细架构说明请参考 [ARCHITECTURE.md](ARCHITECTURE.md)

## 📖 使用示例

```bash
# 基本启动
python main.py --parent-id=你的ID

# 自定义端口启动
MCP_SERVER_PORT=9000 python main.py --parent-id=你的ID

# 使用环境变量
PARENT_ID=你的ID MCP_SERVER_HOST=127.0.0.1 python main.py
```

## 🎯 Claude Desktop 配置示例

```json
{
  "mcpServers": {
    "knowledge-base": {
      "type": "sse", 
      "url": "http://localhost:8000/sse?parentId=1567e6250b82f952efaba4ebba47e229"
    }
  }
}
```
