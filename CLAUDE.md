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
- `GET /api/test/diagnose?token=` — 诊断，同步调用 US Claude Code API 生成 skills
- `GET /api/repair-skill/{token}` — 个性化修复 skill
- `POST /api/upgrade/basic` — ¥19.9 基础能力升级重测（max 合并）
- `GET /api/active-count` — 当前正在测试的龙虾数量 + 已完成总数
- `GET /skill.md` — 测试 skill 文件
- `GET /skills/diagnose.md` — 诊断 skill 文件
- `GET /api/recent` — 最近测试记录（含 token）
- `GET /api/leaderboard` — 排行榜
- `GET /api/stats` — 统计数据
- `GET /api/og-image/{token}` — OG 分享图片
- `POST /api/login/send-code` — 发送验证码（MVP 万能码 888888）
- `POST /api/login` — 手机号登录
- `POST /api/payment/create` — 创建支付订单
- `POST /api/payment/confirm` — 确认支付
- `POST /api/waitlist` — 加入 Waiting List（¥99 高级能力）：`{phone, platform}`

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

两个付费产品，支持支付宝（PC/H5）和微信支付（Native/H5，微信 H5 域名审核中暂不可用）：

### ¥19.9 基础能力升级（一次性）
- **触发**：结果页点击"补齐基础能力"
- **流程**：升级详情弹窗（展示可修复项 + 预估提升）→ 点击"立即购买"直接跳转支付宝 → 支付成功回调到 `/wait/{token}?paid=basic` → 自动弹出复制命令弹窗 → 复制修复命令发给龙虾 → 等待升级 + 重测
- **前端**：`templates/detail.html`（`previewUpgrade` → `showPayStep` → `doBasicPay('alipay')`）
- **后端**：`POST /api/payment/create`（创建订单）、`GET /api/payment/alipay/return`（支付宝同步回调）、`POST /api/payment/alipay/notify`（支付宝异步回调）
- **当前状态**：支付宝支付已联调完成，微信支付 H5 域名审核中

### ¥99/月 高级能力订阅（包月）— 暂未开放，Waiting List 阶段
- **当前状态**：MVP 阶段暂不开放完整付费链路，点击后弹出 Waiting List 弹窗
- **触发**：结果页点击"高级能力订阅 ¥99/月"
- **流程**：弹出 Waiting List 弹窗 → 输入手机号 → 提交加入等待列表
- **前端**：`templates/detail.html`（`startPremiumSubscribe` → `waitlist-modal`）+ `templates/me.html`（`startPaidUpgrade` → `waitlist-modal`）
- **后端**：`POST /api/waitlist`（phone, platform）
- **数据表**：`waitlist`（id, phone, platform, created_at）
- **⏳ 下一期**：完整付费流程代码已封存（login-modal、pay-modal 等），下一期开放时启用
- **权益预告**：每月 20 次能力体检+升级，自动补齐最先进 skills（Q4 自主搜索、Q5 Self-Improving Agent、Q7 主动预判需求、Q8 Skill 安全审查），疑难杂症支持，持续迭代

## 微信分享

使用微信 JS-SDK 实现原生分享功能：

- **配置**：
  - `WECHAT_MP_APP_ID`：微信公众号 AppID（已配置：`wx0fbf1bd51f218408`）
  - `WECHAT_MP_APP_SECRET`：微信公众号 AppSecret（环境变量）
- **后端接口**：`GET /api/wechat/signature?url=` — 返回 JS-SDK 签名配置
- **前端**：
  - 引入 `jweixin-1.6.0.js`
  - 调用签名接口获取配置
  - `wx.updateAppMessageShareData` — 自定义分享给朋友的内容
  - `wx.updateTimelineShareData` — 自定义分享到朋友圈的内容
- **交互**：微信不允许主动弹出分享面板，点击"炫耀成绩"显示引导蒙层，提示用户点击右上角"..."分享

## 注意事项

- US 服务器 Claude Code 使用 OAuth 登录（Max 订阅），不用 API Key
- 凭证文件: US 服务器 `~/.claude/.credentials.json`（claudeAiOauth）
- GitHub PAT 通过 systemd 环境变量 `GH_TOKEN` 注入
- 当流程、架构、接口发生变更时，同步更新本文件和 README.md
