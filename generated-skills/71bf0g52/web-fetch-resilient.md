# web-fetch-resilient

## 目标

提供健壮的网页抓取封装，覆盖重试、降级、结构化错误报告全流程，将当前「部分容错」（q12, 6/10）提升至满分水准。

## 使用方式

```
/web-fetch-resilient <url_or_urls> [max_retries?] [fallback_search?]
```

- `url_or_urls`：单个 URL 或逗号分隔的多个 URL
- `max_retries`：最大重试次数（默认 2）
- `fallback_search`：抓取彻底失败时的备用搜索关键词（可选）

## 执行步骤

### Step 1 — 预检

对每个 URL：
- 检查是否为有效 HTTP/HTTPS URL，否则立即标记 `INVALID_URL` 并跳过
- 不修改或猜测用户未提供的 URL

### Step 2 — 带重试的抓取

```
尝试 WebFetch(url)
  成功 → 进入 Step 3
  失败 → 等待 1s → 重试（最多 max_retries 次）
  全部失败 → 记录错误码 / 错误信息 → 进入 Step 4
```

错误分类：

| 错误类型 | 标签 | 处理策略 |
|----------|------|----------|
| HTTP 4xx | `CLIENT_ERROR` | 不重试，直接降级 |
| HTTP 5xx | `SERVER_ERROR` | 重试 |
| 超时 | `TIMEOUT` | 重试 |
| DNS / 网络 | `NETWORK_ERROR` | 重试 |
| 内容为空 | `EMPTY_CONTENT` | 不重试，直接降级 |

### Step 3 — 内容提取

成功抓取后：
- 提取正文（跳过导航、广告、页脚）
- 截断至前 1500 字，附加 `[内容已截断]` 标注
- 记录实际字符数

### Step 4 — 降级 / Fallback

若 URL 抓取失败且提供了 `fallback_search`：

```
WebSearch(fallback_search) → 取前 3 条结果摘要作为替代内容
标注：[原始 URL 不可达，以下内容来自搜索降级]
```

若无 `fallback_search`：标注 `[内容不可用]`，继续。

### Step 5 — 结构化报告

```markdown
## Web Fetch Report

### 成功 (X/Y)
- ✅ https://example.com — 1234 字符

### 失败 (Y-X/Y)
- ❌ https://bad-url.com — TIMEOUT (重试 2 次)
  降级：[搜索结果摘要 或 内容不可用]

### 汇总内容
[各成功/降级内容正文]
```

## 验收标准

| 场景 | 期望结果 |
|------|----------|
| URL 全部成功 | 输出所有正文，报告 `成功 Y/Y` |
| 单 URL 失败，有 fallback | 降级到搜索，标注来源变更 |
| 单 URL 失败，无 fallback | 标注 `[内容不可用]`，不崩溃 |
| HTTP 4xx | 不触发重试，立即降级 |
| 多 URL 混合成败 | 成功/失败分组输出，不漏报 |
| 无效 URL | 预检阶段拦截，不调用 WebFetch |