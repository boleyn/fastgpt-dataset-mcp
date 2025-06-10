"""
关键词扩展服务

提供智能关键词扩展功能，支持多种扩展策略。
用于实现prompt要求的"核心词 → 同义词 → 相关词 → 上下文词"扩展策略。
"""

from typing import Dict, List
from ..logger import server_logger


class KeywordService:
    """关键词扩展服务类"""
    
    def __init__(self):
        """初始化关键词扩展服务"""
        # 财务税务相关扩展词典
        self.finance_synonyms = {
            "财务": ["会计", "核算", "账务", "资金", "经费"],
            "税务": ["税收", "纳税", "税法", "税政", "征税"],
            "制度": ["规定", "办法", "规范", "标准", "流程"],
            "政策": ["法规", "条例", "规章", "通知", "文件"],
            "流程": ["程序", "步骤", "操作", "处理", "执行"],
            "管理": ["监管", "控制", "治理", "运营", "维护"],
            "报告": ["报表", "汇报", "总结", "分析", "统计"],
            "审计": ["检查", "核查", "稽核", "监察", "评估"]
        }
        
        # 技术相关扩展词典
        self.tech_synonyms = {
            "系统": ["平台", "软件", "应用", "工具", "程序"],
            "网络": ["通信", "连接", "传输", "协议", "架构"],
            "安全": ["防护", "保护", "加密", "认证", "权限"],
            "数据": ["信息", "资料", "记录", "档案", "文档"],
            "标准": ["规范", "准则", "要求", "指标", "基准"],
            "技术": ["工艺", "方法", "手段", "技能", "专业"]
        }
        
        # 业务场景相关词典
        self.business_contexts = {
            "财务": ["预算", "成本", "收入", "支出", "利润", "资产"],
            "税务": ["发票", "申报", "缴纳", "减免", "优惠", "合规"],
            "制度": ["执行", "监督", "考核", "培训", "宣贯", "更新"],
            "系统": ["部署", "配置", "维护", "升级", "监控", "备份"],
            "网络": ["带宽", "延迟", "稳定", "故障", "优化", "扩容"]
        }
        
        # 业务领域识别词典 - 用于智能识别查询内容的业务领域
        self.domain_keywords = {
            "差旅出行": {
                "触发词": ["出差", "差旅", "酒店", "机票", "火车", "高铁", "住宿", "交通", "路费", "餐费"],
                "扩展词": ["财务", "行政", "报销", "费用", "标准", "审批", "发票", "凭证", "预算", "成本控制"],
                "优先级": ["财务", "行政", "报销", "费用"]  # 高优先级关键词
            },
            "财务管理": {
                "触发词": ["财务", "会计", "成本", "预算", "报销", "发票", "税务", "审计"],
                "扩展词": ["制度", "流程", "审批", "核算", "监管", "合规", "风险", "内控"],
                "优先级": ["制度", "流程", "审批", "合规"]
            },
            "人力资源": {
                "触发词": ["员工", "人事", "薪资", "绩效", "培训", "招聘", "考勤", "假期"],
                "扩展词": ["制度", "政策", "流程", "管理", "评估", "发展", "福利", "保险"],
                "优先级": ["制度", "政策", "流程", "管理"]
            },
            "行政管理": {
                "触发词": ["行政", "办公", "采购", "合同", "资产", "设备", "会议", "文档"],
                "扩展词": ["制度", "流程", "审批", "管理", "维护", "标准", "规范", "监督"],
                "优先级": ["制度", "流程", "审批", "管理"]
            },
            "技术运维": {
                "触发词": ["系统", "网络", "服务器", "数据库", "监控", "运维", "故障", "性能"],
                "扩展词": ["技术", "标准", "规范", "流程", "安全", "备份", "升级", "优化"],
                "优先级": ["技术", "标准", "规范", "流程"]
            },
            "项目管理": {
                "触发词": ["项目", "计划", "进度", "里程碑", "交付", "质量", "风险", "团队"],
                "扩展词": ["管理", "流程", "标准", "评估", "监控", "协调", "沟通", "文档"],
                "优先级": ["管理", "流程", "标准", "评估"]
            }
        }
        
        # 亚信数字业务特色上下文词
        self.asiainfo_contexts = [
            "亚信数字", "公司", "员工", "部门", "项目", "客户",
            "合规", "风险", "内控", "审批", "流程", "标准",
            "IPOSS", "网络管理", "运维", "监控", "告警", "性能"
        ]
        
        # 合并所有同义词词典
        self.all_synonyms = {**self.finance_synonyms, **self.tech_synonyms}
    
    def _identify_business_domains(self, query: str) -> List[str]:
        """
        智能识别查询内容的业务领域
        
        Args:
            query: 查询内容
            
        Returns:
            匹配的业务领域列表
        """
        query_lower = query.lower()
        matched_domains = []
        
        for domain, keywords in self.domain_keywords.items():
            trigger_words = keywords["触发词"]
            
            # 检查是否包含触发词
            for trigger in trigger_words:
                if trigger in query_lower:
                    matched_domains.append(domain)
                    server_logger.info(f"识别到业务领域: {domain} (触发词: {trigger})")
                    break
        
        return matched_domains
    
    async def expand_keywords(self, original_query: str, expansion_type: str = "comprehensive") -> Dict[str, List[str]]:
        """
        扩展关键词
        
        Args:
            original_query: 原始搜索关键词
            expansion_type: 扩展类型 (basic/comprehensive/contextual)
            
        Returns:
            包含核心词、同义词、相关词、上下文词的字典
        """
        if not original_query.strip():
            raise ValueError("请提供原始搜索关键词")
        
        server_logger.info(f"开始关键词扩展 | 原词: '{original_query}' | 类型: {expansion_type}")
        
        # 智能识别业务领域
        matched_domains = self._identify_business_domains(original_query)
        
        # 基础关键词处理
        core_words = [word.strip() for word in original_query.split() if word.strip()]
        
        expanded_keywords = {
            "核心词": core_words,
            "同义词": [],
            "相关词": [],
            "上下文词": [],
            "业务领域": matched_domains
        }
        
        # 生成同义词
        for word in core_words:
            if word in self.all_synonyms:
                expanded_keywords["同义词"].extend(self.all_synonyms[word])
        
        # 基于识别的业务领域生成扩展词（优先级排序）
        for domain in matched_domains:
            if domain in self.domain_keywords:
                domain_data = self.domain_keywords[domain]
                domain_expansions = domain_data["扩展词"]
                priority_words = domain_data.get("优先级", [])
                
                # 优先级词汇排在前面
                sorted_expansions = []
                for word in priority_words:
                    if word in domain_expansions:
                        sorted_expansions.append(word)
                
                # 添加其他非优先级词汇
                for word in domain_expansions:
                    if word not in priority_words:
                        sorted_expansions.append(word)
                
                expanded_keywords["相关词"].extend(sorted_expansions)
                server_logger.info(f"基于业务领域 '{domain}' 扩展了 {len(sorted_expansions)} 个相关词 (优先级: {len(priority_words)}个)")
        
        # 生成相关词（基于业务场景）
        for word in core_words:
            if word in self.business_contexts:
                expanded_keywords["相关词"].extend(self.business_contexts[word])
        
        # 生成上下文词（基于亚信数字业务特点）
        if expansion_type in ["comprehensive", "contextual"]:
            expanded_keywords["上下文词"] = self.asiainfo_contexts[:8]  # 限制数量
        
        # 去重处理（保持顺序）
        for key in expanded_keywords:
            if key != "相关词":  # 相关词需要保持优先级顺序
                expanded_keywords[key] = list(set(expanded_keywords[key]))
            else:
                # 相关词去重但保持顺序
                seen = set()
                unique_related = []
                for word in expanded_keywords[key]:
                    if word not in seen:
                        seen.add(word)
                        unique_related.append(word)
                expanded_keywords[key] = unique_related
        
        server_logger.info(f"关键词扩展完成 | 总词数: {sum(len(v) for v in expanded_keywords.values())}")
        
        return expanded_keywords
    
    def format_expansion_result(self, original_query: str, expanded_keywords: Dict[str, List[str]], expansion_type: str) -> str:
        """
        格式化扩展结果
        
        Args:
            original_query: 原始查询
            expanded_keywords: 扩展关键词字典
            expansion_type: 扩展类型
            
        Returns:
            格式化的扩展结果字符串
        """
        core_words = expanded_keywords["核心词"]
        
        # 业务领域信息
        domain_info = ""
        if expanded_keywords.get("业务领域"):
            domain_info = f"""
🏢 **识别业务领域** ({len(expanded_keywords['业务领域'])}个):
{' | '.join(expanded_keywords['业务领域'])}
"""
        
        result = f"""
🎯 关键词智能扩展结果

📝 原始查询: "{original_query}"
🔧 扩展类型: {expansion_type}{domain_info}

📊 扩展关键词:

🎯 **核心词** ({len(expanded_keywords['核心词'])}个):
{' | '.join(expanded_keywords['核心词'])}

🔄 **同义词** ({len(expanded_keywords['同义词'])}个):
{' | '.join(expanded_keywords['同义词']) if expanded_keywords['同义词'] else '暂无'}

🔗 **相关词** ({len(expanded_keywords['相关词'])}个):
{' | '.join(expanded_keywords['相关词']) if expanded_keywords['相关词'] else '暂无'}

🌐 **上下文词** ({len(expanded_keywords['上下文词'])}个):
{' | '.join(expanded_keywords['上下文词']) if expanded_keywords['上下文词'] else '暂无'}

💡 **建议搜索策略**:
1. 第1轮: 使用核心词进行精准搜索
2. 第2轮: 结合同义词扩大搜索范围  
3. 第3轮: 加入相关词进行关联搜索
4. 第4轮: 使用上下文词进行全面检索

🔍 **推荐搜索组合**:
• 精准搜索: {' '.join(core_words[:3])}
• 扩展搜索: {' '.join((expanded_keywords['相关词'][:2] + expanded_keywords['核心词'] + expanded_keywords['同义词'])[:5])}
• 全面搜索: {' '.join((expanded_keywords['相关词'][:4] + expanded_keywords['核心词'] + expanded_keywords['同义词'])[:8])}
"""
        
        return result 