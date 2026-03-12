# proactive-agent

## Goal
Enable the agent to autonomously gather, synthesize, and deliver timely information (e.g., daily news, market data, project status) on a recurring schedule without manual prompting.

## Trigger
User says: "每天给我整理新闻", "schedule a daily digest", "set up a recurring report", or uses `/loop`.

## Execution Steps

### 1. Parse the request
- Extract: **topic** (e.g., "AI news"), **frequency** (e.g., `daily @ 08:00`), **output channel** (reply / email draft / file).
- Confirm schedule with user before creating the cron.

### 2. Register the cron job
```
CronCreate  interval=<parsed_cron_expression>  prompt="<assembled research prompt>"
```
Store the returned cron ID so it can be managed later.

### 3. Research step (runs each cycle)
1. Use `WebSearch` with targeted queries (e.g., `"AI" after:<yesterday_date>`).
2. Fetch up to 5 top result URLs via `WebFetch`; skip any that return non-2xx.
3. On fetch failure: log the URL as unavailable, continue with remaining sources — never abort the whole run.
4. Deduplicate stories by URL and headline similarity.

### 4. Synthesize digest
```
## Daily Digest — <YYYY-MM-DD>
### Top Stories
1. **<Headline>** — <one-sentence summary> ([source](<url>))
…
### Trending Topics
- …
```

### 5. Deliver output
- If channel = email → `mcp__claude_ai_Gmail__gmail_create_draft` with digest as body.
- Otherwise → respond directly in chat.

### 6. Error handling
| Scenario | Action |
|---|---|
| All fetches fail | Report "No sources reachable" and skip cycle — do NOT fabricate news |
| Search returns 0 results | Broaden query, retry once with wider date range |
| Cron missed | Log missed run; do not double-run on next cycle |

## Acceptance Criteria
- [ ] Cron job created and listed in `CronList` after setup.
- [ ] Digest contains ≥ 3 stories from real fetched sources (no hallucinated URLs).
- [ ] Individual URL fetch failures do not crash the pipeline.
- [ ] Digest delivered to correct output channel.
- [ ] User can cancel via `CronDelete <id>` and agent confirms deletion.