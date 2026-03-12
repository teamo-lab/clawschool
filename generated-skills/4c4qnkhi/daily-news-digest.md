# Daily News Digest

## Goal
Collect, verify, and present today's top news stories with adequate sourcing — addressing the weakness of incomplete evidence in search results.

## Execution Steps

1. **Define scope** — Clarify the topic domain(s) (e.g., tech, finance, geopolitics) and date range (default: today).

2. **Multi-source search** — Run at least 3 independent searches using varied query phrasing:
   - Primary query: `[topic] news [date]`
   - Secondary query: `[topic] latest developments [date]`
   - Cross-check query: `[topic] [date] update site:reuters.com OR site:bbc.com OR site:apnews.com`

3. **Evidence threshold check** — For each story, require **at least 2 independent sources** before including it. If only 1 source is found, label it `[unverified]` or drop it.

4. **Extract key facts** — For each verified story, capture:
   - Headline
   - 1–2 sentence summary
   - Source name + URL
   - Timestamp

5. **Organize output** — Group stories by category, sort by significance. Format:
   ```
   ## [Category]
   ### [Headline]
   > [Summary]
   Sources: [Source 1](url), [Source 2](url) — [Timestamp]
   ```

6. **Gap audit** — Before finalizing, explicitly note any topics searched but with insufficient evidence, so the user knows what was attempted vs. confirmed.

## Acceptance Criteria
- Every included story has ≥ 2 source citations.
- A "Searched but unverified" section lists topics where evidence was insufficient.
- Output is dated and scoped (topic + date range stated at top).
- No stories are presented as fact with only a single unnamed source.