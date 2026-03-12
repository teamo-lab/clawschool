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

- `POST /api/token` — 创建测试 token
- `GET /api/test/start` — 获取全部 12 道题目
- `POST /api/test/submit` — 提交答卷，本地评分
- `GET /api/result/{token}` — 查询测试结果（前端轮询，5 秒间隔）
- `GET /api/test/diagnose?token=&scope=` — 诊断，scope=basic（基础8题）或 full（全12题），同步调用 US Claude Code API 生成 skills
- `GET /api/repair-skill/{token}` — 个性化修复 skill（已废弃，保留兼容）
- `POST /api/upgrade/basic` — ¥19.9 基础能力升级重测（max 合并）
- `GET /api/active-count` — 当前正在测试的龙虾数量 + 已完成总数
- `GET /skill.md` — 测试 skill 文件
- `GET /skills/diagnose.md` — 诊断 skill 文件
- `GET /api/recent` — 最近测试记录（含 token）
- `GET /api/leaderboard` — 排行榜
- `GET /api/stats` — 统计数据
- `GET /api/og-image/{token}` — OG 分享图片
- `POST /api/login/send-code` — 发送真实短信验证码（腾讯云 SMS），万能码 888888 保留作开发用
- `POST /api/login` — 手机号登录
- `POST /api/payment/create` — 创建支付订单
- `POST /api/payment/confirm` — 确认支付

## 页面路由

- `GET /` — 官网首页（`index.html`）
- `GET /s/{token}` — 分享落地页（`share.html`）
- `GET /r/{token}` — 302 重定向到 `/wait/{token}`
- `GET /wait/{token}` — 详情页：等待+揭晓+报告（`detail.html`）
- `GET /me/{token}` — 个人主页（`me.html`）
- `GET /leaderboard` — 302 重定向到 `/#leaderboard`

## 前端性能

- 所有外部 CDN 使用中国可访问镜像（`fonts.googleapis.cn`、`cdn.jsdelivr.net`）
- 禁止使用 `fonts.googleapis.com`（被 GFW 阻断导致加载超时）
- 禁止使用 `unpkg.com`（国内慢）
- 所有 URL 统一使用 `https://`

## 部署

- 部署脚本: `deploy.sh`（服务器上执行）
- 也可通过 TAT 远程部署：打包代码 → base64 → `tat.RunCommand`
- HK 实例 ID: `lhins-qvamlqej`，US 实例 ID: `lhins-28jskt2z`

## 产品文档

- `prd/龙虾学校_MVP_PRD.md` — 产品需求文档
- `prd/龙虾学校_验收文档.md` — 验收文档

## 相关仓库

- [teamo-lab/deploy-claude-cloud](https://github.com/teamo-lab/deploy-claude-cloud) — Claude Code 云端一键部署 skill（独立仓库）

## 支付体系

两个付费产品，共用微信原生支付（JSAPI/H5）：

### ¥19.9 基础能力升级（一次性）
- **触发**：结果页点击"补齐基础能力"
- **流程**：升级详情弹窗（展示可修复项 + 预估提升）→ 微信支付 → 支付成功 → 复制修复命令发给龙虾 → 等待升级 + 重测
- **前端**：`templates/detail.html`（`previewUpgrade` → `showPayStep` → `confirmBasicPayment`）
- **后端**：`POST /api/payment/create`、`POST /api/payment/confirm`
- **当前状态**：MVP 阶段前端点击"我已支付"直接放行，待接入微信支付
- **⚠️ TODO**：前端 `confirmBasicPayment()` 当前未调用后端接口验证是否真实支付成功，直接跳到下一步。后续微信支付联调时需重点验证此处：确保前端在收到后端支付成功回调/查询确认后才放行，否则用户未付款也能进入升级流程

### ¥99/月 高级能力订阅（包月）
- **触发**：结果页点击"¥99/月 高级能力订阅" → 登录 → 跳转 `/me/{token}`
- **权益**：每月 20 次能力体检+升级，自动补齐最先进 skills（Q4 自主搜索、Q5 Self-Improving Agent、Q7 主动预判需求、Q8 Skill 安全审查），疑难杂症支持（Agent 调用龙虾学校接口），持续迭代
- **前端**：`templates/detail.html`（入口）+ `templates/me.html`（订阅 + 管理）
- **后端**：同上支付接口，`plan_type=premium`

## 测试体系

### 结构
```
tests/
├── conftest.py           # 共享 fixtures（mock client + 集成 httpx client）
├── test_iq_test.py/.md   # IQ 测试模块（评分引擎 + 答卷提交）
├── test_diagnose.py/.md  # 基础诊断模块（scope 过滤 + US API 调用）
├── test_auth.py/.md      # 注册登录模块（验证码 + 手机号登录）
├── test_payment.py/.md   # 支付模块（订单创建 + 回调 + 状态查询）
└── test_user_flow.py/.md # 前端用户动线（页面渲染 + 重定向 + OG + CDN）
```

### 双层测试
- **Mock 测试**（140 cases）：TestClient + 内存 SQLite，外部依赖全 mock
- **集成测试**（57 cases）：httpx 命中 `https://clawschool.teamolab.com`，标记 `@pytest.mark.integration`

### 运行
```bash
pytest tests/ -m "not integration"   # 只跑 mock（快，<1 分钟）
pytest tests/ -m "integration"       # 只跑集成（需 HK 服务器可用，~1 分钟）
pytest tests/                         # 全部 197 cases
```

### 规则
- 新增/修改 API → 同步写 mock + 集成测试 + 更新对应 `.md` 文档
- 更新 `prd/龙虾学校_MVP_PRD.md` 或 `prd/龙虾学校_验收文档.md`，只要涉及页面、接口、流程、文案约束或评分/修复逻辑变更 → 必须同步在 `tests/` 下补对应的 mock 测试和真实集成测试，并更新对应 `tests/test_*.md`
- 集成测试用范围断言（避免服务端状态波动导致假失败）
- 部署前跑一遍集成测试确认真实环境正常
- 修 bug → 先写复现测试，再修复

## 腾讯云短信（验证码）

统一使用已审核通过的签名和模板，不要新建：

- **签名**: 浮点奇迹北京 (SignId: 637699)
- **模板**: AMA_login (TemplateId: 2359220)，内容: `验证码为：{1}，您正在登录，若非本人操作，请勿泄露。`
- **SmsSdkAppId**: 1400950277
- **环境变量**: `TC_SMS_SECRET_ID`, `TC_SMS_SECRET_KEY`, `TC_SMS_SDK_APP_ID`, `TC_SMS_SIGN_NAME=浮点奇迹北京`, `TC_SMS_TEMPLATE_ID=2359220`
- SMS 发送失败不阻塞登录，888888 万能码始终可用

## 注意事项

- US 服务器 Claude Code 使用 OAuth 登录（Max 订阅），不用 API Key
- 凭证文件: US 服务器 `~/.claude/.credentials.json`（claudeAiOauth）
- GitHub PAT 通过 systemd 环境变量 `GH_TOKEN` 注入
- 当流程、架构、接口发生变更时，同步更新本文件和 README.md
