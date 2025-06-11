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
            "财务": ["会计", "核算", "账务", "资金", "经费", "税号", "纳税人", "税务登记"],
            "税务": ["税收", "纳税", "税法", "税政", "征税", "税号", "纳税人识别号"],
            "制度": ["规定", "办法", "规范", "标准", "流程"],
            "政策": ["法规", "条例", "规章", "通知", "文件"],
            "流程": ["程序", "步骤", "操作", "处理", "执行"],
            "管理": ["监管", "控制", "治理", "运营", "维护"],
            "报告": ["报表", "汇报", "总结", "分析", "统计"],
            "审计": ["检查", "核查", "稽核", "监察", "评估"],
            "报销": ["费用", "支出", "结算", "核销", "申请"],
            # 税号相关词汇应该主要扩展为财务
            "税号": ["财务", "税务", "纳税人识别号", "税务登记号", "纳税人"],
            "纳税人": ["财务", "税务", "税号", "纳税人识别号", "企业"],
            "纳税人识别号": ["财务", "税务", "税号", "纳税人", "税务登记号"],
            "税务登记": ["财务", "税务", "税号", "纳税人", "登记证"],
            "公司税号": ["财务", "税务", "企业管理", "合规", "申报", "登记"]
        }
        
        # 技术相关扩展词典
        self.tech_synonyms = {
            "系统": ["平台", "软件", "应用", "工具", "程序"],
            "网络": ["通信", "连接", "传输", "协议", "架构"],
            "安全": ["防护", "保护", "加密", "认证", "权限"],
            "数据": ["信息", "资料", "记录", "档案", "文档"],
            "标准": ["规范", "准则", "要求", "指标", "基准"],
            "技术": ["工艺", "方法", "手段", "技能", "专业"],
            "软著": ["软件著作权", "知识产权", "版权", "专利", "登记"]
        }
        
        # 业务场景相关词典
        self.business_contexts = {
            "财务": ["预算", "成本", "收入", "支出", "利润", "资产", "税号", "纳税人"],
            "税务": ["发票", "申报", "缴纳", "减免", "优惠", "合规", "税号", "纳税人识别号"],
            "制度": ["执行", "监督", "考核", "培训", "宣贯", "更新"],
            "系统": ["部署", "配置", "维护", "升级", "监控", "备份"],
            "网络": ["带宽", "延迟", "稳定", "故障", "优化", "扩容"],
            "报销": ["流程", "审批", "发票", "凭证", "标准", "政策"],
            "软著": ["申请", "材料", "流程", "费用", "权利", "保护"],
            # 税号相关的业务场景词汇
            "税号": ["财务", "税务", "登记", "申报", "合规", "管理"],
            "纳税人": ["财务", "税务", "企业", "登记", "申报", "义务"],
            "公司税号": ["财务", "税务", "企业管理", "合规", "申报", "登记"]
        }
        
        # 业务领域识别词典 - 基于用户提供的场景分类进行更新
        self.domain_keywords = {
            "亚信企业内部事务": {
                "触发词": [
                    # 法务类
                    "合同", "审核", "知识产权", "法律", "咨询", "法务",
                    # 财务类
                    "报销", "流程", "预算", "管理", "财务", "制度", "税号", "纳税人", "税务登记", "纳税人识别号",
                    # 人事类
                    "招聘", "入职", "考勤", "休假", "培训", "发展", "人事", "员工", "薪资", "绩效",
                    # 行政类
                    "办公", "设施", "后勤", "保障", "会议", "管理", "行政", "采购", "资产", "设备",
                    # 补贴类
                    "补贴", "申请", "发放", "标准", "结算", "周期",
                    # 企营赢/EBOSS类
                    "企营赢", "EBOSS", "系统", "平台",
                    # 软著类
                    "软著", "软件著作权", "版权", "专利"
                ],
                "扩展词": ["制度", "流程", "审批", "管理", "政策", "规范", "标准", "监督", "合规", "内控"],
                "优先级": ["制度", "流程", "审批", "管理"]
            },
            "税务政策问题": {
                "触发词": [
                    # 税率查询相关
                    "税率", "是多少", "几个点", "百分之几", 
                    "预提所得税", "企业所得税", "个人所得税", "增值税",
                    "税务", "税收", "纳税", "税法", "税号", "纳税人", "纳税人识别号"
                ],
                "扩展词": ["财务", "税务", "政策", "法规", "税率", "申报", "缴纳", "合规", "发票"],
                "优先级": ["财务", "税务", "政策", "税率"]
            },
            "软著相关问题": {
                "触发词": [
                    "软著", "软件著作权", "版权", "知识产权", "专利",
                    "申请", "材料", "时间", "费用", "流程",
                    "权利", "保护", "侵权", "维权",
                    "登记", "变更", "续展", "证书", "补办"
                ],
                "扩展词": ["软著", "知识产权", "申请", "流程", "材料", "费用", "保护", "权利", "法规"],
                "优先级": ["软著", "知识产权", "申请", "流程"]
            },
            # 保留原有的其他业务领域，以兼容现有功能
            "差旅出行": {
                "触发词": ["出差", "差旅", "酒店", "机票", "火车", "高铁", "住宿", "交通", "路费", "餐费"],
                "扩展词": ["财务", "行政", "报销", "费用", "标准", "审批", "发票", "凭证", "预算", "成本控制"],
                "优先级": ["财务", "行政", "报销", "费用"]
            },
            "财务管理": {
                "触发词": ["财务", "会计", "成本", "预算", "报销", "发票", "税务", "审计", "税号", "纳税人", "纳税人识别号"],
                "扩展词": ["制度", "流程", "审批", "核算", "监管", "合规", "风险", "内控"],
                "优先级": ["制度", "流程", "审批", "合规"]
            },
            "技术运维": {
                "触发词": ["系统", "网络", "服务器", "数据库", "监控", "运维", "故障", "性能", "IPOSS"],
                "扩展词": ["技术", "标准", "规范", "流程", "安全", "备份", "升级", "优化"],
                "优先级": ["技术", "标准", "规范", "流程"]
            }
        }
        
        # 亚信数字业务特色上下文词
        self.asiainfo_contexts = [
            "亚信数字", "公司", "员工", "部门", "项目", "客户",
            "合规", "风险", "内控", "审批", "流程", "标准",
            "IPOSS", "网络管理", "运维", "监控", "告警", "性能",
            "企营赢", "EBOSS", "软著", "知识产权"
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
            
            # 检查是否包含触发词（支持模糊匹配）
            for trigger in trigger_words:
                if trigger in query_lower:
                    matched_domains.append(domain)
                    server_logger.info(f"识别到业务领域: {domain} (触发词: {trigger})")
                    break
                # 增加相似词匹配逻辑
                elif self._is_similar_word(trigger, query_lower):
                    matched_domains.append(domain)
                    server_logger.info(f"识别到业务领域: {domain} (相似词匹配: {trigger})")
                    break
        
        return matched_domains
    
    def _is_similar_word(self, word: str, query: str) -> bool:
        """
        检查词汇相似性
        
        Args:
            word: 词典中的词汇
            query: 查询内容
            
        Returns:
            是否相似
        """
        # 财务税务相关的相似词匹配 - 重点增强税号、纳税人的财务关联
        similarity_map = {
            "税务": ["税收", "纳税", "征税", "税法", "税号", "纳税人", "纳税人识别号"],
            "财务": ["财政", "资金", "金融", "税号", "纳税人", "税务登记", "纳税人识别号"],
            "制度": ["政策", "规定", "法规"],
            "管理": ["监管", "治理", "控制"],
            "审计": ["审核", "核查", "检查"],
            "政策": ["制度", "规定", "办法"],
            "税号": ["纳税人识别号", "税务登记号", "财务", "税务", "纳税人"],
            "纳税人": ["税号", "纳税人识别号", "财务", "税务", "企业", "税务登记"],
            "纳税人识别号": ["税号", "纳税人", "财务", "税务", "税务登记号"],
            "软著": ["软件著作权", "版权", "知识产权", "专利"],
            "报销": ["费用", "支出", "财务", "申请", "审批", "流程"]
        }
        
        if word in similarity_map:
            for similar in similarity_map[word]:
                if similar in query:
                    return True
        
        return False
    
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
        
        # 改进的关键词处理 - 支持复合词匹配
        core_words = [word.strip() for word in original_query.split() if word.strip()]
        
        expanded_keywords = {
            "核心词": core_words,
            "同义词": [],
            "相关词": [],
            "上下文词": [],
            "业务领域": matched_domains
        }
        
        # 生成同义词 - 改进匹配逻辑
        synonyms_found = set()
        
        # 1. 首先尝试完整匹配（如"公司税号"）
        query_lower = original_query.lower()
        if query_lower in self.all_synonyms:
            synonyms_found.update(self.all_synonyms[query_lower])
            server_logger.info(f"完整匹配找到同义词: {query_lower}")
        
        # 2. 然后尝试分词匹配
        for word in core_words:
            word_lower = word.lower()
            if word_lower in self.all_synonyms:
                synonyms_found.update(self.all_synonyms[word_lower])
                server_logger.info(f"分词匹配找到同义词: {word_lower}")
            else:
                # 3. 尝试包含匹配（如"税号"包含在"公司税号"中）
                for synonym_key in self.all_synonyms:
                    if synonym_key in word_lower or word_lower in synonym_key:
                        synonyms_found.update(self.all_synonyms[synonym_key])
                        server_logger.info(f"包含匹配找到同义词: {synonym_key} <- {word_lower}")
                        break
                
                # 4. 尝试相似词匹配
                for synonym_key, synonym_list in self.all_synonyms.items():
                    if self._is_similar_word(synonym_key, word_lower):
                        synonyms_found.update(synonym_list)
                        server_logger.info(f"相似词匹配找到同义词: {synonym_key} <- {word_lower}")
                        break
        
        expanded_keywords["同义词"] = list(synonyms_found)
        
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
            else:
                # 尝试通过相似词匹配找到业务场景相关词
                for context_key, context_list in self.business_contexts.items():
                    if self._is_similar_word(context_key, word):
                        expanded_keywords["相关词"].extend(context_list)
                        server_logger.info(f"通过相似词匹配为 '{word}' 找到业务场景词组: {context_key}")
                        break
        
        # 生成上下文词（基于亚信数字业务特点）
        if expansion_type in ["comprehensive", "contextual"]:
            expanded_keywords["上下文词"] = self.asiainfo_contexts[:8]  # 限制数量
        
        # 去重处理并按相关性排序
        for key in expanded_keywords:
            if key in ["同义词", "相关词"]:  # 对同义词和相关词进行智能排序
                # 先去重
                unique_words = list(set(expanded_keywords[key]))
                # 按相关性排序
                expanded_keywords[key] = self._sort_expanded_words(unique_words, original_query)
                server_logger.info(f"{key}按相关性排序完成，共{len(expanded_keywords[key])}个词")
            else:
                # 其他类型只去重
                expanded_keywords[key] = list(set(expanded_keywords[key]))
        
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

    def _calculate_word_relevance(self, word: str, original_query: str) -> int:
        """
        计算词汇与原始查询的相关性分数
        
        Args:
            word: 待评分的词汇
            original_query: 原始查询
            
        Returns:
            相关性分数 (分数越高越相关)
        """
        score = 0
        query_lower = original_query.lower()
        word_lower = word.lower()
        
        # 1. 直接包含关系 (最高分)
        if word_lower in query_lower:
            score += 100
        
        # 2. 查询词在扩展词中的包含关系
        query_words = [w.strip().lower() for w in original_query.split() if w.strip()]
        for query_word in query_words:
            if query_word in word_lower:
                score += 80
        
        # 3. 税号相关的特殊高权重处理
        tax_related_queries = ["税号", "纳税人", "公司税号", "纳税人识别号", "税务登记"]
        finance_core_words = ["财务", "税务"]
        
        for tax_query in tax_related_queries:
            if tax_query in query_lower:
                if word_lower in finance_core_words:
                    score += 200  # 给予财务、税务最高权重
                    server_logger.info(f"税号查询 '{tax_query}' 匹配财务核心词 '{word}', 高权重: +200")
        
        # 4. 通过同义词字典的关联度
        for query_word in query_words:
            for synonym_key, synonym_list in self.all_synonyms.items():
                if query_word == synonym_key.lower():
                    # 如果查询词是同义词组的键，该组内的词得高分
                    if word in synonym_list:
                        score += 60
                elif query_word in [s.lower() for s in synonym_list]:
                    # 如果查询词在同义词列表中，同组其他词得分
                    if word == synonym_key or word in synonym_list:
                        score += 50
        
        # 5. 通过相似词映射的关联度 - 增强税号、纳税人的关联
        similarity_map = {
            "税务": ["税收", "纳税", "征税", "税法", "税号", "纳税人", "纳税人识别号"],
            "财务": ["财政", "资金", "金融", "税号", "纳税人", "税务登记", "纳税人识别号"],
            "制度": ["政策", "规定", "法规"],
            "管理": ["监管", "治理", "控制"],
            "审计": ["审核", "核查", "检查"],
            "政策": ["制度", "规定", "办法"],
            "税号": ["纳税人识别号", "税务登记号", "财务", "税务", "纳税人"],
            "纳税人": ["税号", "纳税人识别号", "财务", "税务", "企业", "税务登记"],
            "纳税人识别号": ["税号", "纳税人", "财务", "税务", "税务登记号"],
            "软著": ["软件著作权", "版权", "知识产权", "专利"],
            "报销": ["费用", "支出", "财务", "申请", "审批", "流程"]
        }
        
        for query_word in query_words:
            for key, similar_words in similarity_map.items():
                if query_word == key.lower() or key in query_word:
                    if word.lower() in [s.lower() for s in similar_words]:
                        score += 40
                elif query_word in [s.lower() for s in similar_words]:
                    if word.lower() == key.lower():
                        score += 40
        
        # 6. 通过业务场景词典的关联度
        for query_word in query_words:
            for context_key, context_words in self.business_contexts.items():
                # 直接匹配业务场景键
                if query_word == context_key.lower() or context_key in query_word:
                    if word in context_words:
                        score += 50
                # 通过相似词匹配业务场景键  
                elif self._is_similar_word(context_key, query_word):
                    if word in context_words:
                        score += 45
        
        return score
    
    def _sort_expanded_words(self, words: List[str], original_query: str) -> List[str]:
        """
        根据相关性对扩展词进行排序
        
        Args:
            words: 扩展词列表
            original_query: 原始查询
            
        Returns:
            排序后的扩展词列表
        """
        if not words:
            return words
        
        # 计算每个词的相关性分数并排序
        word_scores = [(word, self._calculate_word_relevance(word, original_query)) for word in words]
        word_scores.sort(key=lambda x: x[1], reverse=True)
        
        sorted_words = [word for word, score in word_scores]
        
        server_logger.info(f"扩展词相关性排序: {[(w, s) for w, s in word_scores[:5]]}")  # 记录前5个的分数
        
        return sorted_words 