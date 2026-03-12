# daily-news-digest

## Goal
Reliably fetch, deduplicate, and summarize current-day news across specified topics, then deliver a structured digest. Closes gaps: **定时任务调度** (q9) and **当日新闻整理** (q10).

## Trigger
User says something like: `/daily-news-digest [topic]` or a cron fires this skill.

## Execution Steps

### Step 1 — Resolve today's date
```
currentDate is injected by the system prompt. Record it as TODAY.
```

### Step 2 — Parallel web search
Run **3 concurrent WebSearch calls** with queries:
- `"[topic] news {TODAY}"`
- `"[topic] latest updates {TODAY}"`
- `"[topic] breaking {TODAY}"`

If a query returns 0 results, widen the date window by 1 day and retry once.

### Step 3 — Fetch & parse top URLs
For each unique URL in the combined results (up to 8 URLs):
1. Call `WebFetch` with a 10-second timeout.
2. On HTTP error or timeout → skip and log `SKIP: <url> reason: <error>`.
3. Extract: **headline**, **publish datetime**, **body snippet ≤ 200 words**.

### Step 4 — Deduplicate
Group articles by semantic similarity (same event = keep highest-quality source). Discard items where `publish_datetime < TODAY - 1 day`.

### Step 5 — Summarize & format
Output a Markdown digest:
```
## News Digest — {TODAY}  Topic: {topic}

### 1. {Headline}
**Source:** {domain} | **Time:** {datetime}
{2-sentence summary}

### 2. ...

---
_Skipped URLs: N_
```

### Step 6 — Schedule (optional)
If the user requests a recurring digest, call `CronCreate` with the user-specified interval (default `0 8 * * *` — 08:00 daily) and this skill as the command.

## Acceptance Criteria
- [ ] At least 3 articles retrieved and summarized for any mainstream topic.
- [ ] Each article includes headline, source domain, and datetime.
- [ ] Failed URLs are logged, not silently dropped.
- [ ] Cron schedule created successfully when requested; `CronList` confirms it.
- [ ] No articles older than 48 hours appear in the digest.