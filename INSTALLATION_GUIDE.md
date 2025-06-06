# 📦 智能知识库MCP系统 - 安装与部署指南

## 🚀 快速安装

### 方式一：使用uv (推荐)

```bash
# 1. 确保已安装uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. 克隆项目
git clone <your-repo-url>
cd dataset-mcp

# 3. 安装依赖
uv sync

# 4. 启动服务器
python main.py
```

### 方式二：使用pip

```bash
# 1. 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\activate     # Windows

# 2. 安装依赖
pip install -r requirements.txt
# 或者手动安装主要依赖
pip install aiohttp fastmcp pydantic python-dotenv uvicorn jieba

# 3. 启动服务器
python main.py
```

## 📋 系统要求

- **Python版本**: >= 3.12
- **操作系统**: Linux, macOS, Windows
- **内存**: 最少512MB，推荐1GB+
- **网络**: 需要访问知识库API服务器

## 🔧 依赖包说明

| 包名 | 版本要求 | 用途 |
|------|---------|------|
| `aiohttp` | >=3.12.9 | 异步HTTP客户端 |
| `fastmcp` | >=2.6.1 | MCP服务器框架 |
| `pydantic` | >=2.11.5 | 数据验证和序列化 |
| `python-dotenv` | >=1.0.0 | 环境变量管理 |
| `uvicorn` | >=0.27.0 | ASGI服务器 |
| `jieba` | >=0.42.1 | 中文分词处理 |

## ⚙️ 配置设置

### 环境变量配置

创建 `.env` 文件：

```env
# 知识库API配置
KNOWLEDGE_BASE_URL=http://10.21.8.6:13000
KNOWLEDGE_BASE_TOKEN=your-token-here

# 默认数据集配置
DEFAULT_PARENT_ID=683462ea7420db05db65b810

# 服务器配置
MCP_SERVER_HOST=0.0.0.0
MCP_SERVER_PORT=8000
```

### 命令行参数

```bash
# 指定父级数据集ID
python main.py --parent-id your-dataset-id

# 自定义服务器配置
MCP_SERVER_HOST=127.0.0.1 MCP_SERVER_PORT=9000 python main.py
```

## 🚀 启动服务器

### 基本启动

```bash
python main.py
```

### 自定义配置启动

```bash
# 指定数据集ID和端口
python main.py --parent-id 683e8f11d635908ed3368af2
```

### 启动成功标志

看到以下输出表示启动成功：

```
🚀 启动知识库管理MCP服务器...
📁 当前工作目录: /path/to/dataset-mcp
🔧 配置的父级目录ID: 683462ea7420db05db65b810

📋 已注册的MCP工具:
  1. get_dataset_tree - 获取知识库目录树
  2. search_dataset - 基础知识库搜索
  3. intelligent_search_and_answer - 🚀 智能搜索和问答系统
  4. generate_search_plan - 生成搜索计划
  5. multi_dataset_search - 多数据集搜索

🌐 启动SSE服务器: http://0.0.0.0:8000
📋 SSE端点: http://0.0.0.0:8000/sse
```

## 🔍 MCP客户端配置

### Claude Desktop配置

在 `claude_desktop_config.json` 中添加：

```json
{
  "mcpServers": {
    "dataset-mcp": {
      "command": "python",
      "args": ["/path/to/dataset-mcp/main.py"],
      "env": {
        "PARENT_ID": "your-dataset-id"
      }
    }
  }
}
```

### 其他MCP客户端

连接到SSE端点：
```
http://localhost:8000/sse?parentId=your-dataset-id
```

## 🚨 常见问题排除

### 1. ModuleNotFoundError: No module named 'jieba'

**问题**: jieba中文分词库未安装

**解决方案**:
```bash
# 使用uv安装
uv add jieba

# 或使用pip安装
pip install jieba>=0.42.1
```

**验证安装**:
```bash
python -c "import jieba; print('jieba版本:', jieba.__version__)"
```

### 2. 端口占用错误

**问题**: `Address already in use`

**解决方案**:
```bash
# 查找占用进程
lsof -i :8000

# 杀死进程
kill -9 <PID>

# 或使用不同端口
MCP_SERVER_PORT=9000 python main.py
```

### 3. 知识库连接失败

**问题**: 无法连接到知识库API

**排查步骤**:
1. 检查网络连接
2. 验证API地址和token
3. 查看防火墙设置

**测试连接**:
```bash
curl -H "Authorization: Bearer your-token" http://10.21.8.6:13000/api/core/dataset/list
```

### 4. Python版本不兼容

**问题**: `requires-python = ">=3.12"`

**解决方案**:
```bash
# 检查Python版本
python --version

# 使用pyenv安装新版本Python
pyenv install 3.12.0
pyenv global 3.12.0
```

### 5. 依赖冲突

**问题**: 包版本冲突

**解决方案**:
```bash
# 清理环境
rm -rf .venv
rm uv.lock

# 重新安装
uv sync
```

## 🔧 开发模式

### 安装开发依赖

```bash
uv sync --dev
```

### 代码格式化

```bash
black dataset/ main.py
ruff check dataset/ main.py
```

### 运行测试

```bash
pytest tests/
```

## 📊 性能优化

### 内存优化

```bash
# 设置jieba词典缓存路径
export JIEBA_CACHE_DIR=/tmp/jieba_cache
```

### 并发调优

在代码中调整并发参数：
```python
# enhanced_search.py
concurrent_limit = 3  # 降低并发数
timeout_seconds = 60  # 增加超时时间
```

## 🛡️ 安全配置

### API Token安全

```bash
# 使用环境变量而非硬编码
export KNOWLEDGE_BASE_TOKEN="your-secure-token"
```

### 网络访问控制

```bash
# 仅本地访问
MCP_SERVER_HOST=127.0.0.1 python main.py

# 指定允许的IP
# 在防火墙中配置访问控制
```

## 📝 日志配置

### 启用详细日志

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 日志文件

```bash
python main.py > mcp_server.log 2>&1 &
```

## 🔄 自动化部署

### Systemd服务 (Linux)

创建 `/etc/systemd/system/dataset-mcp.service`:

```ini
[Unit]
Description=Dataset MCP Server
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/dataset-mcp
Environment=PATH=/path/to/.venv/bin
ExecStart=/path/to/.venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务:
```bash
sudo systemctl enable dataset-mcp
sudo systemctl start dataset-mcp
sudo systemctl status dataset-mcp
```

### Docker部署

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY . .

RUN pip install uv && uv sync

EXPOSE 8000
CMD ["python", "main.py"]
```

构建和运行:
```bash
docker build -t dataset-mcp .
docker run -p 8000:8000 dataset-mcp
```

## 📞 获取帮助

### 检查系统状态

```bash
# 检查服务器状态
curl http://localhost:8000/sse

# 检查依赖安装
python -c "from dataset import planning, enhanced_search, answer_generation; print('✅ 所有模块导入成功')"
```

### 联系支持

如果遇到无法解决的问题：

1. 检查 GitHub Issues
2. 提交详细的错误报告
3. 包含系统信息、错误日志和复现步骤

---

**🎉 安装完成后，您就可以开始使用强大的智能知识库MCP系统了！** 