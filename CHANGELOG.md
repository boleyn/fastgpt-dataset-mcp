# 更新日志

## [2025-06-06] 日志系统全面优化

### 🎯 主要改进

#### 📝 统一日志系统
- **新增** `dataset/logger.py` - 统一的日志管理模块
- **新增** 彩色格式化器，支持开发和生产环境切换
- **新增** 专用日志方法：搜索、API、性能监控等
- **新增** 模块化日志器，便于问题定位

#### 🔧 配置管理
- **新增** `config/logging.env` - 日志配置文件
- **新增** 环境变量支持 (`LOG_LEVEL`, `LOG_PLAIN`)
- **新增** 运行时日志级别调整功能

#### 📊 日志输出优化
- **替换** 所有 `print()` 语句为结构化日志
- **优化** 错误信息格式，更易于调试
- **添加** 时间戳、模块名、日志级别标识
- **支持** DEBUG、INFO、WARNING、ERROR、CRITICAL 五个级别

#### 🎨 视觉改进
- **彩色图标**: 🔍 DEBUG、📝 INFO、⚠️ WARNING、❌ ERROR、🚨 CRITICAL
- **ANSI颜色**: 开发环境下彩色输出
- **简洁格式**: 生产环境下的简单文本格式

### 📋 模块更新

#### 更新的文件
- `main.py` - 服务器启动日志优化
- `dataset/search.py` - 搜索相关日志
- `dataset/search_optimizer.py` - 搜索优化器日志  
- `dataset/tree.py` - 目录树操作日志
- `dataset/enhanced_search.py` - 增强搜索日志
- `dataset/planning.py` - 搜索计划日志
- `dataset/answer_generation.py` - 答案生成日志

#### 新增的文件
- `dataset/logger.py` - 核心日志管理模块
- `config/logging.env` - 日志配置文件
- `docs/logging-guide.md` - 详细使用指南

### 🎯 使用示例

#### 基本使用
```python
from dataset.logger import search_logger, tree_logger

# 信息日志
search_logger.info("搜索操作开始")

# 专用方法
search_logger.search_start("亚信数字化", "dataset_id")
search_logger.search_result("亚信数字化", 10, 1.5)
tree_logger.performance("获取目录树", 2.5)
```

#### 配置管理
```bash
# 环境变量方式
export LOG_LEVEL=DEBUG
export LOG_PLAIN=false

# 配置文件方式
echo "LOG_LEVEL=INFO" > config/logging.env

# 运行时配置
LOG_LEVEL=DEBUG python main.py
```

### 📈 改进效果

#### Before (优化前)
```
🔍 检测到多个搜索词: ['亚信', '数字化']
📝 将分别搜索每个词并合并结果（MongoDB不支持空格OR搜索）
  🔎 搜索关键词: '亚信' 在数据集 683e8f11d635908ed3368af2
📊 合并结果: 找到 5 个唯一结果
```

#### After (优化后)
```
🔍 [14:31:20] DEBUG   | Search               | 检测到多个搜索词: ['亚信', '数字化']
🔍 [14:31:20] DEBUG   | Search               | 将分别搜索每个词并合并结果（MongoDB不支持空格OR搜索）
🔍 [14:31:20] DEBUG   | Search               | 搜索关键词: '亚信' 在数据集 683e8f11d635908ed3368af2  
📝 [14:31:20] INFO    | Search               | 合并结果完成 | 找到 5 个唯一结果
```

### 🎁 附加功能

- **模块识别**: 每条日志都标明来源模块
- **时间戳**: 精确到秒的时间记录
- **级别控制**: 可根据需要调整详细程度
- **错误追踪**: 更详细的错误信息和堆栈跟踪
- **性能监控**: 内置性能日志方法

### 🔗 相关文档

- [日志系统使用指南](docs/logging-guide.md)
- [配置文件说明](config/logging.env)

---

通过这次优化，系统的日志输出更加专业、结构化，大大提升了开发和运维体验！🎉 