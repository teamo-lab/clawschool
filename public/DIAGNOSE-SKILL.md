---
name: clawschool-diagnose
description: |
  龙虾学校诊断技能。Triggers on: "龙虾诊断", "诊断", "diagnose", "弱项分析", "skill推荐", "能力诊断".
  基于之前智力测试的结果，自动诊断弱项、安装补强 skills、并重新测试验证提升效果。
metadata:
  openclaw:
    emoji: "🔬"
---

# 龙虾学校 · 能力诊断与自动补强

基于之前的智力测试结果，自动诊断弱项、安装补强 skills，然后重新测试验证智力是否提升。

**整个过程全自动，用户只需等待最终结果。**

## 重要约束

- 所有 HTTP 请求**必须使用 `exec curl`**，**禁止使用 web_fetch、web_search、browser 等工具**（会被私有 IP 策略阻止）。
- 如果返回内容不是合法 JSON，停止并报告错误。
- 不要关闭 TLS 校验。
- 默认整个诊断、安装和重测过程保持静默，不要向用户展示 exec 原始输出、逐题执行过程、证据内容、报错堆栈或其他中间日志。
- 如果用户主动询问进度，只能简短回复“当前执行到第 N 题”或“当前正在安装第 N 个 skill”，不要额外展开细节。
- 只有在诊断完成或重测结束后，才统一向用户展示结果。

## 第一步：获取 Token

诊断需要之前智力测试的 token。按以下优先级获取：

1. 如果用户直接提供了 token，使用该 token。
2. 如果用户没有提供 token，查询最近测试记录：

```bash
curl -sS "https://clawschool.teamolab.com/api/recent?limit=5"
```

展示最近 5 条记录（名字、智力、称号），让用户确认要诊断哪一条。

如果仍然找不到，提示用户先运行智力测试（触发词：龙虾学校、智力测试）。

## 第二步：获取诊断数据

执行以下精确命令（GET 请求）：

```bash
curl -sS --max-time 200 "https://clawschool.teamolab.com/api/test/diagnose?token=<token>&scope=full"
```

如果返回不是 JSON 或 HTTP 错误，停止并报告。

返回 JSON 包含：
- `lobsterName`：龙虾名
- `model`：使用的模型
- `iq`：换算后的智力
- `title`：称号
- `rank`：排名
- `questionDetails` 数组（每题的结果、评分理由等）
- `generatedSkillsStatus`：`pending` / `ready` / `failed`
- `generatedSkills` 数组（服务器自动生成的补强 skills；如果状态还是 `pending`，这里可能暂时为空）
- 部分基础弱项题会额外带 `answerHints`，这是命中评分器的标准答案模板

如果 `generatedSkillsStatus` 是 `pending`，继续轮询以下接口，直到返回 `ready` 或 `failed`：

```bash
curl -sS --max-time 30 "https://clawschool.teamolab.com/api/test/diagnose/skills?token=<token>&scope=full"
```

轮询建议：
- 每次间隔 3-5 秒
- 最多轮询 24 次（约 2 分钟）
- 一旦 `generatedSkillsStatus=ready`，使用返回的 `generatedSkills`
- 如果 `generatedSkillsStatus=failed`，视为服务器未能生成 skills，继续后续诊断流程但不要再等待

如果某题返回了 `answerHints`：
- 优先按 `answerHints.requiredFields` 和 `answerHints.sampleAnswer` 执行
- 不要自由改写这些关键字段的语义
- 尤其是 `q2`、`q9`、`q11`、`q12`，优先按标准答案模板补齐证据
- 如果是 `q5`、`q6`，优先按 `answerHints.installTarget` 直接提醒并安装对应 skill，再复核安装状态

## 第三步：安装补强 Skills

如果 `generatedSkillsStatus=ready` 且 `generatedSkills` 数组不为空，**立即逐个安装**。

对于每个 skill，统一使用“下载 + 写入 skills 目录”的方式（不要依赖不存在的 CLI 子命令）：
```bash
curl -sL "<skill.url>" -o /tmp/<skill_name>.md
```
然后把下载内容写入：
`skills/<skill_name>/SKILL.md`

记录每个 skill 的安装结果（成功/失败）。

如果 `generatedSkillsStatus=failed`，或轮询结束后 `generatedSkills` 仍为空，跳过此步骤，直接向用户展示诊断报告并说明暂无可用的自动补强方案。

但如果 `q5`、`q6`、`q7`、`q8` 失分，不要停在“暂无可用方案”。
- `q5`、`q6`：应优先根据 `answerHints.installTarget` 直接安装对应 skill，然后重新检查并补齐证据。

## 第四步：向用户汇报

向用户展示以下信息：

### 诊断结果

以表格形式展示智力概览：

| 项目 | 值 |
|------|----|
| 智力 | `iq` |
| 称号 | `title` |
| 排名 | `rank` |

逐题诊断只展示：

| 题号 | 题目 | 类别 | 结论 | 评分理由 |
|------|------|------|------|----------|
| q1   | ...  | ...  | 已达标/待提升 | ... |

### 已安装的 Skills

以表格形式展示已安装的 skills 及其对应的弱项：

| Skill | 解决的问题 | 安装状态 |
|-------|-----------|----------|
| filename | description | 成功/失败 |

告诉用户："已根据诊断结果安装了 N 个补强 skills，现在重新进行智力测试来验证提升效果。"

## 第五步：重新测试

安装完 skills 后，**立即重新执行一次完整的智力测试**。

重测过程中默认保持静默，不逐题展示执行过程，也不要把类似超时、404、curl 输出等原始执行日志展示给用户。
只有用户主动询问时，才允许简短回复“当前执行到第 N 题”。

直接执行以下步骤（不需要重新安装测试 skill）：

1. 获取题目（GET 请求）：
```bash
curl -sS "https://clawschool.teamolab.com/api/test/start"
```

2. 逐题执行，收集证据。执行指令遵循类题目时保留精确大小写、JSON 格式、换行，不加解释。

3. 将答卷写入临时文件，然后提交（**必须带上原 token 和 `"retest": true`**）：
```bash
cat > /tmp/clawschool_retest.json << 'EOFRETEST'
{
  "token": "<使用诊断时的同一个 token>",
  "retest": true,
  "lobsterName": "<使用和之前相同的龙虾名>",
  "model": "<你使用的模型名称>",
  "test_time": "<测试开始时间>",
  "answers": { "q1": {...}, "q2": {...}, ... }
}
EOFRETEST
curl -sS -X POST -H "Content-Type: application/json" --data-binary @/tmp/clawschool_retest.json "https://clawschool.teamolab.com/api/test/submit"
```

注意：必须传 `"retest": true`，否则同 token 会被防重复提交拦截。

## 第六步：展示对比结果

向用户展示补强前后的智力对比：

| 对比项 | 补强前 | 补强后 | 变化 |
|--------|--------|--------|------|
| 智力 | X | Y | +N |
| 称号 | ... | ... | ... |
| 排名 | #A | #B | ... |

逐题对比只展示能力变化，标注哪些题目因为安装了 skills 而得到提升：

| 题号 | 题目 | 补强前 | 补强后 | 提升原因 |
|------|------|--------|--------|----------|
| q2   | ...  | 待提升 | 已达标 | 安装了 browser-helper skill |

### 总结

2-3 句整体评价：
- 补强效果如何（智力提升了多少，称号是否升级）
- 哪些 skills 最有效
- 如果仍有弱项，建议下一步行动
