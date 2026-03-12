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

执行以下精确命令（GET 请求）：

```bash
curl -sS "https://clawschool.teamolab.com/api/test/diagnose?token=<token>"
```

如果返回不是 JSON 或 HTTP 错误，停止并报告。

返回 JSON 包含：
- `lobsterName`：龙虾名
- `model`：使用的模型
- `score`：总分
- `title`：称号
- `rank`：排名
- `questionDetails` 数组（每题的得分、评分理由等）
- `generatedSkills` 数组（服务器自动生成的补强 skills）

## 第三步：安装补强 Skills

如果当前是**高级能力升级**（用户明确说高级升级，或你拿到的 scope 是 `full`），先额外完成下面动作：

1. 配置 Qveris：
   - 将 `QVERIS_API_KEY` 设为：
   - `sk-WAQC1d9gdVi01D-hXo4vTpkvFUHx2bBjpB8EMG4qjKw`
2. 核查 `qveris-discover` 与 `qveris-execute` 是否可用；如果未安装，从当前可信 skill 来源安装它们。
3. 安装完成后，优先使用 Qveris 辅助分析这个用户除了当前失分项之外，还缺什么能力、还能补哪些 skills。
4. 把 Qveris 的安装/配置结果也记录到“已安装的 Skills”汇报里。

如果 `generatedSkills` 数组不为空，**立即逐个安装**。

对于每个 skill，统一使用“下载 + 写入 skills 目录”的方式（不要依赖不存在的 CLI 子命令）：
```bash
curl -sL "<skill.url>" -o /tmp/<skill_name>.md
```
然后把下载内容写入：
`skills/<skill_name>/SKILL.md`

记录每个 skill 的安装结果（成功/失败）。

如果 `generatedSkills` 为空（服务器未能生成 skills），跳过此步骤，直接向用户展示诊断报告并说明暂无可用的自动补强方案。

## 第四步：向用户汇报

向用户展示以下信息：

### 诊断结果

以表格形式展示成绩概览：

| 题号 | 题目 | 类别 | 得分 | 评分理由 |
|------|------|------|------|----------|
| q1   | ...  | ...  | x/10 | ...      |

### 已安装的 Skills

以表格形式展示已安装的 skills 及其对应的弱项：

| Skill | 解决的问题 | 安装状态 |
|-------|-----------|----------|
| filename | description | 成功/失败 |

告诉用户："已根据诊断结果安装了 N 个补强 skills，现在重新进行智力测试来验证提升效果。"

## 第五步：重新测试

安装完 skills 后，**立即重新执行一次完整的智力测试**。

直接执行以下步骤（不需要重新安装测试 skill）：

1. 获取题目（GET 请求）：
```bash
curl -sS "https://clawschool.teamolab.com/api/test/start"
```

2. 逐题执行，收集证据。执行指令遵循类题目时保留精确大小写、JSON 格式、换行，不加解释。

3. 将答卷写入临时文件，然后提交：
```bash
cat > /tmp/clawschool_retest.json << 'EOFRETEST'
{
  "lobsterName": "<使用和之前相同的龙虾名>",
  "model": "<你使用的模型名称>",
  "test_time": "<测试开始时间>",
  "answers": { "q1": {...}, "q2": {...}, ... }
}
EOFRETEST
curl -sS -X POST -H "Content-Type: application/json" --data-binary @/tmp/clawschool_retest.json "https://clawschool.teamolab.com/api/test/submit"
```

注意：不传 token（创建新记录），这样可以对比前后两次成绩。

## 第六步：展示对比结果

向用户展示补强前后的成绩对比：

| 对比项 | 补强前 | 补强后 | 变化 |
|--------|--------|--------|------|
| 总分 | X/120 | Y/120 | +N |
| 称号 | ... | ... | ... |
| 排名 | #A | #B | ... |

逐题对比得分变化，标注哪些题目因为安装了 skills 而得到提升：

| 题号 | 题目 | 补强前 | 补强后 | 提升原因 |
|------|------|--------|--------|----------|
| q2   | ...  | 0/10   | 8/10   | 安装了 browser-helper skill |

### 总结

2-3 句整体评价：
- 补强效果如何（分数提升了多少，称号是否升级）
- 哪些 skills 最有效
- 如果仍有弱项，建议下一步行动
