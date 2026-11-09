#!/usr/bin/env python3
"""
OpsAlert Agent 测试脚本
使用 httpx 测试所有 API 接口
"""
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_all_apis():
    """测试所有API接口"""
    import httpx

    base_url = "http://127.0.0.1:8000"
    client = httpx.Client(timeout=30.0)

    passed = 0
    failed = 0

    def test(name, method, path, json_data=None, params=None):
        nonlocal passed, failed
        try:
            if method == "GET":
                resp = client.get(f"{base_url}{path}", params=params)
            else:
                resp = client.post(f"{base_url}{path}", json=json_data)

            if resp.status_code in (200, 201):
                print(f"  [PASS] {name} (status={resp.status_code})")
                passed += 1
                return resp.json()
            else:
                print(f"  [FAIL] {name} (status={resp.status_code})")
                print(f"         Error: {resp.text[:200]}")
                failed += 1
                return None
        except Exception as e:
            print(f"  [FAIL] {name} - {str(e)}")
            failed += 1
            return None

    print("=" * 60)
    print("OpsAlert Agent API 测试")
    print("=" * 60)

    # 1. 健康检查
    print("\n1. 健康检查")
    test("健康检查", "GET", "/health")

    # 2. 根路径
    print("\n2. 根路径")
    test("根路径", "GET", "/")

    # 3. 告警接入
    print("\n3. 告警接入")
    alert_data = {
        "alert_name": "CPU使用率过高",
        "severity": "critical",
        "host": "order-service-01.prod.local",
        "service": "order-service",
        "metric_name": "cpu_usage",
        "metric_value": 95.5,
        "threshold": 90,
        "unit": "%",
        "summary": "CPU使用率过高: order-service-01 cpu_usage=95.5% (阈值=90%)",
        "description": "订单服务CPU使用率持续超过90%阈值",
        "labels": {"environment": "prod", "region": "cn-east-1"},
        "tags": ["cpu", "critical"],
    }
    result = test("创建告警", "POST", "/api/v1/alerts", alert_data)
    alert_id = result.get("id") if result else None

    # 4. 告警列表
    print("\n4. 告警查询")
    test("告警列表", "GET", "/api/v1/alerts")
    test("按级别过滤", "GET", "/api/v1/alerts", params={"level": "P1"})
    test("告警统计", "GET", "/api/v1/alerts/stats/summary")
    if alert_id:
        test("告警详情", "GET", f"/api/v1/alerts/{alert_id}")

    # 5. 同步分析
    print("\n5. 告警分析（同步）")
    analysis_alert = {
        "alert_name": "数据库连接池耗尽",
        "severity": "critical",
        "host": "order-service-01.prod.local",
        "service": "order-service",
        "metric_name": "db_connections",
        "metric_value": 96,
        "threshold": 90,
        "unit": "%",
        "summary": "数据库连接池使用率超过90%阈值",
        "description": "订单服务数据库连接池即将耗尽",
        "labels": {"environment": "prod"},
        "tags": ["database", "critical"],
    }
    result = test("同步分析", "POST", "/api/v1/analyze", analysis_alert)
    if result:
        print(f"         级别: {result.get('level')}")
        print(f"         根因: {result.get('top_root_cause', {}).get('description') if result.get('top_root_cause') else 'N/A'}")
        print(f"         处置步骤: {len(result.get('remediation_steps', []))}步")
        print(f"         状态: {result.get('status')}")

    # 6. 知识库搜索
    print("\n6. 知识库搜索")
    test("搜索CPU相关", "GET", "/api/v1/knowledge/search", params={"q": "CPU使用率过高"})
    test("搜索数据库相关", "GET", "/api/v1/knowledge/search", params={"q": "慢查询 索引"})
    test("搜索内存相关", "GET", "/api/v1/knowledge/search", params={"q": "OOM 内存溢出"})
    test("知识库统计", "GET", "/api/v1/knowledge/stats")

    # 7. 历史告警匹配
    print("\n7. 历史告警匹配")
    test("相似告警查询", "GET", "/api/v1/history/similar",
         params={"alert_name": "CPU使用率过高", "service": "order-service", "metric_name": "cpu_usage"})
    test("历史告警统计", "GET", "/api/v1/history/stats")

    # 8. CMDB拓扑
    print("\n8. CMDB拓扑")
    test("服务拓扑", "GET", "/api/v1/cmdb/topology", params={"service": "order-service"})
    test("服务列表", "GET", "/api/v1/cmdb/services")
    test("影响范围", "GET", "/api/v1/cmdb/impact/order-service")

    # 9. 事故列表
    print("\n9. 事故管理")
    test("事故列表", "GET", "/api/v1/incidents")

    # 10. SSE流式分析（测试能否正常连接）
    print("\n10. SSE流式分析（连接测试）")
    try:
        sse_alert = {
            "alert_name": "接口错误率过高",
            "severity": "critical",
            "host": "payment-service-01.prod.local",
            "service": "payment-service",
            "metric_name": "http_error_rate",
            "metric_value": 12.5,
            "threshold": 10,
            "unit": "%",
            "summary": "支付服务错误率超过阈值",
        }
        with client.stream("POST", f"{base_url}/api/v1/analyze/stream", json=sse_alert, timeout=60.0) as resp:
            if resp.status_code == 200:
                event_count = 0
                for line in resp.iter_lines():
                    if line and line.startswith("event:"):
                        event_count += 1
                print(f"  [PASS] SSE流式分析 (收到 {event_count} 个事件)")
                passed += 1
            else:
                print(f"  [FAIL] SSE流式分析 (status={resp.status_code})")
                failed += 1
    except Exception as e:
        print(f"  [FAIL] SSE流式分析 - {str(e)}")
        failed += 1

    # 汇总
    print("\n" + "=" * 60)
    print(f"测试结果: {passed} passed, {failed} failed, 共 {passed + failed} 个测试")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = test_all_apis()
    sys.exit(0 if success else 1)
