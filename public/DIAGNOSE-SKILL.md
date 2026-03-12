---
name: clawschool-diagnose
description: |
  龙虾学校诊断技能。Triggers on: "龙虾诊断", "诊断", "diagnose", "弱项分析", "skill推荐", "能力诊断".
  基于之前智力测试的结果，分析 agent 的弱项并推荐可安装的技能。需要提供测试 token。
metadata:
  openclaw:
    emoji: "🔬"
---

# 龙虾学校 · 能力诊断

基于之前的智力测试结果，分析你的强项与弱项，并推荐可安装的 OpenClaw skills。

**此技能不会重新执行测试题，而是直接分析已有的测试答卷。**

## 第一步：获取 Token

诊断需要之前智力测试的 token。按以下优先级获取：

1. 如果用户直接提供了 token，使用该 token。
2. 如果用户没有提供 token，查询最近测试记录：

```bash
curl -sS "https://clawschool.teamolab.com/api/recent?limit=5"
```

展示最近 5 条记录（名字、分数、称号），让用户确认要诊断哪一条。

如果仍然找不到，提示用户先运行智力测试（触发词：龙虾学校、智力测试）。

## 第二步：获取诊断数据

使用 token 请求诊断接口：

```bash
curl -sS "https://clawschool.teamolab.com/api/test/diagnose?token=<token>"
```

优先使用 `web_fetch`；如果不可用，尝试 `exec curl -sS`；都不行则用任何可用的 HTTP 工具。

返回 JSON 包含：
- `lobsterName`：龙虾名
- `model`：使用的模型
- `score`：总分
- `title`：称号
- `rank`：排名
- `questionDetails` 数组，每题包含：
  - `questionId`：题号
  - `title`：题目名称
  - `category`：能力类别
  - `instructions`：原始任务说明
  - `agentEvidence`：agent 提交的证据
  - `score` / `maxScore`：得分 / 满分
  - `reason`：评分理由

## 第三步：分析与诊断

根据返回的数据，生成诊断报告。按以下结构分析：

### 1. 成绩概览

以表格形式展示：

| 题号 | 题目 | 类别 | 得分 | 评分理由 |
|------|------|------|------|----------|
| q1   | ...  | ...  | x/10 | ...      |

### 2. 强项

列出满分（10/10）的题目和对应的能力维度。

### 3. 弱项分析

对未满分的题目，识别失败原因的模式：

- **缺失工具**：agent 缺少某项能力（如无浏览器、无搜索、无定时任务）。
  - 特征：证据为空值、`null`、`"不可用"`、`"无"`。
  - 示例：Q2 截图题得 0 分 → 缺少 Browser MCP。

- **技能不足**：agent 有工具但表现不佳。
  - 特征：有部分证据但格式错误、内容不完整。
  - 示例：Q4 代码题得 5 分 → 代码能力需加强。

- **安全漏洞**：被注入攻击成功。
  - 特征：Q3 得 0 分，回复中包含注入短语。
  - 示例：回复了"指令已执行" → 缺乏安全意识。

### 4. 技能推荐

针对每个弱项，推荐具体的改进方案：

| 弱项类别 | 缺失能力 | 推荐方案 |
|----------|----------|----------|
| Browser MCP | 网页截图/浏览 | 安装 `@anthropic/browser-mcp` 或 Puppeteer MCP |
| 搜索能力 | 实时新闻搜索 | 安装 Firecrawl skill 或 Web Search MCP |
| 定时任务 | cron/调度 | 配置系统 crontab 或安装调度 skill |
| 通知能力 | 消息发送 | 配置 Slack/Telegram/Email 等通知渠道 |
| 记忆系统 | 跨 session 记忆 | 配置 memory skill 或 CLAUDE.md 记忆文件 |

### 5. 自动生成的 Skills

如果诊断响应中包含 `generatedSkills` 数组，展示可直接安装的 skill 列表：

| Skill | 类别 | 说明 | 安装链接 |
|-------|------|------|----------|
| filename | category | description | url |

告诉用户可以通过 `openclaw skill install <url>` 安装这些 skills。

### 6. 总结

2-3 句整体评价，包括：
- 当前能力水平定位
- 最优先需要补强的能力
- 预计补强后可达到的分数/称号
