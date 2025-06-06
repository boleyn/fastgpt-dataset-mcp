#!/usr/bin/env python3
"""
智能文档分析功能演示

展示新的智能文档分析工具的强大功能：
1. 搜索定位相关文档
2. 获取完整文档内容
3. 基于全文生成综合答案
"""

import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.document_analysis_service import DocumentAnalysisService
from src.config import config


async def demo_smart_analysis():
    """演示智能文档分析功能"""
    
    print("=" * 60)
    print("🧠 智能文档分析功能演示")
    print("=" * 60)
    
    # 创建文档分析服务
    analysis_service = DocumentAnalysisService()
    
    # 演示问题
    question = "亚信科技的主要产品有哪些？请详细介绍各产品的特点和应用场景。"
    
    # 演示数据集（请根据实际情况修改）
    dataset_ids = [
        "67489e8043c5b3000c23b4c6",  # 示例数据集ID
        # 添加更多数据集ID...
    ]
    
    print(f"📋 分析问题: {question}")
    print(f"🎯 目标数据集: {len(dataset_ids)} 个")
    print()
    
    # 开始智能分析
    print("🚀 开始智能文档分析...")
    print("1. 🔍 搜索定位相关文档...")
    print("2. 📄 获取文档完整内容...")
    print("3. 🎯 分析多个文档内容...")
    print("4. ✨ 生成综合性答案...")
    print()
    
    try:
        # 执行分析
        result = await analysis_service.analyze_documents_for_question(
            question=question,
            dataset_ids=dataset_ids,
            max_docs=3,  # 最多分析3个文档
            max_search_results=15  # 每个数据集最多搜索15个结果
        )
        
        # 显示结果
        print("✅ 分析完成！")
        print()
        print("📊 分析结果:")
        print("=" * 40)
        print(result)
        
        # 保存结果到文件
        output_file = "logs/smart_analysis_result.md"
        os.makedirs("logs", exist_ok=True)
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(f"# 智能文档分析结果\n\n")
            f.write(f"**问题**: {question}\n\n")
            f.write(f"**数据集数量**: {len(dataset_ids)}\n\n")
            f.write(f"**分析时间**: {asyncio.get_event_loop().time()}\n\n")
            f.write("---\n\n")
            f.write(result)
        
        print(f"💾 结果已保存到: {output_file}")
        
    except Exception as e:
        print(f"❌ 分析失败: {str(e)}")
        import traceback
        traceback.print_exc()


async def demo_workflow_comparison():
    """对比传统搜索和智能分析的工作流程"""
    
    print("\n" + "=" * 60)
    print("🔄 工作流程对比")
    print("=" * 60)
    
    print("📊 传统工作流程:")
    print("  1. get_dataset_tree - 查看可用数据集")
    print("  2. search_dataset - 搜索相关片段")
    print("  3. view_collection_content - 手动查看每个文档")
    print("  4. 人工整理和分析信息")
    print("  5. 手动生成答案")
    print()
    
    print("🧠 智能分析工作流程:")
    print("  1. smart_document_analysis - 一键完成:")
    print("     • 🔍 自动搜索多数据集")
    print("     • 📄 智能识别最相关文档")
    print("     • 📖 获取完整文档内容")
    print("     • 🎯 基于全文内容分析")
    print("     • ✨ 生成综合性答案")
    print()
    
    print("💡 优势对比:")
    print("  • 效率提升: 从5步手动操作 → 1步自动完成")
    print("  • 内容质量: 从片段信息 → 完整文档内容")
    print("  • 答案准确性: 从人工整理 → AI智能分析")
    print("  • 信息完整性: 自动汇总多文档信息")


if __name__ == "__main__":
    # 检查配置
    if not config.get_parent_id():
        print("❌ 错误: 请先配置 PARENT_ID 环境变量")
        sys.exit(1)
    
    # 运行演示
    asyncio.run(demo_smart_analysis())
    asyncio.run(demo_workflow_comparison())
    
    print("\n" + "=" * 60)
    print("🎉 演示完成！")
    print("=" * 60) 