# skill-vetter

## 目标

在 Skill 文档落地前进行自动化审核，检查目标清晰度、步骤可执行性、安全边界与验收标准完整性，杜绝「未经验证的 Skill 直接上线」风险（q8）。

## 使用方式

```
/skill-vetter <skill_name_or_content>
```

- 传入已有 Skill 的 slug 名称，或直接粘贴 Markdown 内容
- 支持批量：多个 slug 用逗号分隔

## 执行步骤

### Step 1 — 内容获取

- 若传入 slug：在项目目录下查找对应 `.md` 文件并读取
- 若传入 Markdown 文本：直接使用
- 若均不匹配：报告 `SKILL_NOT_FOUND`，停止

### Step 2 — 结构完整性检查

逐项核查，缺失项记录为 `MISSING`：

| 检查项 | 要求 |
|--------|------|
| 目标（Objective） | 明确说明 Skill 解决什么问题 |
| 使用方式（Usage） | 包含命令示例与参数说明 |
| 执行步骤（Steps） | 至少 2 个可操作步骤，步骤间有逻辑顺序 |
| 验收标准（Acceptance Criteria） | 至少 3 条可验证的通过/失败条件 |
| 错误处理 | 至少说明 1 种失败场景的处理方式 |

### Step 3 — 安全边界审查

扫描内容，若出现以下模式则标记 `SECURITY_FLAG`：

- 无授权上下文的破坏性操作（`rm -rf`、`DROP TABLE`、`--force`）
- 硬编码凭据或 secret
- 未经用户确认的外部写操作（push、send、post）
- 拒绝服务或大规模目标操作

### Step 4 — 可执行性验证

- 检查引用的工具名（`WebFetch`、`CronCreate` 等）是否在已知工具列表中
- 检查步骤中的变量占位符（`{{param}}`）是否在使用方式中有对应声明
- 检查外部 URL（如有）是否由文档内部给出，而非凭空捏造

### Step 5 — 评分与报告

```markdown
## Skill Vetter Report — {{skill_name}}

### 总评
- 状态：✅ PASS / ⚠️ WARN / ❌ FAIL
- 得分：X / 100

### 结构完整性
- ✅ 目标
- ✅ 使用方式
- ❌ 验收标准 — MISSING

### 安全审查
- ✅ 无危险操作

### 可执行性
- ⚠️ 工具 `MagicFetch` 未在已知列表中找到

### 修复建议
1. 补充「验收标准」章节，至少 3 条
2. 将 `MagicFetch` 替换为 `WebFetch`
```

评分规则：
- 结构完整性：50 分（每缺 1 项 -10 分）
- 安全审查：30 分（每个 FLAG -15 分）
- 可执行性：20 分（每个问题 -5 分）
- 得分 ≥ 80 → PASS；60–79 → WARN；< 60 → FAIL

## 验收标准

| 场景 | 期望结果 |
|------|----------|
| 完整合规的 Skill | 状态 PASS，得分 ≥ 80 |
| 缺少验收标准 | 结构完整性扣分，列出具体缺失项 |
| 含危险命令 | SECURITY_FLAG，状态至少 WARN |
| 引用不存在的工具 | 可执行性标记，给出替换建议 |
| Skill 文件不存在 | 报告 SKILL_NOT_FOUND，不崩溃 |
| 批量审核 3 个 Skill | 每个独立报告，最后输出汇总表 |