---
name: service-diagnosis
description: 当用户询问服务是否异常、服务健康状况、服务诊断、或提到具体服务名称并询问其状态时，使用此skill调用xray-ai诊断API分析服务风险
allowed-tools: ["Bash"]
user-invocable: true
---

# 服务诊断 Skill

当用户询问某个服务是否存在异常、服务健康状况、或服务诊断时，使用此 skill。

## 触发条件

- 用户询问服务是否有异常
- 用户询问服务健康状况
- 用户要求诊断某个服务
- 用户询问服务风险分析

## 执行步骤

### 1. 提取参数

从用户消息中提取：
- **服务名称**（必需）：用户提到的服务名
- **时间范围**（可选）：
  - 如果用户未指定时间，默认使用最近 1 小时
  - 如果用户指定了时间范围，解析为 "YYYY-MM-DD HH:MM:SS" 格式

### 2. 调用诊断脚本

使用 Bash 工具执行诊断脚本：

```bash
# 默认最近 1 小时
python3 ~/.claude/skills/service-diagnosis/scripts/diagnose.py "服务名称"

# 或指定时间范围
python3 ~/.claude/skills/service-diagnosis/scripts/diagnose.py "服务名称" "2026-02-26 22:00:01" "2026-02-26 23:00:01"
```

### 3. 分析结果并生成报告

根据脚本返回的 JSON 数据，生成简洁易读的诊断报告。

#### 报告结构

报告应该包含以下部分：

1. **总体评估**：一句话概括服务健康状况
2. **风险列表**：列出发现的问题和风险，按严重程度排序
3. **建议**：针对每个风险提供具体的优化建议

#### 报告格式要求

- 使用简洁的中文描述
- 对于每个风险项，包含：
  - 严重程度（严重/警告/提示）
  - 问题描述
  - 影响范围（机房、接口等）
  - 异常时段（从 summary 字段提取）
- 如果是弱依赖导致的问题，明确说明"未影响服务可用性"
- 提供可操作的建议（如扩容、优化等）

#### 数据解析说明

从 JSON 响应中提取关键信息：
- `data.riskAnalysis[]` - 风险分析列表
- `category` - 风险类别（如"依赖风险"）
- `riskMetrics[].items[]` - 具体的风险指标
- `abnormalStatus` - 异常严重程度（CRITICAL/WARNING/INFO）
- `summary` - 问题摘要（包含时间和数值）
- `labels` - 相关标签（服务名、接口名、机房等）

#### 示例报告格式

```
您的服务 [服务名] 在 [时间范围] 运行整体正常，但存在部分稳定性风险：

1. [严重] RPC 下游可用性问题
   - 接口 resourceQuery 调用 riskcommunity-marketconcatimgdet-v1 时成功率下跌
   - 机房：qcsh5-new
   - 异常时段：2026-02-26 20:30:00 ~ 20:37:00
   - 建议：检查下游服务状态，考虑添加熔断机制

2. [警告] 下游服务延迟偏高
   - 调用下游 A 的延迟与服务自身延迟趋势相符
   - 未影响服务可用性（弱依赖）
   - 建议：如需优化性能可关注该服务

总体建议：
- 优先处理严重级别的问题
- 对关键下游服务添加监控和告警
- 考虑实施降级和熔断策略
```

### 4. 联动指标查询（如果检测到异常）

**重要：** 当诊断结果显示存在异常时，应该联动调用 metric-query skill 查询详细的指标数据，提供更全面的分析。

#### 联动触发条件

如果 `data.riskAnalysis` 不为空（检测到异常），根据异常类型调用 metric-query：

#### 异常类型与指标映射

| 异常类型 | diagnosisMetricType | 应查询的指标 |
|---------|---------------------|-------------|
| RPC客户端成功率异常 | RPC_CLIENT_SUCCESS_RATE | ["RPC_CLIENT_SUCCESS_RATE", "RPC_CLIENT_QPS", "RPC_CLIENT_TIME"] |
| RPC服务端成功率异常 | RPC_SERVICE_SUCCESS_RATE | ["RPC_SERVICE_SUCCESS_RATE", "RPC_SERVICE_QPS", "RPC_SERVICE_TIME"] |
| CPU使用率异常 | CPU_USAGE | ["CPU_USAGE"] |
| 内存使用率异常 | MEM_USAGE | ["MEM_USAGE"] |
| JVM相关异常 | JVM_* | ["JVM_OLD_GC_COUNT", "JVM_OLD_GC_TIME", "JVM_YOUNG_GC_COUNT"] |

#### 调用方式

使用 Bash 工具调用 metric-query 脚本：

```bash
python3 ~/.claude/skills/metric-query/scripts/query_metric.py '{
  "app": "服务名称",
  "start": "异常开始时间",
  "end": "异常结束时间",
  "metricIds": ["对应的指标ID"],
  "scope": "CLUSTER",
  "groupBys": []
}'
```

#### 综合分析报告

结合诊断结果和指标数据，生成综合报告：

1. **诊断结论**：来自 service-diagnosis 的异常检测结果
2. **指标详情**：来自 metric-query 的详细数据和趋势
3. **关联分析**：将异常时段的指标数据与正常时段对比
4. **深度建议**：基于详细数据提供更精准的优化建议

### 5. 错误处理

如果脚本执行失败或 API 返回错误：
- 检查服务名称是否正确
- 检查网络连接
- 向用户说明具体错误信息
- 建议用户检查服务名称或稍后重试

## 注意事项

- 脚本已自动过滤大数据量字段（outlinerTss、outlinerValues、values、timeStamps）
- 报告应简洁明了，避免技术术语过多
- 优先展示对用户最有价值的信息
- 如果没有发现异常，也要明确告知用户
