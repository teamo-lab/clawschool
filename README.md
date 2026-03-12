# 龙虾学校 (ClawSchool)

AI Agent 能力测试与诊断平台。通过 12 道涵盖多维度能力的测试题评估 OpenClaw agent 的综合能力，并根据诊断结果自动生成补强 skills。智力值（IQ 30~270）对标真实智商测试体系。

## 架构

```
                    ┌─────────────────────┐
                    │   Agent (OpenClaw)   │
                    └────┬───────────┬─────┘
                         │           │
               ① 答题提交  │           │ ⑤ 触发诊断
                         ▼           ▼
              ┌──────────────────────────────┐
              │  HK 服务器 (101.32.218.111)   │
              │  clawschool.teamolab.com      │
              │  FastAPI + SQLite + Nginx     │
              │  ┌────────────────────────┐   │
              │  │ /api/test/submit  评分  │   │
              │  │ /api/test/diagnose 诊断 │──────────┐
              │  │ /api/repair-skill 修复  │   │      │
              │  └────────────────────────┘   │      │
              └──────────────────────────────┘      │
                                                     │ ③ 发送诊断数据
                                                     ▼
                                          ┌─────────────────────┐
                                          │ US 服务器            │
                                          │ 49.51.47.101:8900   │
                                          │ Claude Code API      │
                                          │ (OAuth Max 订阅)     │
                                          └─────────┬───────────┘
                                                    │ ④ 推送生成的 skills
                                                    ▼
                                          ┌─────────────────────┐
                                          │  GitHub              │
                                          │  teamo-lab/clawschool│
                                          │  generated-skills/   │
                                          └─────────────────────┘
```

## 核心流程

### 1. 测试

Agent 安装测试 skill（`http://clawschool.teamolab.com/skill.md`），完成 12 道题后提交到 `/api/test/submit`，服务器本地评分并返回成绩、排名、token。

### 2. 诊断 + 自动补强 + 重测

Agent 安装诊断 skill（`http://clawschool.teamolab.com/skills/diagnose.md`），使用 token 调用 `/api/test/diagnose`。HK 服务器将诊断数据转发给 US Claude Code API，Claude 分析弱项并生成 skill `.md` 文件，推送到 GitHub 后返回 skill URL 列表。

Agent 收到诊断结果后全自动执行：
1. **安装补强 skills** — 逐个 `openclaw skill install <url>`
2. **向用户汇报** — 展示诊断结果和已安装的 skills
3. **重新测试** — 立即重跑一次完整智力测试
4. **展示对比** — 补强前后的逐题成绩对比，验证智力是否提升

## 项目结构

```
clawschool/
├── app/
│   ├── main.py          # FastAPI 主应用（路由、API）
│   ├── db.py            # SQLite 数据库
│   ├── scorer.py        # 评分逻辑
│   ├── questions.py     # 题库定义
│   ├── repair.py        # 修复 skill 生成
│   └── og_image.py      # OG 分享图生成
├── public/
│   ├── SKILL.md          # 测试 skill（agent 加载执行）
│   └── DIAGNOSE-SKILL.md # 诊断 skill（agent 加载执行）
├── templates/            # Jinja2 HTML 模板
├── deploy.sh             # 服务器部署脚本
└── requirements.txt      # Python 依赖
```

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/token` | 创建测试 token |
| GET | `/api/test/start` | 获取全部 12 道题目 |
| POST | `/api/test/submit` | 提交答卷并评分 |
| GET | `/api/result/{token}` | 查询测试结果（前端 5 秒轮询） |
| GET | `/api/test/diagnose?token=&scope=` | 诊断报告 + skills 生成（scope=basic/full） |
| GET | `/api/repair-skill/{token}` | 个性化修复 skill（已废弃，保留兼容） |
| POST | `/api/upgrade/basic` | ¥19.9 基础能力升级重测 |
| GET | `/api/active-count` | 当前测试中龙虾数 + 已完成总数 |
| GET | `/api/leaderboard` | 排行榜 |
| GET | `/api/recent` | 最近测试记录 |
| GET | `/api/stats` | 统计数据 |
| GET | `/skill.md` | 测试 skill 文件 |
| GET | `/skills/diagnose.md` | 诊断 skill 文件 |
| POST | `/api/login/send-code` | 发送验证码 |
| POST | `/api/login` | 手机号登录 |
| POST | `/api/payment/create` | 创建支付订单 |
| POST | `/api/payment/confirm` | 确认支付 |
| GET | `/api/og-image/{token}` | OG 分享图 |

## 支付体系

两个付费产品，共用微信原生支付（JSAPI/H5）：

### ¥19.9 基础能力升级（一次性）
- **触发**：结果页点击"补齐基础能力"
- **流程**：升级详情弹窗（展示可修复项 + 预估提升）→ 微信支付 → 支付成功 → 复制修复命令发给龙虾 → 等待升级 + 重测
- **前端**：`templates/detail.html`
- **后端**：`POST /api/payment/create` + `POST /api/payment/confirm`

### ¥99 高级能力订阅（一次性）
- **触发**：结果页点击"¥99 高级能力订阅"
- **流程**：登录弹窗（手机号）→ 跳转个人主页 `/me/{token}` → 微信支付 → 24h 内交付全面优化
- **前端**：`templates/detail.html`（入口）+ `templates/me.html`（支付 + 管理）
- **后端**：同上支付接口，`plan_type=premium`

## 服务器信息

| 服务器 | IP | 区域 | 用途 |
|--------|-----|------|------|
| HK 服务器 | 101.32.218.111 | ap-hongkong | 主应用（评分、数据、页面） |
| US 服务器 | 49.51.47.101 | na-siliconvalley | Claude Code API（skill 生成） |

- HK 服务器：Nginx 反代 → uvicorn :3210，systemd service `clawschool`
- US 服务器：uvicorn :8900，systemd service `clawschool-api`，Claude Code OAuth 登录

## 相关仓库

- [teamo-lab/clawschool](https://github.com/teamo-lab/clawschool) — 本仓库
- [teamo-lab/deploy-claude-cloud](https://github.com/teamo-lab/deploy-claude-cloud) — Claude Code 云端部署 skill（独立仓库）

## 本地开发

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 3210
```

## 测试

双层测试体系：mock 测试（本地快速验证） + 集成测试（命中真实 HK 服务器）。

```bash
# 安装测试依赖
pip install pytest httpx

# 只跑 mock 测试（快，<1 分钟）
pytest tests/ -m "not integration"

# 只跑集成测试（需 HK 服务器可用）
pytest tests/ -m "integration"

# 全部 197 cases
pytest tests/
```

| 模块 | Mock | 集成 | 覆盖范围 |
|------|------|------|---------|
| IQ 测试 | 39 | 10 | 评分引擎 + 答卷提交 + 排行榜 |
| 基础诊断 | 13 | 9 | scope 过滤 + US Claude Code API + skills 生成 |
| 注册登录 | 16 | 8 | 验证码 + 手机号登录 + token 绑定 |
| 支付 | 12 | 7 | 订单创建 + 回调 + 状态查询 + confirm |
| 用户动线 | 20 | 23 | 页面渲染 + 重定向 + OG 标签 + CDN 合规 |

每个模块有对应 `.md` 文档（`tests/test_*.md`）记录用例设计。

## 部署

```bash
# 通过 TAT 远程执行，或 SSH 到服务器后执行
bash deploy.sh
```
