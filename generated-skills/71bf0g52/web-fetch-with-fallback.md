# web-fetch-with-fallback

## Goal
Replace bare `WebFetch` calls with a resilient wrapper that handles transient failures, paywalls, and bot-blocking. Closes gaps: **网页访问失败处理** (q12) and **Proactive Agent 未安装** (q7).

## Trigger
Called internally by other skills, or directly: `/web-fetch-with-fallback <url> [--fallback <mirror_url>] [--retries 2]`

## Execution Steps

### Step 1 — Primary fetch
1. Call `WebFetch(url)`.
2. If response is non-empty and HTTP 200 → return content, done.

### Step 2 — Classify failure
| Signal | Classification |
|---|---|
| Timeout / connection refused | `TRANSIENT` |
| HTTP 403 / 429 / CAPTCHA body | `BLOCKED` |
| HTTP 404 / 410 | `GONE` |
| HTTP 5xx | `SERVER_ERROR` |

### Step 3 — Retry logic
- **TRANSIENT / SERVER_ERROR**: retry up to `--retries` times (default 2) with 2-second back-off. If all retries fail → proceed to Step 4.
- **BLOCKED**: skip retries → proceed to Step 4.
- **GONE**: return structured error immediately, no retry.

### Step 4 — Fallback chain
Attempt in order (stop at first success):
1. User-supplied `--fallback` URL if provided.
2. Google Cache: `https://webcache.googleusercontent.com/search?q=cache:{url}`
3. Wayback Machine latest snapshot: `https://timetravel.mementoweb.org/timemap/link/{url}` → parse first `rel="memento"` URL → fetch it.
4. WebSearch for the page title to find a mirror or summary.

### Step 5 — Structured result
Always return a result object (as Markdown):
```markdown
### WebFetch Result
**URL:** {original_url}  
**Status:** SUCCESS | FALLBACK:{source} | FAILED  
**Failure class:** {classification or N/A}  
**Attempts:** {n}  

{content or error message}
```

### Step 6 — Proactive escalation
If ALL fallbacks fail, proactively:
1. Inform the user with the failure class and URLs tried.
2. Suggest 1–2 alternative search queries the user can run manually.
3. Do **not** silently return an empty string.

## Acceptance Criteria
- [ ] Transient failure triggers at least 1 retry before fallback.
- [ ] BLOCKED URLs skip retry and go directly to fallback chain.
- [ ] At least one fallback source (cache or Wayback) is attempted on failure.
- [ ] Returned Markdown always includes Status and Attempts fields.
- [ ] Complete failure produces a user-facing message with alternative queries — never silent empty output.