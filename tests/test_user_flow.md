# 前端用户动线

## 覆盖范围

SSR 页面渲染 + 重定向 + OG 标签 + CDN 合规 + Skill 文件下载 + 统计 API。

## 页面路由

```
用户扫码/点链接
  → /s/{token}   分享落地页（朋友看到的）
  → /r/{token}   302 重定向到 /wait/{token}
  → /wait/{token} 详情页（等待 → 揭晓 → 报告 → 升级）
  → /me/{token}  个人主页（订阅管理）
  → /            首页（排行榜、CTA）
  → /leaderboard 302 重定向到 /#leaderboard
```

## 测试用例

### 首页
- 渲染 200 + 包含「龙虾学校」
- 使用 fonts.googleapis.cn（非 .com）

### 详情页
- 正常渲染 + 包含 token
- 不存在 token → 404
- OG 标签（og:title, og:image, og:url）存在
- OG URLs 全部 https（无 http://）
- 无 GFW 阻断 CDN（fonts.googleapis.com, unpkg.com）
- 包含 IQ 值
- 基础能力升级命令使用 `skills/diagnose.md`，并携带 `scope=basic`
- 模板变量 advanced_qids/basic_qids 正确传入

### 分享页
- 正常渲染 + 不存在 token 404
- OG title 包含 IQ 值
- OG URLs 全部 https

### 个人主页
- 正常渲染 + 不存在 token 404
- 无 GFW 阻断 CDN
- 包含 IQ 值
- premium 订单为 paid 时显示「生效中」，并注入 `PAYMENT_STATUS="paid"`

### 重定向
- /r/{token} → 302 /wait/{token}
- /leaderboard → 302 /#leaderboard

### Skill 文件
- GET /skill.md → 200 + 包含「龙虾学校」
- GET /skills/diagnose.md → 200 + 包含诊断关键词
- 本地域名 `127.0.0.1:3210` 时，`/api/token`、`/skill.md`、`/wait/{token}` 对外链接使用 `http://`

### 计数器 + 统计
- /api/active-count 返回 active + total_done
- 提交后 total_done +1
- /api/stats 返回统计数据

---

## 集成测试（`@pytest.mark.integration`）

命中真实 HK 服务器 `https://clawschool.teamolab.com`。

### 首页
- 渲染 200 + 包含「龙虾学校」
- 无 GFW 阻断 CDN（fonts.googleapis.com, unpkg.com）

### 详情页
| 用例 | 预期 |
|------|------|
| 正常渲染 | 200 + 包含 token |
| 不存在 token | 404 |
| OG 标签 | og:title, og:image, og:url 存在 |
| OG URLs https | 无 http:// |
| CDN 合规 | 无 fonts.googleapis.com / unpkg.com |
| IQ 显示 | 包含 IQ 值 |
| 升级命令 | /skills/diagnose.md + token + `scope=basic` |

### 分享页
| 用例 | 预期 |
|------|------|
| 正常渲染 | 200 |
| 不存在 token | 404 |
| OG title 含 IQ | IQ 值在页面中 |
| OG URLs https | 无 http:// |

### 个人主页
| 用例 | 预期 |
|------|------|
| 正常渲染 | 200 |
| 不存在 token | 404 |
| CDN 合规 | 无 fonts.googleapis.com / unpkg.com |
| IQ 显示 | 包含 IQ 值 |

### 重定向
- /r/{token} → 302 /wait/{token}
- /leaderboard → 302 /#leaderboard

### Skill 文件
- GET /skill.md → 200 + 包含「龙虾学校」
- GET /skills/diagnose.md → 200 + 包含诊断关键词

### 计数器 + 统计
- /api/active-count 返回 active + total_done
- 提交后 total_done 递增
- /api/stats 返回 total_tests >= 1 + avg_iq > 0
