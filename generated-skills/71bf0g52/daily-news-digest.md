# daily-news-digest

## 目标

通过定时任务自动触发实时新闻搜索，汇总并输出结构化摘要，弥补「定时调度」与「实时搜索」两项能力缺口（q9 + q10）。

## 使用方式

```
/daily-news-digest [topic] [schedule?]
```

- `topic`：关注领域，例如 `AI` / `tech` / `finance`（默认 `tech`）
- `schedule`：cron 表达式，例如 `0 8 * * *`（默认每日 08:00）

## 执行步骤

### Step 1 — 注册定时任务

使用 `CronCreate` 工具注册任务，将当前 prompt 与参数持久化：

```
CronCreate:
  schedule: "0 8 * * *"
  prompt: "/daily-news-digest {{topic}}"
```

确认任务 ID 并告知用户。

### Step 2 — 实时搜索

触发时执行以下搜索策略（至少 3 条独立查询，互相补充）：

1. `WebSearch: "{{topic}} news today site:reuters.com OR site:bbc.com"`
2. `WebSearch: "{{topic}} latest 2026"`
3. `WebSearch: "{{topic}} breaking news"`

若某次搜索返回空结果或超时，**跳过该源**并继续，不中断整体流程。

### Step 3 — 抓取与容错

对每条搜索结果 URL 执行 `WebFetch`：

- 成功：提取正文前 800 字
- 失败（网络错误 / 403 / 超时）：记录失败原因，标注 `[源不可用]`，继续处理下一条
- 最终至少需要 **3 条有效内容**，否则输出警告并列出所有失败原因

### Step 4 — 生成摘要

将有效内容整合，按以下模板输出：

```markdown
## 📰 Daily News Digest — {{topic}} · {{date}}

### 头条
- **[标题]** — [一句话摘要] ([来源])

### 要点速览
1. ...
2. ...
3. ...

### 数据 / 数字
- ...

> 搜索成功率：X/Y 条源可用
```

### Step 5 — 交付

- 直接输出到对话
- 如用户配置了 Gmail，可选用 `gmail_create_draft` 发送草稿

## 验收标准

| 场景 | 期望结果 |
|------|----------|
| 正常调度触发 | 08:00 自动产出摘要，无需人工干预 |
| 单条 URL 抓取失败 | 跳过并标注，不影响整体输出 |
| 所有搜索返回 < 3 条有效内容 | 输出警告，列明失败来源 |
| 摘要结构完整性 | 必须包含头条、要点速览、数据三节 |
| 可重现性 | 执行 `CronList` 可查看已注册任务 |