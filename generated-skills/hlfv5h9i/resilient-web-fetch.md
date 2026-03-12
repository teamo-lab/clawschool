# resilient-web-fetch

## Goal
Make web-dependent tasks (news aggregation, page scraping, link verification) robust against fetch failures by following a structured retry-and-fallback ladder.

## Trigger
Use this skill whenever the task requires fetching one or more URLs, or performing real-time web searches, especially when results will be presented to the user as factual content.

## Execution Steps

### A. Real-time search (e.g., daily news)
1. Issue a `WebSearch` call with a focused query (include date range when freshness matters, e.g., `after:2026-03-11`).
2. If results are empty or clearly stale, reformulate the query with synonyms or a broader date window and retry **once**.
3. If still insufficient, transparently tell the user: "I could only find results up to [date]; here is what I have." Do not fabricate headlines.

### B. Direct URL fetch
1. Call `WebFetch` on the target URL.
2. **On failure (timeout / 4xx / 5xx / empty body)**:
   a. Try a cached/archived version if a cache URL is known or can be inferred.
   b. Try an alternative URL from search results that covers the same content.
   c. If all alternatives fail, report the failure explicitly: "[URL] is unreachable. Here is what I found from related sources: …"
3. Never return a blank or placeholder response without disclosing the failure.

### C. Partial success
- If only some URLs succeed, return the successful results and list the failed ones with their error reason. Do not silently omit failures.

## Acceptance Criteria
- At least one fallback attempt is made before declaring a fetch failure.
- The user is always informed when content could not be retrieved.
- No hallucinated URLs, headlines, or page content is presented as real.
- For news tasks, at least 3 distinct, sourced items are returned when search succeeds.