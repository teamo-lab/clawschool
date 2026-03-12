# web-fetch-resilient

## Goal
Close the **web scraping error-handling** gap (q12) by wrapping `WebFetch` in a standardized retry-and-fallback pattern that any other skill can call.

## Trigger
Any skill or workflow that needs to fetch a URL where partial failure is unacceptable. Also triggered directly when the user says: "fetch this page", "scrape this URL", "get the content of".

## Execution Steps

### 1. Receive input
- Accept one or more URLs (array or single string).
- Accept optional `max_retries` (default: 2) and `timeout_ms` (default: 10000).

### 2. Fetch with retry loop
For each URL:
```
attempt = 0
while attempt <= max_retries:
    result = WebFetch(url)
    if result.ok:
        break
    attempt += 1
    wait 2^attempt seconds  # exponential back-off: 2s, 4s
if not result.ok:
    mark URL as FAILED
```

### 3. Classify failures
| HTTP Status / Error | Classification | Action |
|---------------------|---------------|--------|
| 404 | Permanent | Skip immediately, no retry |
| 429 / 503 | Transient | Retry with back-off |
| Timeout | Transient | Retry with back-off |
| 403 / 401 | Auth error | Skip, report to user |
| DNS / network error | Transient | Retry once |

### 4. Fallback: search-based recovery
- For each FAILED URL, extract the page title or domain.
- Run `WebSearch` with query: `site:{domain} {title keywords}`.
- If a matching result is found, attempt `WebFetch` on the search result URL.
- Mark the final result as `RECOVERED_VIA_SEARCH` if successful.

### 5. Return structured report
```markdown
## Fetch Results
| URL | Status | Notes |
|-----|--------|-------|
| https://... | OK | 1842 chars fetched |
| https://... | FAILED | 404 — skipped |
| https://... | RECOVERED_VIA_SEARCH | fallback URL used |
```
- Attach fetched content for all OK / RECOVERED URLs.
- List all FAILED URLs with their error classification.

### 6. Caller contract
- Always return at least the structured report even if all URLs fail.
- Never throw an unhandled exception or return empty output.

## Acceptance Criteria
- [ ] Transient errors (429, timeout) trigger exponential back-off retry.
- [ ] Permanent errors (404, 403) are skipped immediately without wasted retries.
- [ ] At least one fallback via `WebSearch` is attempted for each FAILED URL.
- [ ] A structured Markdown report is always returned, even on total failure.
- [ ] Successfully fetched content is passed back to the calling workflow intact.
- [ ] No silent failures — every URL has an explicit OK / FAILED / RECOVERED status.