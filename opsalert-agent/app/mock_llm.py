"""Mock LLM - 基于规则模板模拟大语言模型，无需外部API"""
from typing import Dict, Any, List, Optional
from datetime import datetime


class MockLLM:
    """模拟LLM，基于规则模板生成响应"""

    def __init__(self, model_name: str = "mock-gpt-4"):
        self.model_name = model_name
        self.call_count = 0

    def chat(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """模拟聊天接口"""
        self.call_count += 1
        system_prompt = ""
        user_message = ""

        for msg in messages:
            if msg["role"] == "system":
                system_prompt = msg["content"]
            elif msg["role"] == "user":
                user_message = msg["content"]

        # 根据系统提示词的类型返回不同的模拟结果
        if "detection" in system_prompt.lower() or "分级" in system_prompt:
            return self._mock_detection(user_message)
        elif "diagnosis" in system_prompt.lower() or "根因" in system_prompt:
            return self._mock_diagnosis(user_message)
        elif "remediation" in system_prompt.lower() or "处置" in system_prompt:
            return self._mock_remediation(user_message)
        elif "report" in system_prompt.lower() or "报告" in system_prompt:
            return self._mock_report(user_message)
        else:
            return {
                "role": "assistant",
                "content": "Mock LLM 通用响应：已收到您的请求，正在处理中。",
                "model": self.model_name,
                "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
            }

    def _mock_detection(self, user_message: str) -> Dict[str, Any]:
        """模拟告警分级响应"""
        # 解析告警信息中的关键指标
        severity = "warning"
        service = "unknown"
        metric_name = "unknown"
        metric_value = 0
        threshold = 0

        # 简单的关键词提取
        if "critical" in user_message.lower() or "严重" in user_message:
            severity = "critical"
        if "P0" in user_message:
            severity = "p0"

        # 基于severity的分级模拟
        level_score_map = {
            "critical": (85, 95),
            "warning": (50, 75),
            "info": (20, 40),
            "p0": (95, 100),
        }
        low, high = level_score_map.get(severity, (50, 70))
        import random
        level_score = round(random.uniform(low, high), 1)

        if level_score >= 90:
            level = "P0"
            reason = "告警严重程度高，服务核心业务，影响范围大"
        elif level_score >= 75:
            level = "P1"
            reason = "告警严重程度较高，影响重要业务服务"
        elif level_score >= 50:
            level = "P2"
            reason = "告警严重程度中等，影响一般业务或单实例"
        else:
            level = "P3"
            reason = "告警严重程度低，影响范围较小或为预警性质"

        content = f"""
## 告警分级结果

**告警级别**: {level}
**分级得分**: {level_score} / 100
**判定理由**: {reason}

### 评分维度详情

1. **严重程度得分**: {round(level_score * 0.4, 1)} (权重40%)
   - 告警级别: {severity}
   - 指标超出阈值程度

2. **影响范围得分**: {round(level_score * 0.3, 1)} (权重30%)
   - 服务重要性: 核心业务服务
   - 受影响实例数: 多个实例
   - 上下游影响范围

3. **业务优先级得分**: {round(level_score * 0.3, 1)} (权重30%)
   - 业务优先级等级: 高
   - 是否影响用户交易/体验

### 建议动作
- 立即通知On-Call工程师
- 启动应急响应流程
- 密切关注告警发展趋势
"""

        return {
            "role": "assistant",
            "content": content,
            "level": level,
            "level_score": level_score,
            "reason": reason,
            "model": self.model_name,
            "usage": {"prompt_tokens": 200, "completion_tokens": 300, "total_tokens": 500},
        }

    def _mock_diagnosis(self, user_message: str) -> Dict[str, Any]:
        """模拟根因诊断响应"""
        content = """
## 根因分析结果

经过对告警信息、监控指标、错误日志、历史数据的综合分析，得出以下根因假设：

### 最可能根因 (置信度: 0.82)
**应用层资源耗尽导致服务响应异常**

主要证据：
1. 错误日志显示大量 Connection Pool Exhausted 异常
2. 数据库连接使用率持续在95%以上
3. 慢查询数量激增，平均查询时间从50ms上升到500ms
4. 历史相似告警均由慢查询导致连接池耗尽

### 次要可能 (置信度: 0.65)
**业务流量突增**

主要证据：
1. QPS较平时增长了3倍
2. 各服务资源使用率均有上升
3. 接口响应时间整体变慢

### 其他可能 (置信度: 0.45)
**缓存失效导致数据库压力增大**

主要证据：
1. 缓存命中率从98%下降到75%
2. 数据库读取QPS显著增加
3. 近期有缓存相关配置变更

### 分析方法
- 基于知识图谱的规则推理
- 错误日志语义分析
- 历史告警相似度匹配
- 指标关联分析
"""

        return {
            "role": "assistant",
            "content": content,
            "top_cause": "应用层资源耗尽导致服务响应异常",
            "confidence": 0.82,
            "model": self.model_name,
            "usage": {"prompt_tokens": 500, "completion_tokens": 400, "total_tokens": 900},
        }

    def _mock_remediation(self, user_message: str) -> Dict[str, Any]:
        """模拟处置建议响应"""
        content = """
## 处置建议方案

根据根因分析结果，建议按照以下步骤进行处置：

### 紧急处理（立即执行）

1. **检查并kill慢查询** (预计5分钟, 风险:中)
   - 操作：登录数据库执行 `show full processlist`
   - 定位执行时间超过30秒的查询
   - 确认非关键业务后kill对应连接
   - 回滚：无，查询可重新执行

2. **临时增大连接池** (预计10分钟, 风险:低)
   - 操作：调整数据库连接池max_size配置
   - 从当前200增大到300
   - 重启对应服务实例（滚动重启）
   - 回滚：恢复原配置值

3. **启用限流降级** (预计5分钟, 风险:中)
   - 操作：在网关层开启限流
   - 限制非核心接口的QPS
   - 核心接口保障优先通过
   - 回滚：关闭限流策略

### 根本解决

4. **优化慢查询SQL** (预计30分钟, 风险:低)
   - 分析TOP慢查询的执行计划
   - 添加缺失的索引
   - 优化SQL写法
   - 回滚：删除新增索引

5. **增加缓存层** (预计60分钟, 风险:中)
   - 对热点查询结果增加缓存
   - 设置合理的过期时间
   - 降低数据库读压力
   - 回滚：关闭缓存

### 风险评估
- 整体风险等级：中
- 预计总处理时间：45分钟
- 关键操作需要双人复核

### 回滚方案
所有变更操作均有对应的回滚步骤，如遇问题可快速恢复。
"""

        return {
            "role": "assistant",
            "content": content,
            "steps_count": 5,
            "estimated_time": 45,
            "risk_level": "medium",
            "model": self.model_name,
            "usage": {"prompt_tokens": 400, "completion_tokens": 500, "total_tokens": 900},
        }

    def _mock_report(self, user_message: str) -> Dict[str, Any]:
        """模拟报告生成响应"""
        content = """
# 事故报告 (Postmortem)

## 摘要
本次事故由数据库慢查询导致连接池耗尽，进而引发order-service服务响应时间增长和错误率升高。事故持续约25分钟，影响了订单创建和支付相关功能。

## 时间线

| 时间 | 事件 | 说明 |
|------|------|------|
| 14:30:00 | 告警触发 | order-service的P99响应时间超过1000ms阈值 |
| 14:30:15 | 自动分析 | OpsAlert Agent启动自动分析 |
| 14:31:30 | 根因定位 | 初步判定为数据库连接池耗尽，置信度82% |
| 14:32:00 | 通知On-Call | 自动通知DBA和SRE值班人员 |
| 14:35:00 | 人工介入 | DBA开始排查慢查询 |
| 14:40:00 | 问题定位 | 发现订单表缺少索引导致慢查询 |
| 14:45:00 | 紧急修复 | 添加索引后数据库性能恢复 |
| 14:55:00 | 服务恢复 | 所有指标恢复正常水平 |

## 影响范围
- 受影响服务：order-service, payment-service
- 受影响用户：约5%的下单用户
- 业务影响：订单创建成功率下降12%
- 持续时间：约25分钟

## 根因分析

### 直接原因
订单查询接口的SQL缺少合适的索引，导致全表扫描，数据库CPU和连接被占满。

### 根本原因
1. 代码发布时未进行SQL审核，新增查询未考虑性能影响
2. 慢查询告警阈值设置过高，未能及时预警
3. 数据库连接池监控不够精细

## 做得好的
- 告警及时触发，检测时间短
- 自动化分析快速给出了正确的根因方向
- On-Call响应及时，10分钟内介入处理

## 做得不好的
- SQL变更审核流程不完善
- 慢查询预警阈值需要优化
- 缺乏自动kill慢查询的机制

## 改进项 (Action Items)

1. **[高] 完善SQL审核流程**
   - 负责人：DBA团队
   - 截止时间：7天内
   - 所有SQL变更必须经过审核和性能测试

2. **[高] 优化慢查询告警阈值**
   - 负责人：SRE团队
   - 截止时间：3天内
   - 增加分级别告警，提前预警

3. **[中] 增加自动处理机制**
   - 负责人：SRE团队
   - 截止时间：14天内
   - 实现自动kill超过阈值的慢查询

4. **[中] 加强容量规划**
   - 负责人：架构团队
   - 截止时间：30天内
   - 定期进行压测和容量评估

5. **[低] 完善故障演练**
   - 负责人：SRE团队
   - 截止时间：30天内
   - 每季度进行一次数据库性能故障演练

## 经验教训
1. 数据库性能问题往往是连锁反应的起点
2. 自动化运维工具可以显著缩短MTTR
3. 完善的监控和告警是快速发现问题的基础
4. 定期的故障演练有助于提升应急响应能力

---
*报告生成时间：{now}*
*生成工具：OpsAlert Agent v1.0*
""".format(now=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        return {
            "role": "assistant",
            "content": content,
            "sections": ["摘要", "时间线", "影响范围", "根因分析", "改进项"],
            "model": self.model_name,
            "usage": {"prompt_tokens": 600, "completion_tokens": 800, "total_tokens": 1400},
        }


# 全局单例
_mock_llm: Optional[MockLLM] = None


def get_mock_llm() -> MockLLM:
    global _mock_llm
    if _mock_llm is None:
        _mock_llm = MockLLM()
    return _mock_llm
