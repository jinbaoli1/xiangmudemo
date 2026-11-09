# OpsAlert Agent - PowerShell 测试脚本
# 使用方法: .\test_curl.ps1

$BaseUrl = "http://127.0.0.1:8000"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " OpsAlert Agent API 测试脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 1. 健康检查
Write-Host "`n[1] 健康检查" -ForegroundColor Yellow
try {
    $resp = Invoke-RestMethod -Uri "$BaseUrl/health" -Method Get -UseBasicParsing
    Write-Host "  Status: $($resp.status)" -ForegroundColor Green
} catch {
    Write-Host "  Failed: $($_.Exception.Message)" -ForegroundColor Red
}

# 2. 接入告警
Write-Host "`n[2] 接入告警 - CPU使用率过高" -ForegroundColor Yellow
$alertBody = @{
    alert_name = "CPU使用率过高"
    severity = "critical"
    host = "order-service-01.prod.local"
    service = "order-service"
    metric_name = "cpu_usage"
    metric_value = 95.5
    threshold = 90
    unit = "%"
    summary = "CPU使用率过高: order-service-01 cpu_usage=95.5%"
    description = "订单服务CPU使用率持续超过90%阈值"
    labels = @{ environment = "prod"; region = "cn-east-1" }
    tags = @("cpu", "critical")
} | ConvertTo-Json -Depth 10

try {
    $resp = Invoke-RestMethod -Uri "$BaseUrl/api/v1/alerts" -Method Post -Body $alertBody -ContentType "application/json" -UseBasicParsing
    Write-Host "  Alert ID: $($resp.id)" -ForegroundColor Green
    Write-Host "  Fingerprint: $($resp.fingerprint)" -ForegroundColor Green
    $script:alertId = $resp.id
} catch {
    Write-Host "  Failed: $($_.Exception.Message)" -ForegroundColor Red
}

# 3. 同步分析告警
Write-Host "`n[3] 同步分析告警 - 数据库连接池耗尽" -ForegroundColor Yellow
$analysisBody = @{
    alert_name = "数据库连接池耗尽"
    severity = "critical"
    host = "order-service-01.prod.local"
    service = "order-service"
    metric_name = "db_connections"
    metric_value = 96
    threshold = 90
    unit = "%"
    summary = "数据库连接池使用率超过90%阈值"
    description = "订单服务数据库连接池即将耗尽"
    labels = @{ environment = "prod" }
    tags = @("database", "critical")
} | ConvertTo-Json -Depth 10

try {
    $resp = Invoke-RestMethod -Uri "$BaseUrl/api/v1/analyze" -Method Post -Body $analysisBody -ContentType "application/json" -UseBasicParsing
    Write-Host "  Trace ID: $($resp.trace_id)" -ForegroundColor Green
    Write-Host "  告警级别: $($resp.level)" -ForegroundColor Green
    Write-Host "  分级得分: $($resp.level_score)" -ForegroundColor Green
    if ($resp.top_root_cause) {
        Write-Host "  最可能根因: $($resp.top_root_cause.description)" -ForegroundColor Green
        Write-Host "  置信度: $($resp.top_root_cause.confidence)" -ForegroundColor Green
    }
    Write-Host "  处置步骤数: $($resp.remediation_steps.Count)" -ForegroundColor Green
    Write-Host "  分析状态: $($resp.status)" -ForegroundColor Green
    Write-Host "  Agent步骤数: $($resp.agent_steps.Count)" -ForegroundColor Green
} catch {
    Write-Host "  Failed: $($_.Exception.Message)" -ForegroundColor Red
}

# 4. 告警列表
Write-Host "`n[4] 告警列表" -ForegroundColor Yellow
try {
    $resp = Invoke-RestMethod -Uri "$BaseUrl/api/v1/alerts" -Method Get -UseBasicParsing
    Write-Host "  总告警数: $($resp.total)" -ForegroundColor Green
} catch {
    Write-Host "  Failed: $($_.Exception.Message)" -ForegroundColor Red
}

# 5. 知识库搜索
Write-Host "`n[5] 知识库搜索 - 'CPU 高'" -ForegroundColor Yellow
try {
    $resp = Invoke-RestMethod -Uri "$BaseUrl/api/v1/knowledge/search?q=CPU%E4%BD%BF%E7%94%A8%E7%8E%87%E8%BF%87%E9%AB%98" -Method Get -UseBasicParsing
    Write-Host "  搜索结果数: $($resp.total)" -ForegroundColor Green
    if ($resp.results.Count -gt 0) {
        Write-Host "  Top 1: $($resp.results[0].title) (score: $($resp.results[0].retrieval_score))" -ForegroundColor Green
    }
} catch {
    Write-Host "  Failed: $($_.Exception.Message)" -ForegroundColor Red
}

# 6. 历史告警相似匹配
Write-Host "`n[6] 历史告警相似匹配" -ForegroundColor Yellow
try {
    $resp = Invoke-RestMethod -Uri "$BaseUrl/api/v1/history/similar?alert_name=CPU%E4%BD%BF%E7%94%A8%E7%8E%87%E8%BF%87%E9%AB%98&service=order-service&metric_name=cpu_usage" -Method Get -UseBasicParsing
    Write-Host "  相似告警数: $($resp.total)" -ForegroundColor Green
} catch {
    Write-Host "  Failed: $($_.Exception.Message)" -ForegroundColor Red
}

# 7. CMDB拓扑
Write-Host "`n[7] CMDB拓扑 - order-service" -ForegroundColor Yellow
try {
    $resp = Invoke-RestMethod -Uri "$BaseUrl/api/v1/cmdb/topology?service=order-service" -Method Get -UseBasicParsing
    Write-Host "  上游服务数: $($resp.upstream_services.Count)" -ForegroundColor Green
    Write-Host "  下游服务数: $($resp.downstream_services.Count)" -ForegroundColor Green
    Write-Host "  影响级别: $($resp.impact_scope.impact_level)" -ForegroundColor Green
} catch {
    Write-Host "  Failed: $($_.Exception.Message)" -ForegroundColor Red
}

# 8. 影响范围评估
Write-Host "`n[8] 影响范围评估 - payment-service" -ForegroundColor Yellow
try {
    $resp = Invoke-RestMethod -Uri "$BaseUrl/api/v1/cmdb/impact/payment-service" -Method Get -UseBasicParsing
    Write-Host "  业务优先级: $($resp.business_priority)" -ForegroundColor Green
    Write-Host "  影响评分: $($resp.impact_score)" -ForegroundColor Green
    Write-Host "  影响级别: $($resp.impact_level)" -ForegroundColor Green
} catch {
    Write-Host "  Failed: $($_.Exception.Message)" -ForegroundColor Red
}

# 9. 告警统计
Write-Host "`n[9] 告警统计概览" -ForegroundColor Yellow
try {
    $resp = Invoke-RestMethod -Uri "$BaseUrl/api/v1/alerts/stats/summary" -Method Get -UseBasicParsing
    Write-Host "  P0: $($resp.by_level.P0)" -ForegroundColor Green
    Write-Host "  P1: $($resp.by_level.P1)" -ForegroundColor Green
    Write-Host "  P2: $($resp.by_level.P2)" -ForegroundColor Green
    Write-Host "  P3: $($resp.by_level.P3)" -ForegroundColor Green
} catch {
    Write-Host "  Failed: $($_.Exception.Message)" -ForegroundColor Red
}

# 10. 知识库统计
Write-Host "`n[10] 知识库统计" -ForegroundColor Yellow
try {
    $resp = Invoke-RestMethod -Uri "$BaseUrl/api/v1/knowledge/stats" -Method Get -UseBasicParsing
    Write-Host "  总条目数: $($resp.total_entries)" -ForegroundColor Green
    Write-Host "  分类分布: $($resp.category_distribution | ConvertTo-Json -Compress)" -ForegroundColor Green
} catch {
    Write-Host "  Failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host " 测试完成" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "`n提示: SSE流式分析请使用以下命令测试:" -ForegroundColor Yellow
Write-Host "  curl -N -X POST $BaseUrl/api/v1/analyze/stream -H 'Content-Type: application/json' -d '{\"alert_name\":\"测试告警\",\"severity\":\"critical\",\"host\":\"test\",\"service\":\"order-service\",\"metric_name\":\"cpu_usage\",\"metric_value\":95,\"threshold\":90,\"unit\":\"%\"}'"
