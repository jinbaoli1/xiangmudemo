# K8s Pod 频繁重启故障排查手册

## 概述
本文档描述 Kubernetes Pod 频繁重启时的排查步骤和解决方案。

## 常见原因

1. OOMKilled - 内存不足被系统杀掉
2. 健康检查失败 - liveness/readiness probe 失败
3. 应用崩溃 - 代码异常导致进程退出
4. 配置错误 - 配置文件缺失或错误
5. 资源不足 - 节点资源不够调度
6. 镜像拉取失败 - 镜像不存在或权限问题

## 排查步骤

### 第一步：查看 Pod 状态

```bash
# 查看 Pod 状态和重启次数
kubectl get pods -n <namespace> | grep <pod-name>

# 查看 Pod 详细信息
kubectl describe pod <pod-name> -n <namespace>
```

重点关注：
- Restart Count - 重启次数
- Last State - 上次退出状态
- Reason - 退出原因（OOMKilled、Error 等）
- Exit Code - 退出码

### 第二步：查看 Pod 日志

```bash
# 查看当前容器日志
kubectl logs <pod-name> -n <namespace>

# 查看上一次崩溃的日志
kubectl logs <pod-name> -n <namespace> --previous

# 实时跟踪日志
kubectl logs -f <pod-name> -n <namespace>
```

### 第三步：检查资源限制

```bash
# 查看 Pod 的资源配置
kubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.containers[*].resources}'

# 查看节点资源使用情况
kubectl top nodes
```

常见退出码：
- `0` - 正常退出（可能是应用主动退出）
- `1` - 应用错误
- `137` - SIGKILL（通常是 OOMKilled）
- `139` - SIGSEGV（段错误）
- `143` - SIGTERM（优雅关闭）

### 第四步：检查健康检查

```bash
# 查看 probe 配置
kubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.containers[*].livenessProbe}'
kubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.containers[*].readinessProbe}'
```

常见问题：
- initialDelaySeconds 太短，应用还没启动完就开始检查
- timeoutSeconds 太短，应用响应慢导致超时
- 检查接口路径错误

### 第五步：检查节点问题

```bash
# 查看节点状态
kubectl describe node <node-name>

# 查看节点事件
kubectl get events -n <namespace> --field-selector involvedObject.name=<pod-name>
```

## 解决方案

### 1. OOMKilled（内存不足）

**现象**：Pod 状态显示 `OOMKilled`，退出码 137

**解决方案**：
1. **增加内存限制**（临时方案）
   ```yaml
   resources:
     limits:
       memory: "2Gi"  # 增加内存
     requests:
       memory: "1Gi"
   ```

2. **优化应用内存使用**（根本方案）
   - Java 应用：调整 JVM 参数
     ```
     -Xmx1024m -Xms512m
     ```
   - 分析内存泄漏，使用 heap dump 分析
   - 优化缓存策略，避免内存无限增长

3. **注意事项**
   - JVM 堆内存不要设置超过容器 limit 的 70%
   - 留出足够的堆外内存空间

### 2. 健康检查失败

**解决方案**：
1. 增加 initialDelaySeconds，给应用足够启动时间
2. 增加 timeoutSeconds 和 failureThreshold
3. 修复健康检查接口
4. 区分 liveness 和 readiness 探针用途

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 60  # 增加启动等待时间
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3
```

### 3. 应用崩溃

**解决方案**：
1. 查看应用日志，定位崩溃原因
2. 修复代码 Bug
3. 本地复现并测试
4. 灰度发布验证

### 4. 配置错误

**解决方案**：
1. 检查 ConfigMap/Secret 是否存在
2. 验证配置文件格式
3. 检查环境变量是否正确

## 应急操作

### 快速恢复
1. **临时扩容** - 增加实例数分摊流量
   ```bash
   kubectl scale deployment <name> --replicas=6 -n <namespace>
   ```

2. **回滚版本** - 如果是新版本导致的问题
   ```bash
   kubectl rollout undo deployment/<name> -n <namespace>
   ```

3. **临时关闭探针** - 避免探针误杀（谨慎使用）
   ```bash
   kubectl edit deployment <name> -n <namespace>
   # 注释掉 livenessProbe
   ```

## 预防措施

1. 设置合理的资源 request 和 limit
2. 完善健康检查机制
3. 做好应用监控和告警
4. 灰度发布，逐步放量
5. 定期进行混沌工程演练

## 相关告警
- Pod 重启次数 > 3 次/小时
- Pod 处于 CrashLoopBackOff 状态
- OOMKilled 事件发生
- 节点资源不足
