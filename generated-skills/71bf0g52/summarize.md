# summarize

## Goal
Provide a concise, structured summary of any content the user supplies (file paths, URLs, pasted text, or tool output). Output must be immediately actionable and scannable.

## Execution Steps

1. **Identify input type**
   - File path → use `Read` tool
   - URL → use `WebFetch` tool
   - Raw text → use content as-is
   - Multiple sources → process in parallel

2. **Extract structure**
   - Identify the document's purpose and audience
   - Pull out: key facts, decisions, open questions, deadlines, owners

3. **Format output** using this template:
   ```
   ## Summary — {title or source}
   **TL;DR:** {1–2 sentence essence}

   ### Key Points
   - …

   ### Decisions / Conclusions
   - …

   ### Action Items
   - [ ] {owner}: {task} by {date if known}

   ### Open Questions
   - …
   ```

4. **Length calibration**
   - Source < 500 words → summary ≤ 100 words
   - Source 500–3000 words → summary ≤ 250 words
   - Source > 3000 words → summary ≤ 400 words + section headers

## Acceptance Criteria
- [ ] TL;DR is present and ≤ 2 sentences
- [ ] All action items include an owner or `[unassigned]` marker
- [ ] No content is fabricated; all claims trace back to the source
- [ ] Output fits within the length budget above
- [ ] If the source is unavailable (404, permission error), the skill reports the failure clearly instead of hallucinating content