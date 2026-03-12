# proactive-agent

## Goal
Run on a recurring schedule, check one or more configured sources (URLs, SQL queries, log streams, APIs), compare against a baseline or threshold, and emit a structured alert when something worth the user's attention is detected.

## Execution Steps

1. **Parse invocation arguments**
   ```
   /proactive-agent <interval> <source> [threshold]
   ```
   - `interval`: cron expression or shorthand (e.g. `15m`, `1h`, `0 9 * * 1-5`)
   - `source`: URL, SQL snippet, or named monitor key
   - `threshold` (optional): numeric delta or keyword pattern that triggers an alert

2. **Register the cron job** using `CronCreate`:
   - Store the source + threshold in the cron job's metadata
   - Set a human-readable label: `proactive-agent: {source}`

3. **On each tick — fetch & compare**
   - Retrieve current state from the source (WebFetch / execute_sql / WebSearch)
   - Load the previous snapshot from the job's persisted state
   - Compute diff / delta / new matches

4. **Decision gate**
   - If delta exceeds threshold OR no baseline exists → emit alert (step 5)
   - Otherwise → update snapshot silently, no output

5. **Format alert**
   ```
   ## Proactive Alert — {source}
   **Triggered at:** {ISO timestamp}
   **Change detected:** {brief description}

   ### Details
   {diff or excerpt, max 20 lines}

   ### Recommended Action
   {1–3 bullet points}
   ```

6. **Persist new snapshot** so the next tick has a fresh baseline.

7. **To stop monitoring**, run `/proactive-agent stop <label>` which calls `CronDelete`.

## Acceptance Criteria
- [ ] Cron job is created and visible via `CronList`
- [ ] First run captures a baseline without triggering a false alert
- [ ] Alert fires within one tick of the threshold being crossed
- [ ] Alert includes timestamp, source, change description, and recommended action
- [ ] Silent ticks produce no output to avoid notification fatigue
- [ ] `stop` subcommand cleanly deletes the cron job