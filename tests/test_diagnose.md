# 基础诊断模块

## 覆盖范围

诊断 API（`app/main.py` 中 `/api/test/diagnose`）+ US Claude Code API 调用 + skills 生成容错降级。

## 核心通路

```
答题结果 → GET /api/test/diagnose?token=xxx&scope=basic
  → 从 DB 读取答卷详情
  → 按 scope 过滤题目（basic=8题 / full=12题）
  → POST US:8900/api/generate-skills （携带诊断数据）
  → Claude Code 分析弱项 → 生成 skill .md → 推送 GitHub
  → 返回 skill URL 列表 → 注入 generatedSkills 字段
```

## 测试用例

### scope 参数过滤
| 用例 | scope | 预期题数 | 排除 |
|------|-------|---------|------|
| 默认 | 无/full | 12 | 无 |
| 基础 | basic | 8 | q4, q5, q7, q8 |
| 基础包含所有 BASIC_QIDS | basic | 8 | ADVANCED_QIDS |
| 全量包含所有题 | full | 12 | 无 |

### 诊断响应结构
- 必含字段：token, lobsterName, model, score, iq, title, rank, scope, questionDetails
- questionDetail 子结构：questionId, title, category, instructions, evidenceFormat, agentEvidence, score, maxScore, reason
- agentEvidence 与提交的答卷一致

### US Claude Code API 调用
| 用例 | mock 行为 | 预期 generatedSkills |
|------|----------|---------------------|
| 成功 | 返回 2 个 skills | 长度 2，含 name+url |
| 超时 | TimeoutError | 空数组 [] |
| 连接错误 | ConnectionError | 空数组 [] |
| 无效 JSON | 返回非 JSON | 空数组 [] |

### API payload 验证
- payload 包含 token + diagnosis 对象
- diagnosis 中 questionDetails 数量与 scope 一致
- scope=basic 时 payload 只含 8 题（不含 ADVANCED_QIDS）

### 错误场景
- token 不存在 → 404
- token 状态为 waiting（未完成测试）→ 404
