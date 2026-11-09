# Redis 故障排查手册

## 概述
本文档描述 Redis 常见故障的排查步骤和解决方案。

## 常见故障类型

### 1. 缓存命中率骤降

**现象**
- 缓存命中率从正常水平（>90%）下降到 70% 以下
- 后端数据库查询压力增大
- 接口响应时间变长

**排查步骤**
1. 检查 Redis 节点状态
   ```bash
   redis-cli -h host -p port info replication
   ```
2. 确认是否有节点故障或主从切换
3. 查看 Redis 慢日志
   ```bash
   redis-cli slowlog get 20
   ```
4. 检查内存使用情况
   ```bash
   redis-cli info memory
   ```
5. 确认是否有 bigkey 导致内存不足

**解决方案**
- 节点故障：等待自动故障转移完成，或手动提升从节点
- 内存不足：清理过期 key，扩容内存，优化缓存策略
- 缓存击穿：对热点 key 加互斥锁，永不过期
- 缓存雪崩：给 key 过期时间加随机值

### 2. Redis 连接超时

**现象**
- 应用日志大量 Redis 连接超时错误
- 接口响应时间显著增加

**排查步骤**
1. 检查 Redis 进程是否存活
2. 检查网络连通性
   ```bash
   telnet host port
   ```
3. 查看连接数是否达到上限
   ```bash
   redis-cli info clients
   ```
4. 检查 CPU 使用率是否过高
5. 查看是否有阻塞命令（keys *、smembers 等）

**解决方案**
- 连接数满：增加 maxclients 配置，排查连接泄漏
- CPU 高：优化慢查询，使用 scan 代替 keys
- 网络问题：检查网络带宽，考虑同机房部署

### 3. Redis 内存溢出

**现象**
- Redis 进程被 OOM killer 杀掉
- 设置 key 报 OOM 错误

**排查步骤**
1. 查看内存使用情况
   ```bash
   redis-cli info memory
   ```
2. 检查 maxmemory 配置
3. 分析 bigkey 分布
   ```bash
   redis-cli --bigkeys
   ```
4. 检查内存淘汰策略

**解决方案**
- 调整 maxmemory 配置
- 启用合适的淘汰策略（allkeys-lru 推荐）
- 拆分大 key
- 扩容 Redis 集群

## 应急操作

### 快速降级
当 Redis 完全不可用时，可临时关闭缓存，直接访问数据库：
1. 打开应用的缓存降级开关
2. 监控数据库负载
3. Redis 恢复后逐步恢复缓存

### 数据预热
Redis 恢复后，需要预热热点数据：
1. 使用脚本批量导入热点数据
2. 让流量逐步切入，避免缓存击穿

## 相关告警
- Redis 缓存命中率低于 85%
- Redis 连接数超过 80% 阈值
- Redis 内存使用率超过 80%
- Redis 主从同步延迟过大
