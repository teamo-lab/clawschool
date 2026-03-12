# summarize

## Goal
Address the **Summarize skill not installed** gap (q6) by providing a single, reliable entry-point for all summarization tasks across content types.

## Trigger
User says: "summarize this", "give me a summary of", "TL;DR", "condense this article", or pastes a URL / file path and asks for a summary.

## Execution Steps

### 1. Detect content type
| Input | Action |
|-------|--------|
| URL | `WebFetch` the page; extract body text |
| File path | `Read` the file |
| Pasted text | Use directly |
| Ambiguous | Ask user: "Is this a URL, a file path, or text?" |

### 2. Determine desired length
- Check if user specified length: `short` (3 bullets), `medium` (1 paragraph), `long` (structured sections).
- Default: `medium`.

### 3. Produce summary

**Short** — 3 bullet points:
```
- {key point 1}
- {key point 2}
- {key point 3}
```

**Medium** — 1 paragraph (4–6 sentences): context → main argument → key evidence → conclusion.

**Long** — structured Markdown:
```markdown
## Summary
### Background
...
### Key Points
...
### Conclusion
...
```

### 4. Handle fetch failures
- If `WebFetch` returns an error: report the error code to the user and ask them to paste the text manually.
- If the file is not found: report the path and ask the user to verify it.

### 5. Output
- Print the summary directly in the conversation.
- If the source was a URL, append: `**Source:** {url}`.

## Acceptance Criteria
- [ ] Works for all three input types: URL, file, pasted text.
- [ ] Respects the user's length preference.
- [ ] Fetch/read failures produce a clear error message and a recovery prompt — never a silent empty output.
- [ ] Summary accurately reflects the source material (no hallucinated facts).
- [ ] Response time under 30 seconds for typical article lengths.