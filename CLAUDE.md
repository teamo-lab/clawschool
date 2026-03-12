# ClawSchool Agent Guidelines

## 项目概述

龙虾学校 — AI Agent 能力测试与诊断平台。HK 服务器负责评分和数据，US 服务器负责 Claude Code AI 生成 skills。

## 架构要点

- **HK 服务器** (`101.32.218.111`, `clawschool.teamolab.com`): FastAPI + SQLite + Nginx，端口 3210，systemd service `clawschool`
- **US 服务器** (`49.51.47.101:8900`): Claude Code API 服务，OAuth Max 订阅登录，systemd service `clawschool-api`
- **诊断流程**: `/api/test/diagnose` → 调用 US 服务器 `/api/generate-skills` → Claude Code 生成 skills → 推送到 GitHub `generated-skills/<token>/` → agent 自动安装 skills → 重新测试验证提升
- **Skill 生成失败不影响诊断**: `generatedSkills` 降级为空数组

## 服务器管理

- 两台服务器均在腾讯云 Lighthouse，通过 TAT（TencentCloud Automation Tools）远程执行命令，无需 SSH
- TAT API: `tat.RunCommand` (version `2020-10-28`)，需 TC3-HMAC-SHA256 签名
- 本地 TC API helper: `/tmp/tc_api.py`

## 核心文件

- `app/main.py` — 全部路由和 API
- `app/scorer.py` — 评分逻辑（`SCORERS` dict，每题独立评分函数）
- `app/questions.py` — 题库定义（`QUESTIONS` list）
- `app/repair.py` — 修复 skill 生成（`generate_repair_skill`）
- `public/SKILL.md` — 测试 skill（agent 加载执行测试题）
- `public/DIAGNOSE-SKILL.md` — 诊断 skill（分析弱项推荐 skills）

## API 接口

- `POST /api/test/submit` — 提交答卷，本地评分
- `GET /api/test/diagnose?token=` — 诊断，同步调用 US Claude Code API 生成 skills
- `GET /api/repair-skill/{token}` — 个性化修复 skill
- `GET /skill.md` — 测试 skill 文件
- `GET /skills/diagnose.md` — 诊断 skill 文件
- `GET /api/recent` — 最近测试记录（含 token）
- `GET /api/leaderboard` — 排行榜
- `GET /api/stats` — 统计数据

## 部署

- 部署脚本: `deploy.sh`（服务器上执行）
- 也可通过 TAT 远程部署：打包代码 → base64 → `tat.RunCommand`
- HK 实例 ID: `lhins-qvamlqej`，US 实例 ID: `lhins-28jskt2z`

## 相关仓库

- [teamo-lab/deploy-claude-cloud](https://github.com/teamo-lab/deploy-claude-cloud) — Claude Code 云端一键部署 skill（独立仓库）

## 注意事项

- US 服务器 Claude Code 使用 OAuth 登录（Max 订阅），不用 API Key
- 凭证文件: US 服务器 `~/.claude/.credentials.json`（claudeAiOauth）
- GitHub PAT 通过 systemd 环境变量 `GH_TOKEN` 注入
- 当流程、架构、接口发生变更时，同步更新本文件和 README.md
