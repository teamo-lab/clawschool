# proactive-news-brief

## Goal
A proactive-agent skill that runs on a configurable cron schedule, searches the web for today's top stories on a given topic, handles fetch failures gracefully, and formats results as a Markdown brief.

## Trigger
Manual: /proactive-news-brief [topic] [schedule]
- topic: keyword or domain, default technology
- schedule: cron expression, default 0 8 * * * (08:00 daily)
Scheduled: fires automatically per the installed cron.

## Execution Steps

### Install (first run)
1. Parse topic and schedule from arguments.
2. Call CronCreate with the resolved schedule and command: /proactive-news-brief <topic> --run
3. Confirm to user: News brief for {topic} scheduled at {schedule} (cron ID: {id}).

### Runtime (every scheduled fire or --run flag)
1. Search: call WebSearch with query "{topic} news {current_date}", top 10 results.
2. Fetch and fallback loop: for each result URL call WebFetch; on failure (timeout, 4xx, 5xx) log skipped URL and continue. If 7 or more of 10 URLs fail, append a notice that results may be incomplete.
3. Deduplicate: drop stories with headline similarity over 80%.
4. Format brief with date header, numbered top stories each with one-sentence summary, quick-takes bullet section, and a footer showing sources fetched count and generation time.
5. Output the brief to the conversation.

## Acceptance Criteria
- CronCreate is called exactly once during install and the cron ID is reported.
- At least 3 distinct stories appear in every successful brief.
- Each failed fetch is skipped without crashing; brief still renders.
- Brief header always shows the correct current date.
- /proactive-news-brief --remove <id> calls CronDelete to cancel the schedule.