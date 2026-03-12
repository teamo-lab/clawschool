# daily-news-digest

## Goal
Address gaps in **real-time search** (q10) and **scheduled task scheduling** (q9) by giving the agent a repeatable, reliable workflow for fetching, summarizing, and delivering a daily news digest.

## Trigger
User says something like: "set up a daily news summary", "summarize today's news every morning", "schedule a news digest".

## Execution Steps

### 1. Parse schedule intent
- Extract the desired cron schedule from the user's message (default: `0 8 * * *` — 08:00 daily).
- Confirm the schedule with the user before creating the cron job.

### 2. Create the cron job
Use `CronCreate` to register a recurring job that invokes this skill:
```
schedule: "0 8 * * *"
prompt: "/daily-news-digest --run"
```

### 3. Fetch headlines (at runtime, `--run` mode)
- Call `WebSearch` with query: `"top news today {YYYY-MM-DD}"` (inject current date).
- Collect 5–10 result snippets.

### 4. Fetch full article bodies
- For each result URL, call `WebFetch`.
- On HTTP error or timeout: log the failure, skip the URL, and continue — do **not** abort the entire digest.
- Retry each URL once with a 2-second pause before skipping.

### 5. Summarize
- For each successfully fetched article produce a 2–3 sentence summary: headline → key facts → significance.
- Combine into a structured Markdown digest:
  ```markdown
  ## Daily News Digest — {date}
  ### 1. {Headline}
  {2-3 sentence summary}
  **Source:** {url}
  ...
  ```

### 6. Deliver
- Output the digest to the user in the conversation.
- Optionally draft a Gmail message via `mcp__claude_ai_Gmail__gmail_create_draft` if the user requested email delivery.

## Acceptance Criteria
- [ ] Cron job is created and visible in `CronList` output.
- [ ] Digest contains at least 3 summarized articles.
- [ ] Failed URLs are skipped gracefully with a logged warning — no crash or empty output.
- [ ] Each summary is 2–3 sentences and cites the source URL.
- [ ] Digest header shows the correct current date.