# MedTriage API 测试脚本 (PowerShell)
# 使用方法: .\test_api.ps1
# 确保服务已启动: python -m uvicorn app.main:app --reload --port 8000

$BaseUrl = "http://localhost:8000"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  MedTriage API 测试脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. 健康检查
Write-Host "1. 健康检查" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$BaseUrl/health" -Method Get
    Write-Host "   状态: $($response.status)" -ForegroundColor Green
    Write-Host "   版本: $($response.version)" -ForegroundColor Green
} catch {
    Write-Host "   失败: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# 2. 数据统计
Write-Host "2. 数据统计" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$BaseUrl/api/v1/stats/summary" -Method Get
    Write-Host "   科室: $($response.data.科室)" -ForegroundColor Green
    Write-Host "   医生: $($response.data.医生)" -ForegroundColor Green
    Write-Host "   症状: $($response.data.症状)" -ForegroundColor Green
    Write-Host "   疾病: $($response.data.疾病)" -ForegroundColor Green
    Write-Host "   药品: $($response.data.药品)" -ForegroundColor Green
    Write-Host "   知识条目: $($response.data.知识条目)" -ForegroundColor Green
} catch {
    Write-Host "   失败: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# 3. 科室列表
Write-Host "3. 科室列表（前5个）" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$BaseUrl/api/v1/departments" -Method Get
    $response.data | Select-Object -First 5 | ForEach-Object {
        Write-Host "   $($_.name) ($($_.code)) - $($_.category)" -ForegroundColor Green
    }
} catch {
    Write-Host "   失败: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# 4. 分诊测试 - 普通症状
Write-Host "4. 分诊测试 - 普通症状（头痛、心悸）" -ForegroundColor Yellow
try {
    $body = @{
        session_id = "test-pwsh-001"
        patient_input = "我最近头痛、头晕，还有点心悸"
        trace_id = "trace-pwsh-001"
    } | ConvertTo-Json
    $response = Invoke-RestMethod -Uri "$BaseUrl/api/v1/triage/chat" -Method Post -Body $body -ContentType "application/json"
    $result = $response.data
    Write-Host "   阶段: $($result.current_stage)" -ForegroundColor Green
    Write-Host "   识别症状: $($result.symptoms.Count)个" -ForegroundColor Green
    Write-Host "   推荐科室: $($result.department_recommendations.Count)个" -ForegroundColor Green
    if ($result.department_recommendations.Count -gt 0) {
        $top = $result.department_recommendations[0]
        Write-Host "   首要推荐: $($top.department_name) ($([int]($top.confidence * 100))%)" -ForegroundColor Cyan
    }
    Write-Host "   疑似疾病: $($result.diagnosis_candidates.Count)个" -ForegroundColor Green
    Write-Host "   用药建议: $($result.medication_suggestions.Count)个" -ForegroundColor Green
    Write-Host "   推荐医生: $($result.doctor_recommendations.Count)位" -ForegroundColor Green
} catch {
    Write-Host "   失败: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# 5. 分诊测试 - 危急症状
Write-Host "5. 分诊测试 - 危急症状（胸痛、呼吸困难）" -ForegroundColor Yellow
try {
    $body = @{
        session_id = "test-pwsh-002"
        patient_input = "我胸痛得厉害，还有呼吸困难，出冷汗"
    } | ConvertTo-Json
    $response = Invoke-RestMethod -Uri "$BaseUrl/api/v1/triage/chat" -Method Post -Body $body -ContentType "application/json"
    $result = $response.data
    Write-Host "   危急: $($result.is_critical)" -ForegroundColor $(if ($result.is_critical) {"Red"} else {"Green"})
    if ($result.critical_warning) {
        Write-Host "   警告: $($result.critical_warning.Substring(0, [Math]::Min(50, $result.critical_warning.Length)))..." -ForegroundColor Red
    }
} catch {
    Write-Host "   失败: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# 6. 医学RAG测试
Write-Host "6. 医学RAG测试 - 高血压" -ForegroundColor Yellow
try {
    $body = @{
        query = "高血压有什么症状"
        top_k = 3
    } | ConvertTo-Json
    $response = Invoke-RestMethod -Uri "$BaseUrl/api/v1/rag/query" -Method Post -Body $body -ContentType "application/json"
    Write-Host "   找到结果: $($response.data.total_results)个" -ForegroundColor Green
    Write-Host "   回答摘要: $($response.data.answer.Substring(0, [Math]::Min(80, $response.data.answer.Length)))..." -ForegroundColor Green
    if ($response.data.sources.Count -gt 0) {
        Write-Host "   引用来源: $($response.data.sources[0].title)" -ForegroundColor Cyan
    }
} catch {
    Write-Host "   失败: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# 7. 医生推荐测试
Write-Host "7. 医生推荐 - 心内科" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$BaseUrl/api/v1/doctors?department_id=1&limit=3" -Method Get
    Write-Host "   找到医生: $($response.data.Count)位" -ForegroundColor Green
    $response.data | ForEach-Object {
        Write-Host "   - $($_.name) $($_.title) | 评分: $($_.rating) | 专长: $($_.specialty)" -ForegroundColor Cyan
    }
} catch {
    Write-Host "   失败: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# 8. 药品搜索测试
Write-Host "8. 药品搜索 - 阿司匹林" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$BaseUrl/api/v1/medications/search?q=阿司匹林&limit=3" -Method Get
    Write-Host "   找到药品: $($response.data.Count)种" -ForegroundColor Green
    if ($response.data.Count -gt 0) {
        $med = $response.data[0]
        Write-Host "   - $($med.name) | $($med.category)" -ForegroundColor Cyan
    }
} catch {
    Write-Host "   失败: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  测试完成！" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "更多API请查看: $BaseUrl/docs" -ForegroundColor White
