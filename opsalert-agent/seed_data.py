"""数据初始化脚本 - 初始化SQLite数据库和模拟数据"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def init_data():
    """初始化所有数据"""
    print("=" * 60)
    print("OpsAlert Agent - 数据初始化")
    print("=" * 60)

    from app.data.cmdb_data import generate_cmdb_data
    from app.data.alert_rules import generate_alert_rules
    from app.data.historical_alerts import generate_historical_alerts
    from app.data.log_samples import generate_log_samples
    from app.data.knowledge_base import generate_knowledge_base
    from app.services.cmdb_service import get_cmdb_service
    from app.services.knowledge_service import get_knowledge_service
    from app.services.log_service import get_log_service

    # 1. CMDB数据
    print("\n[1/5] 生成CMDB拓扑数据...")
    nodes, relations, service_deps = generate_cmdb_data()
    cmdb_service = get_cmdb_service()
    cmdb_service.load_data(nodes, relations, service_deps)
    print(f"  - CMDB节点数: {len(nodes)}")
    print(f"  - 关系数: {len(relations)}")
    print(f"  - 服务数: {len(service_deps)}")

    # 2. 告警规则
    print("\n[2/5] 生成告警规则...")
    rules = generate_alert_rules()
    print(f"  - 告警规则数: {len(rules)}")

    # 3. 历史告警
    print("\n[3/5] 生成历史告警数据...")
    nodes_dict_list = [n.model_dump() for n in nodes]
    hist_alerts = generate_historical_alerts(nodes_dict_list, rules)
    print(f"  - 历史告警数: {len(hist_alerts)}")

    # 4. 日志样本
    print("\n[4/5] 生成日志样本...")
    log_samples = generate_log_samples(nodes_dict_list, count=120)
    log_service = get_log_service()
    log_service.set_log_samples(log_samples)
    print(f"  - 日志样本数: {len(log_samples)}")

    # 5. 知识库
    print("\n[5/5] 生成故障知识库并构建检索索引...")
    kb_entries = generate_knowledge_base()
    knowledge_service = get_knowledge_service()
    knowledge_service.load_knowledge_base(kb_entries)
    knowledge_service.load_historical_alerts(hist_alerts)
    print(f"  - 知识库条目数: {len(kb_entries)}")

    # 统计信息
    kb_stats = knowledge_service.get_knowledge_stats()
    hist_stats = knowledge_service.get_historical_alert_stats()

    print("\n" + "=" * 60)
    print("数据初始化完成!")
    print("=" * 60)
    print(f"  CMDB节点: {len(nodes)}")
    print(f"  告警规则: {len(rules)}")
    print(f"  历史告警: {len(hist_alerts)}")
    print(f"  日志样本: {len(log_samples)}")
    print(f"  知识库条目: {len(kb_entries)}")
    print(f"\n  知识库分类分布: {kb_stats['category_distribution']}")
    print(f"  历史告警严重程度: {hist_stats['severity_distribution']}")
    print("=" * 60)

    return {
        "cmdb_nodes": len(nodes),
        "alert_rules": len(rules),
        "historical_alerts": len(hist_alerts),
        "log_samples": len(log_samples),
        "knowledge_entries": len(kb_entries),
    }


if __name__ == "__main__":
    init_data()
