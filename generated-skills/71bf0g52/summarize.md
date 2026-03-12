# summarize

## Goal
Provide a concise, structured summary of any input — free-form text, local files, or web URLs — so the user can quickly grasp key information without reading the full source.

## Trigger
User says: "summarize", "tl;dr", "给我总结一下", or passes a file/URL with no other instruction.

## Execution Steps

1. **Identify input type**
   - If a URL is provided → use `WebFetch` to retrieve page content.
   - If a file path is provided → use `Read` to load the file.
   - If inline text is provided → use it directly.

2. **Extract structure** — identify:
   - Main topic / title
   - Key points (3–7 bullet points)
   - Decisions, conclusions, or recommendations
   - Action items (if any)

3. **Output format**
   ```
   ## Summary: <title>
   **Source**: <origin>   **Date**: <date if available>

   ### Key Points
   - …

   ### Conclusions / Recommendations
   - …

   ### Action Items
   - [ ] …
   ```

4. **Length calibration** — target ≤ 20 % of original length. If the source is < 200 words, one paragraph suffices.

## Acceptance Criteria
- [ ] Output produced for text, file, and URL inputs without user needing to specify format.
- [ ] Key points section always present and contains ≥ 3 items for sources > 300 words.
- [ ] Response length ≤ 20 % of input length (measured in tokens).
- [ ] Action items section omitted (not shown as empty) when none exist.
- [ ] Works offline (file/text path) without requiring network tools.