#!/bin/bash
#
# Commerce Copilot - API 测试脚本
# 使用方法：bash test_curls.sh
# 注意：启动服务后再运行：cd app && uvicorn main:app --port 8000
#

BASE_URL="http://localhost:8000"
USER_ID="user_001"

echo "========================================"
echo "Commerce Copilot API 测试"
echo "========================================"

# 1. 健康检查
echo ""
echo "[1/10] 健康检查"
curl -s "$BASE_URL/api/health" | python -m json.tool 2>/dev/null || curl -s "$BASE_URL/api/health"
echo ""

# 2. 系统统计
echo ""
echo "[2/10] 系统统计"
curl -s "$BASE_URL/api/stats" | python -m json.tool 2>/dev/null || curl -s "$BASE_URL/api/stats"
echo ""

# 3. 商品搜索
echo ""
echo "[3/10] 商品搜索 - 无线耳机"
curl -s "$BASE_URL/api/products?q=无线耳机&page_size=3" | python -m json.tool 2>/dev/null || curl -s "$BASE_URL/api/products?q=无线耳机&page_size=3"
echo ""

# 4. 热门商品
echo ""
echo "[4/10] 热门商品"
curl -s "$BASE_URL/api/products/hot?limit=5" | python -m json.tool 2>/dev/null || curl -s "$BASE_URL/api/products/hot?limit=5"
echo ""

# 5. 非流式对话 - 商品导购
echo ""
echo "[5/10] 非流式对话 - 商品导购"
curl -s -X POST "$BASE_URL/api/chat" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $USER_ID" \
  -d '{"message": "推荐一款性价比高的无线耳机", "conversation_id": "test_conv_001"}' \
  | python -m json.tool 2>/dev/null || echo "(需要python格式化)"
echo ""

# 6. 非流式对话 - 订单查询
echo ""
echo "[6/10] 非流式对话 - 订单查询"
curl -s -X POST "$BASE_URL/api/chat" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $USER_ID" \
  -d '{"message": "我的订单", "conversation_id": "test_conv_002"}' \
  | python -m json.tool 2>/dev/null || echo "(需要python格式化)"
echo ""

# 7. 非流式对话 - 政策QA
echo ""
echo "[7/10] 非流式对话 - 政策QA"
curl -s -X POST "$BASE_URL/api/chat" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $USER_ID" \
  -d '{"message": "七天无理由退货政策是什么", "conversation_id": "test_conv_003"}' \
  | python -m json.tool 2>/dev/null || echo "(需要python格式化)"
echo ""

# 8. 非流式对话 - 闲聊
echo ""
echo "[8/10] 非流式对话 - 闲聊"
curl -s -X POST "$BASE_URL/api/chat" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $USER_ID" \
  -d '{"message": "你好", "conversation_id": "test_conv_004"}' \
  | python -m json.tool 2>/dev/null || echo "(需要python格式化)"
echo ""

# 9. 非流式对话 - 人工接管
echo ""
echo "[9/10] 非流式对话 - 人工接管"
curl -s -X POST "$BASE_URL/api/chat" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $USER_ID" \
  -d '{"message": "转人工客服", "conversation_id": "test_conv_005"}' \
  | python -m json.tool 2>/dev/null || echo "(需要python格式化)"
echo ""

# 10. SSE流式对话（只输出前几行）
echo ""
echo "[10/10] SSE流式对话（输出前20行）"
curl -s -N -X POST "$BASE_URL/api/chat/stream" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $USER_ID" \
  -d '{"message": "推荐一款手机", "conversation_id": "test_stream_001"}' \
  | head -20
echo ""

echo ""
echo "========================================"
echo "测试完成！"
echo "========================================"
