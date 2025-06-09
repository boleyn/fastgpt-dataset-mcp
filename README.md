# 🧠 知识库管理MCP工具 v2.0

基于FastMCP构建的知识库管理工具，支持目录树查看、内容搜索和文档查看功能。

## ✨ 功能亮点

### 🔍 优化的搜索结果格式 (新增)
**搜索结果包含完整的文档信息**
- 📁 **文件名**: 显示准确的文档文件名
- 🔗 **Collection ID**: 提供文档的唯一标识符
- ⬇️ **文件下载**: 提供Markdown格式的文件下载链接
- 📋 **文档详情**: 包含文档类型、大小等详细信息

### 🔗 SSE URL参数支持
**支持通过URL参数动态设置parentId**
- 🌐 支持SSE协议URL参数传递parentId
- 🎯 工具调用时自动检查URL参数
- ✅ 简单易用，无需复杂配置

### 🏗️ 全新架构设计
- 📁 统一API客户端封装所有接口调用
- 🔧 分层架构设计（配置、模型、服务、工具层）
- 🎯 新的detail接口获取准确文件名
- 🛡️ 类型安全的Pydantic模型
- 📊 统一的日志系统

## 🚀 快速开始

### 启动MCP SSE服务器
```bash
# 基本启动（使用默认配置）
python main.py

# 使用环境变量设置parentId
DEFAULT_PARENT_ID=683462ea7420db05db65b810 python main.py

# 自定义端口和主机
MCP_SERVER_HOST=127.0.0.1 MCP_SERVER_PORT=9000 python main.py
```

### MCP客户端配置
```json
{
  "mcpServers": {
    "knowledge-base": {
      "type": "sse",
      "url": "http://localhost:18007/sse?parentId=683462ea7420db05db65b810"
    }
  }
}
```

**重要说明**: 
- 服务器默认在端口18007提供SSE服务
- **parentId可通过URL参数传递**：`?parentId=你的ID`
- 工具调用时会自动检查并应用URL参数中的parentId
- 支持通过环境变量 `MCP_SERVER_HOST` 和 `MCP_SERVER_PORT` 配置服务器地址

## 🛠️ 可用工具

### 🔧 set_parent_id
**设置会话级别的parentId**

动态设置当前会话使用的父级目录ID

**参数:**
- `parent_id` (必需): 要设置的父级目录ID

### 📁 get_dataset_tree
**获取知识库目录树**

浏览知识库结构，查看可用数据集

**参数:**
- `search_value` (可选): 过滤关键词，支持多关键词空格分隔
- `deep` (可选): 目录深度，默认4

### 🔍 search_dataset
**单数据集精确搜索**

在指定数据集中搜索相关内容片段，返回包含完整文档信息的结果

**参数:**
- `dataset_id` (必需): 数据集ID
- `text` (必需): 搜索关键词
- `limit` (可选): 结果数量，默认10

**返回格式特点:**
- 📁 **文件名**: 准确的文档文件名
- 🔗 **Collection ID**: 文档唯一标识符
- ⬇️ **文件下载**: Markdown格式的下载链接
- 📋 **详细信息**: 文档类型、大小等

### 📄 view_collection_content
**查看文档完整内容**

获取搜索到的文档的完整内容

**参数:**
- `collection_id` (必需): 文档ID（从搜索结果中获取）
- `page_size` (可选): 每页数据块数量，默认50

### 🔍 multi_dataset_search
**多数据集快速搜索**

在多个数据集中同时搜索，返回包含完整文档信息的汇总结果

**参数:**
- `dataset_ids` (必需): 数据集ID列表
- `query` (必需): 搜索关键词
- `limit_per_dataset` (可选): 每个数据集的结果限制，默认5

## 🔧 环境变量配置

复制配置文件：
```bash
cp config.env.example .env
```

主要配置项：
- `DEFAULT_PARENT_ID`: 默认父级目录ID
- `KNOWLEDGE_BASE_URL`: API基础URL，默认http://10.21.8.6:13000
- `KNOWLEDGE_BASE_TOKEN`: 认证token
- `MCP_SERVER_HOST`: 服务器主机，默认0.0.0.0
- `MCP_SERVER_PORT`: 服务器端口，默认18007

## 🔗 SSE URL参数功能详解

### 使用方法

#### 客户端连接
```
http://localhost:18007/sse?parentId=683462ea7420db05db65b810
```

#### 动态设置parentId
```bash
# 使用set_parent_id工具
{
  "parent_id": "683462ea7420db05db65b810"
}
```

#### 日志输出示例
```
🔗 从SSE URL提取并存储parentId: 683462ea...
🔑 设置会话parentId: 683462ea...
```

## 🎯 搜索结果格式优化

### 新的搜索结果格式

每个搜索结果现在包含：

```markdown
## 结果 1

**内容:**
搜索到的文档内容片段...

**相关性评分:**
- embedding: 0.8542
- rerank: 0.7234

**Token数量:** 156

### 📄 来源信息

**📁 文件名:** 产品介绍文档.pdf
**🔗 Collection ID:** `67890abcdef123456789`
**⬇️ 文件下载:** [产品介绍文档.pdf](http://example.com/download/file.pdf)

**📋 文档类型:** pdf
**📏 文档大小:** 15,234 字符
**🗂️ 数据集ID:** `dataset123456`
```

### 优化特点

1. **突出显示**: 使用emoji图标突出重要信息
2. **Markdown链接**: 文件下载使用标准Markdown语法
3. **完整信息**: 包含所有必要的文档元数据
4. **统一格式**: 所有搜索工具使用相同的格式标准

## 🚀 项目架构

### 新架构特点

- ✅ **统一API客户端**: 所有HTTP请求都通过统一的客户端处理
- ✅ **分层架构**: 配置、模型、服务层清晰分离
- ✅ **优化格式化**: 统一的FormatUtils提供标准化输出格式
- ✅ **类型安全**: 使用Pydantic模型确保数据类型正确
- ✅ **配置集中管理**: 所有配置项统一管理
- ✅ **会话管理**: 支持会话级别的parentId存储

## 📖 使用示例

```bash
# 基本启动
python main.py

# 自定义端口启动
MCP_SERVER_PORT=9000 python main.py

# 使用环境变量设置默认parentId
DEFAULT_PARENT_ID=你的ID python main.py
```

## 🎯 Claude Desktop 配置示例

```json
{
  "mcpServers": {
    "knowledge-base": {
      "type": "sse", 
      "url": "http://localhost:18007/sse?parentId=683462ea7420db05db65b810"
    }
  }
}
```

## 🐛 故障排除

### SSE URL参数不生效
**问题**: 通过`?parentId=xxx`传递的参数不生效

**解决方案**: 
1. 确保URL格式正确：`http://localhost:18007/sse?parentId=你的ID`
2. 调用任何工具时会自动检查URL参数
3. 或使用`set_parent_id`工具动态设置
4. 查看服务器日志确认参数是否被正确解析

**日志示例**:
```
🔗 从SSE URL提取并存储parentId: 683462ea...
🔑 使用会话存储的parentId: 683462ea...
```

### 搜索结果格式问题
**问题**: 搜索结果缺少文件下载链接或collectionId

**解决方案**:
1. 确保使用最新版本的工具
2. 所有搜索工具现在都包含完整的文档信息
3. 如果下载链接显示"暂无下载链接"，说明该文档不支持下载

## 📝 更新日志

### v2.0 主要更新
- ✅ 优化搜索结果格式，突出显示collectionId、文件名和下载链接
- ✅ 移除暂时不可用的智能分析功能
- ✅ 清理无用的代码和依赖
- ✅ 更新文档和使用说明
- ✅ 统一格式化工具，确保所有搜索结果格式一致
