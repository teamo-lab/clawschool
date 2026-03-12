# Search Evidence Validator

## Goal
Prevent under-evidenced conclusions by scoring each search result for reliability before using it — directly fixing the pattern of acting on partial search results.

## Execution Steps

1. **Initial search pass** — Perform the search and collect all results (aim for 5–10 results).

2. **Score each result** using this rubric (total out of 10):
   | Criterion | Points |
   |---|---|
   | Published by known outlet (Reuters, AP, BBC, gov, academic) | +3 |
   | Timestamp within target date range | +2 |
   | Article body directly addresses the query | +2 |
   | Corroborated by another result in the set | +2 |
   | Author/byline present | +1 |

3. **Apply threshold**:
   - Score ≥ 7: Use as primary evidence.
   - Score 4–6: Use as supporting evidence only; note uncertainty.
   - Score < 4: Discard or flag as low-confidence.

4. **Re-search if needed** — If fewer than 2 results score ≥ 7, reformulate the query and repeat. Try:
   - Adding a date filter (`after:2026-03-13`)
   - Switching to a different search engine or news-specific source
   - Breaking a compound query into simpler parts

5. **Summarize evidence posture** — Before presenting conclusions, state:
   ```
   Evidence quality: [Strong / Moderate / Weak]
   Sources used: N (M high-confidence, K supporting)
   Gaps: [what could not be confirmed]
   ```

## Acceptance Criteria
- No conclusion is presented without stating its evidence quality.
- At least 2 high-confidence sources back any factual claim.
- A re-search attempt is always made when initial evidence is weak.
- Gaps and unverified areas are explicitly surfaced to the user.