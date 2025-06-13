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
            "税号": ["财务", "税务", "纳税人识别号", "税务登记号", "纳税人", "发票抬头"],
            "纳税人": ["财务", "税务", "税号", "纳税人识别号", "企业", "发票抬头"],
            "纳税人识别号": ["财务", "税务", "税号", "纳税人", "税务登记号", "发票抬头"],
            "税务登记": ["财务", "税务", "税号", "纳税人", "登记证", "发票抬头"],
            "公司税号": ["财务", "税务", "企业管理", "合规", "申报", "登记", "发票抬头"]
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
        
        # 亚信数字产品术语扩展词典 - 基于布谷术语表
        self.asiainfo_product_synonyms = {
            # OSS层产品扩展
            "IPOSS": ["智慧运维管理平台", "网管", "NMS", "运维管理", "网络管理系统", "智能运维", "IP网管"],
            "NMS": ["网络管理系统", "IPOSS", "智慧运维管理平台", "网管", "智能运维管理", "IP网管"],
            "FMS": ["故障管理系统", "iNOC", "故障管理", "运维系统"],
            "iNOC": ["智能网络运营中心", "FMS", "故障管理系统", "运维中心"],
            "IPAM": ["IP地址管理系统", "地址管理", "网络管理", "IP管理"],
            "CNCMP": ["算网融合管理平台", "多云管理平台", "算力管理", "云管理"],
            
            # 终端管理产品扩展
            "ITMS": ["综合终端管理系统", "终端管理", "ACS", "终端系统"],
            "ACS": ["终端管理系统", "ITMS", "终端管理", "设备管理"],
            "CSMP": ["智慧家庭终端融合管理平台", "家庭终端", "智慧家庭", "终端融合"],
            "TLMS": ["终端全生命周期管理系统", "终端管理", "生命周期管理"],
            "IoT": ["物联网管理系统", "物联网", "设备联网", "智能设备"],
            
            # BSS产品扩展
            "CBS": ["融合计费系统", "计费系统", "结算系统", "计费管理"],
            "CRM": ["客户关系管理系统", "客户管理", "客户服务", "营业厅系统"],
            "SPN": ["业务开通网管", "业务开通系统", "开通管理", "业务管理"],
            "AAA": ["认证授权计费系统", "接入认证平台", "认证系统", "授权管理"],
            "Settlement": ["结算系统", "计费结算", "财务结算", "账务系统"],
            "UIP": ["统一交互平台", "交互平台", "统一平台", "接口平台"],
            
            # 数据应用产品扩展
            "CCC": ["固网融合感知分析平台", "流量分析", "质差分析", "网络分析"],
            "VAMS": ["视频应用管理系统", "视频管理", "应用管理", "视频系统"],
            "FDL": ["数据中台Lite", "数据中台", "数据平台", "数据管理"],
            
            # VAS增值服务产品扩展
            "SMSC": ["短信中心", "短信系统", "消息中心", "短信服务"],
            "SMS-VAS": ["短信增值业务", "短信服务", "增值业务", "SMSP", "SMSGW"],
            "USSD": ["非结构化补充数据业务", "补充业务", "数据业务", "USSD业务"],
            "IVR": ["交互式语音应答系统", "语音应答", "交互语音", "语音系统"],
            "VC": ["充值中心", "充值系统", "VOMS", "充值管理"],
            "EIR": ["设备身份寄存器", "设备管理", "身份管理", "设备注册"],
            "E-Topup": ["电子充值", "充值服务", "在线充值", "充值业务"],
            "SCP": ["业务控制点", "控制系统", "业务控制", "服务控制"],
            "DNS": ["域名系统", "企业业务统解析系统", "域名解析", "DNS服务"],
            
            # 政企产品扩展
            "EBOSS": ["企营盘", "企营赢", "企业运营", "政企平台"],
            "企营盘": ["EBOSS", "企营赢", "企业运营", "政企平台", "企业管理", "运营系统"],
            "企营赢": ["EBOSS", "企营盘", "企业运营", "政企平台", "企业管理", "运营系统"],
            "SSCP": ["智慧环卫云平台", "环卫系统", "智慧环卫", "环卫管理"],
            "CEM": ["客户体验管理", "体验管理", "客户服务", "用户体验"],
            
            # ICT基础设施扩展
            "DHCP": ["动态主机配置协议", "地址分配", "网络配置", "IP分配"],
            
            # 缺失的产品补充
            "能力测度系统": ["能力评估", "性能测量", "系统评估", "能力分析"],
            "流量分析系统": ["CCC", "网络分析", "数据分析", "流量监控", "质差分析"],
            "AI客服问答系统": ["智能客服", "问答系统", "人工智能", "客服机器人"],
            "智慧工地云监工平台": ["工地管理", "施工监控", "云监工", "智慧建筑"],
            "校园AAA系统": ["校园网认证", "AAA", "教育网络", "学校认证", "校园管理"],
            "卫星终端管理APP": ["卫星通信", "终端管理", "移动应用", "卫星设备"],
            "政企业务综合运维平台": ["政企运维", "综合平台", "业务运维", "企业服务"],
            "政企专线客服": ["专线服务", "政企客服", "专线支持", "企业客服"],
            "RMS": ["ITMS", "远程管理", "终端管理", "设备管理"],
            "PCDN": ["CCC", "内容分发", "网络加速", "CDN服务"],
            
            # 特殊产品简称扩展
            "网管": ["NMS", "IPOSS", "智慧运维管理平台", "网络管理", "运维管理"],
            "运维": ["IPOSS", "运维管理", "网络运维", "系统运维", "智能运维"],
            "终端": ["ITMS", "终端管理", "设备管理", "终端系统"],
            "计费": ["CBS", "计费系统", "结算系统", "财务系统"],
            "客服": ["CRM", "客户服务", "客户管理", "服务系统"]
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
            "税号": ["财务", "税务", "登记", "申报", "合规", "管理", "发票抬头"],
            "纳税人": ["财务", "税务", "企业", "登记", "申报", "义务", "发票抬头"],
            "公司税号": ["财务", "税务", "企业管理", "合规", "申报", "登记", "发票抬头"],
            # 新增产品相关业务场景
            "IPOSS": ["运维", "监控", "网络", "故障", "性能", "配置", "管理", "告警"],
            "NMS": ["网络", "管理", "监控", "运维", "故障", "性能", "配置"],
            "ITMS": ["终端", "设备", "管理", "配置", "监控", "升级", "维护"],
            "CBS": ["计费", "结算", "财务", "账务", "收费", "管理", "系统"],
            "CRM": ["客户", "服务", "管理", "营销", "销售", "关系", "维护"],
            "EBOSS": ["企业", "运营", "管理", "平台", "系统", "业务", "流程"],
            "运维": ["监控", "维护", "故障", "性能", "备份", "升级", "优化", "安全"],
            "网管": ["网络", "管理", "监控", "配置", "故障", "性能", "运维"],
            "终端": ["设备", "管理", "配置", "监控", "维护", "升级", "安全"],
            "计费": ["结算", "收费", "账务", "财务", "管理", "系统", "业务"],
            # 新增产品的业务场景
            "能力测度系统": ["性能", "评估", "分析", "测量", "监控", "优化", "指标"],
            "流量分析系统": ["流量", "分析", "监控", "统计", "优化", "质量", "性能"],
            "AI客服问答系统": ["客服", "智能", "问答", "服务", "自动化", "机器人", "交互"],
            "智慧工地云监工平台": ["工地", "监控", "管理", "安全", "质量", "进度", "智能"],
            "校园AAA系统": ["校园", "认证", "授权", "网络", "学校", "教育", "管理"],
            "卫星终端管理APP": ["卫星", "终端", "管理", "通信", "移动", "设备", "控制"],
            "政企业务综合运维平台": ["政企", "运维", "业务", "综合", "平台", "服务", "管理"],
            "政企专线客服": ["政企", "专线", "客服", "服务", "支持", "企业", "通信"],
            "RMS": ["远程", "管理", "终端", "设备", "控制", "监控", "维护"],
            "PCDN": ["内容", "分发", "加速", "网络", "CDN", "服务", "优化"]
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
            "运营商产品解决方案": {
                "触发词": [
                    # OSS层产品
                    "IPOSS", "NMS", "FMS", "iNOC", "IPAM", "CNCMP",
                    "智慧运维", "网络管理", "故障管理", "算网融合", "IP网管",
                    # 终端管理产品
                    "ITMS", "ACS", "CSMP", "TLMS", "IoT", 
                    "终端管理", "智慧家庭", "物联网",
                    # 数据应用产品
                    "CCC", "VAMS", "FDL", "流量分析", "视频应用", "数据中台",
                    # ICT基础设施
                    "DNS", "IVR", "AAA", "域名系统", "语音应答"
                ],
                "扩展词": ["运维", "网络", "系统", "平台", "管理", "监控", "配置", "故障", "性能", "技术"],
                "优先级": ["运维", "网络", "系统", "管理"]
            },
            "政企产品解决方案": {
                "触发词": [
                    "EBOSS", "SSCP", "企营盘", "智慧环卫", 
                    "智慧工地", "校园AAA", "政企专线", "卫星终端",
                    "政企业务", "综合运维", "云监工"
                ],
                "扩展词": ["政企", "智慧", "云平台", "管理", "监控", "业务", "系统", "服务"],
                "优先级": ["政企", "智慧", "管理", "系统"]
            },
            "国际产品BSS解决方案": {
                "触发词": [
                    # BSS类产品
                    "CBS", "CRM", "SPN", "Settlement", "UIP",
                    "融合计费", "客户关系管理", "业务开通", "结算系统", "统一交互",
                    # VAS增值服务
                    "SMSC", "SMS-VAS", "USSD", "IVR", "VC", "EIR", 
                    "E-Topup", "SCP", "短信中心", "充值中心"
                ],
                "扩展词": ["计费", "客户", "业务", "结算", "管理", "系统", "服务", "平台"],
                "优先级": ["计费", "客户", "业务", "系统"]
            },
            "国际产品OSS解决方案": {
                "触发词": [
                    "NMS", "iNOC", "CEM", "CNCMP", "ACS",
                    "网络管理", "智能网络运营", "客户体验管理", 
                    "计算网络融合", "终端管理系统"
                ],
                "扩展词": ["网络", "运维", "管理", "监控", "系统", "平台", "服务", "技术"],
                "优先级": ["网络", "运维", "管理", "系统"]
            },
            "税务政策问题": {
                "触发词": [
                    # 税率查询相关
                    "税率", "是多少", "几个点", "百分之几", 
                    "预提所得税", "企业所得税", "个人所得税", "增值税",
                    "税务", "税收", "纳税", "税法", "税号", "纳税人", "纳税人识别号"
                ],
                "扩展词": ["财务", "税务", "政策", "法规", "税率", "申报", "缴纳", "合规", "发票", "发票抬头"],
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
        
        # 亚信数字业务特色上下文词 - 基于产品术语表扩展
        self.asiainfo_contexts = [
            "亚信数字", "公司", "员工", "部门", "项目", "客户",
            "合规", "风险", "内控", "审批", "流程", "标准",
            # 运营商产品相关
            "IPOSS", "网络管理", "运维", "监控", "告警", "性能",
            "智慧运维", "故障管理", "终端管理", "算网融合",
            # 国际产品相关
            "CBS", "CRM", "计费系统", "客户管理", "业务开通",
            "NMS", "iNOC", "网络运营中心", "客户体验",
            # 政企产品相关
            "企营赢", "EBOSS", "智慧环卫", "政企业务",
            # 技术和知识产权
            "软著", "知识产权", "数据中台", "物联网", "云平台"
        ]
        
        # 布谷专用扩展词典 - 增加产品术语关联
        self.cuckoo_synonyms = {
            "布谷": ["通用知识", "亚信数字通用", "亚信创新通用", "产品术语", "技术词汇"]
        }
        
        # 相似词映射扩展 - 增加产品术语相关的相似词匹配
        self.product_similarity_map = {
            # 产品别名和海外版本映射
            "IPOSS": ["NMS", "智慧运维", "网络管理", "运维管理", "IP网管"],
            "NMS": ["IPOSS", "网络管理系统", "智慧运维管理平台", "IP网管"],
            "ITMS": ["ACS", "终端管理系统", "综合终端管理"],
            "ACS": ["ITMS", "终端管理", "设备管理"],
            "FMS": ["iNOC", "故障管理", "智能网络运营"],
            "iNOC": ["FMS", "故障管理系统", "运维中心"],
            "EBOSS": ["企营盘", "企营赢", "政企平台"],
            "企营盘": ["EBOSS", "企营赢", "企业运营", "政企平台"],
            "企营赢": ["EBOSS", "企营盘", "企业运营", "政企平台"],
            "运维": ["网管", "监控", "维护", "管理"],
            "网管": ["运维", "NMS", "IPOSS", "网络管理", "IP网管"],
            "终端": ["设备", "ITMS", "ACS", "终端管理"],
            "计费": ["CBS", "结算", "财务", "收费"],
            # 新增产品相似词映射
            "流量分析系统": ["CCC", "网络分析", "数据分析", "流量监控"],
            "AI客服问答系统": ["智能客服", "客服系统", "问答机器人"],
            "校园AAA系统": ["校园认证", "教育网络", "学校网络"],
            "RMS": ["ITMS", "远程管理", "终端系统"],
            "PCDN": ["CCC", "CDN", "内容分发"]
        }
        
        # 合并所有同义词词典
        self.all_synonyms = {**self.finance_synonyms, **self.tech_synonyms, **self.asiainfo_product_synonyms, **self.cuckoo_synonyms}
    
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
        
        # 定义优先级顺序：产品相关领域优先于通用技术领域
        domain_priority = [
            "运营商产品解决方案",
            "政企产品解决方案", 
            "国际产品BSS解决方案",
            "国际产品OSS解决方案",
            "亚信企业内部事务",
            "税务政策问题",
            "软著相关问题",
            "差旅出行",
            "财务管理",
            "技术运维"  # 最后匹配通用技术领域
        ]
        
        # 按优先级顺序检查匹配
        for domain in domain_priority:
            if domain not in self.domain_keywords:
                continue
                
            keywords = self.domain_keywords[domain]
            trigger_words = keywords["触发词"]
            
            # 检查是否包含触发词（支持模糊匹配）
            for trigger in trigger_words:
                if trigger in query_lower:
                    matched_domains.append(domain)
                    server_logger.info(f"识别到业务领域: {domain} (触发词: {trigger})")
                    return matched_domains  # 找到高优先级匹配就返回
                # 增加相似词匹配逻辑
                elif self._is_similar_word(trigger, query_lower):
                    matched_domains.append(domain)
                    server_logger.info(f"识别到业务领域: {domain} (相似词匹配: {trigger})")
                    return matched_domains  # 找到高优先级匹配就返回
        
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
        
        # 合并产品术语相似词映射
        combined_similarity_map = {**similarity_map, **self.product_similarity_map}
        
        if word in combined_similarity_map:
            for similar in combined_similarity_map[word]:
                if similar in query:
                    return True
        
        # 反向匹配：如果查询词在相似词列表中，匹配对应的主词
        for key, similar_words in combined_similarity_map.items():
            if word == key and any(similar in query for similar in similar_words):
                return True
        
        return False
    
    def _generate_dynamic_context_words(self, query: str, domains: List[str], synonyms: set) -> List[str]:
        """
        根据查询内容和业务领域动态生成上下文词
        
        Args:
            query: 原始查询
            domains: 识别的业务领域
            synonyms: 已找到的同义词
            
        Returns:
            动态生成的上下文词列表
        """
        context_words = set()
        
        # 基础企业上下文
        base_context = ["亚信数字", "公司", "员工", "部门"]
        context_words.update(base_context)
        
        # 根据业务领域生成特定上下文
        domain_context_map = {
            "运营商产品解决方案": [
                "运营商", "电信", "网络", "基站", "5G", "数字化转型", 
                "通信网络", "网络优化", "运维服务", "技术支撑"
            ],
            "政企产品解决方案": [
                "政府", "企业", "数字政务", "智慧城市", "政企客户",
                "行业解决方案", "数字化服务", "业务转型", "信息化建设"
            ],
            "国际产品BSS解决方案": [
                "国际市场", "海外客户", "计费结算", "客户服务",
                "业务支撑", "运营商BSS", "全球化", "本地化服务"
            ],
            "国际产品OSS解决方案": [
                "网络运维", "海外部署", "运营支撑", "网络管理",
                "国际标准", "跨国运营", "技术输出", "全球服务"
            ],
            "财务管理": [
                "财务合规", "成本控制", "预算管理", "风险管控",
                "内部审计", "财务流程", "税务筹划", "资金管理"
            ],
            "技术运维": [
                "系统稳定", "性能优化", "安全防护", "故障处理",
                "技术创新", "运维自动化", "监控告警", "技术支持"
            ]
        }
        
        # 添加领域特定上下文
        for domain in domains:
            if domain in domain_context_map:
                context_words.update(domain_context_map[domain][:6])  # 每个领域取6个词
        
        # 根据产品类型生成特定上下文
        product_context_map = {
            # 网络管理产品
            "IPOSS": ["网络运维", "系统监控", "故障诊断", "性能分析", "配置管理", "自动化运维"],
            "NMS": ["网络管理", "设备监控", "拓扑发现", "告警处理", "运维效率", "网络优化"],
            "FMS": ["故障管理", "问题诊断", "应急响应", "服务恢复", "运维流程", "质量保障"],
            
            # 终端管理产品  
            "ITMS": ["终端管理", "设备配置", "远程控制", "软件分发", "安全策略", "资产管理"],
            "CSMP": ["家庭网关", "智能家居", "用户体验", "服务质量", "远程诊断", "家庭网络"],
            
            # 计费系统
            "CBS": ["计费准确", "账单管理", "收入保障", "财务对账", "费率管理", "客户账务"],
            "CRM": ["客户关系", "服务体验", "销售支持", "客户洞察", "营销活动", "客户价值"],
            
            # 政企产品
            "EBOSS": ["企业运营", "业务流程", "数据分析", "决策支持", "效率提升", "数字化管理"],
            "企营盘": ["企业运营", "业务流程", "数据分析", "决策支持", "效率提升", "数字化管理"],
            "企营赢": ["企业运营", "业务流程", "数据分析", "决策支持", "效率提升", "数字化管理"],
        }
        
        # 根据同义词中的产品添加特定上下文
        for synonym in synonyms:
            if synonym in product_context_map:
                context_words.update(product_context_map[synonym][:4])  # 每个产品取4个词
                break  # 避免重复添加相似产品的上下文
        
        # 根据查询关键词特征添加上下文
        query_lower = query.lower()
        if any(word in query_lower for word in ["网管", "运维", "管理"]):
            context_words.update(["运维效率", "管理规范", "服务质量", "技术创新"])
        elif any(word in query_lower for word in ["计费", "结算", "财务"]):
            context_words.update(["收入保障", "财务合规", "成本控制", "业务支撑"])
        elif any(word in query_lower for word in ["客户", "服务", "体验"]):
            context_words.update(["客户满意", "服务品质", "用户体验", "价值创造"])
        
        # 转换为列表并限制数量
        context_list = list(context_words)
        return context_list[:10]  # 限制最多10个上下文词
    
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
        
        # 生成上下文词（基于业务领域和产品特性动态生成）
        if expansion_type in ["comprehensive", "contextual"]:
            expanded_keywords["上下文词"] = self._generate_dynamic_context_words(original_query, matched_domains, synonyms_found)
        
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
        
        # 合并产品术语相似词映射进行权重计算
        combined_similarity_map = {**similarity_map, **self.product_similarity_map}
        
        for query_word in query_words:
            for key, similar_words in combined_similarity_map.items():
                if query_word == key.lower() or key in query_word:
                    if word.lower() in [s.lower() for s in similar_words]:
                        # 产品术语给予更高权重
                        if key in self.product_similarity_map:
                            score += 60  # 产品术语相关性更高
                        else:
                            score += 40
                elif query_word in [s.lower() for s in similar_words]:
                    if word.lower() == key.lower():
                        # 产品术语给予更高权重
                        if key in self.product_similarity_map:
                            score += 60  # 产品术语相关性更高
                        else:
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