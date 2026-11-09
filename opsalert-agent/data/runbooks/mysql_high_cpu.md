# MySQL 高 CPU 故障排查手册

## 概述
本文档描述 MySQL 数据库 CPU 使用率过高时的排查步骤和解决方案。

## 常见原因

1. 慢查询导致 CPU 飙升
2. 大量并发连接
3. 缺少索引或索引失效
4. 死锁和锁等待
5. 排序/分组操作消耗大量 CPU

## 排查步骤

### 第一步：确认 CPU 高的原因

```sql
-- 查看当前运行的所有查询
SHOW PROCESSLIST;

-- 查看更详细的信息
SHOW FULL PROCESSLIST;
```

重点关注：
- Command 为 Query 且 Time 很大的会话
- State 为 Copying to tmp table、Sorting result 等
- Info 中的 SQL 语句

### 第二步：分析慢查询

```sql
-- 查看慢查询是否开启
SHOW VARIABLES LIKE 'slow_query%';

-- 查看慢查询阈值
SHOW VARIABLES LIKE 'long_query_time';

-- 查看慢查询日志路径
SHOW VARIABLES LIKE 'slow_query_log_file';
```

使用 pt-query-digest 分析慢查询日志：
```bash
pt-query-digest /path/to/slow.log
```

### 第三步：检查索引使用情况

```sql
-- 分析 SQL 执行计划
EXPLAIN <SQL语句>;

-- 查看未使用索引的查询
SHOW STATUS LIKE 'Handler_read%';
```

判断标准：
- type 列应为 ref、range 或更好
- Extra 列不应出现 Using filesort、Using temporary
- rows 列扫描行数应尽量少

### 第四步：检查连接数

```sql
-- 查看当前连接数
SHOW STATUS LIKE 'Threads_connected';

-- 查看最大连接数
SHOW VARIABLES LIKE 'max_connections';

-- 查看连接使用情况
SHOW STATUS LIKE 'Max_used_connections';
```

### 第五步：检查锁等待

```sql
-- 查看当前锁等待
SELECT * FROM information_schema.INNODB_LOCK_WAITS;

-- 查看当前持有锁
SELECT * FROM information_schema.INNODB_LOCKS;

-- 查看死锁（最近一次）
SHOW ENGINE INNODB STATUS;
```

## 解决方案

### 1. 紧急处理（CPU 持续 90%+）

1. **Kill 慢查询**
   ```sql
   -- 找出执行时间最长的查询并 kill
   SELECT id, user, host, db, command, time, state, info 
   FROM information_schema.processlist 
   WHERE command = 'Query' AND time > 60 
   ORDER BY time DESC;
   
   KILL <id>;
   ```

2. **临时调大连接数（如果连接不够）**
   ```sql
   SET GLOBAL max_connections = 2000;
   ```

3. **启用查询缓存（如适用）**

### 2. 根本解决

1. **优化慢 SQL**
   - 添加合适的索引
   - 优化 SQL 写法，避免全表扫描
   - 拆分复杂查询
   - 使用覆盖索引

2. **调整配置参数**
   ```ini
   [mysqld]
   innodb_buffer_pool_size = 物理内存的 60%-70%
   innodb_log_file_size = 256M 或更大
   query_cache_size = 64M  # MySQL 5.7 已废弃
   ```

3. **架构优化**
   - 读写分离，读请求走从库
   - 分库分表
   - 增加缓存层（Redis）
   - 使用连接池

## 预防措施

1. 上线 SQL 必须经过 DBA 审核
2. 定期分析慢查询日志
3. 建立索引规范
4. 设置合理的超时时间
5. 做好容量规划和压测

## 回滚方案

如果优化操作导致性能下降：
1. 立即回滚变更的 SQL 或配置
2. 如果是索引变更，删除新添加的索引
3. 如果是配置变更，恢复原有配置
4. 必要时切换到备库

## 相关告警
- CPU 使用率超过 80%
- 慢查询数量突增
- 连接数超过阈值的 80%
- 锁等待时间超过 5 秒
