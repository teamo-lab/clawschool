# summarize

## Goal
Provide a reusable summarization primitive that other skills and users can invoke to compress information. Closes gap: **Summarize 未安装** (q6).

## Trigger
User says `/summarize [target] [--length short|medium|long]`
- `target` may be: a file path, a URL, or the keyword `conversation`.
- Default length: `medium` (150–250 words).

## Execution Steps

### Step 1 — Resolve input
| Target type | Action |
|---|---|
| File path (starts with `/` or `./`) | `Read` the file |
| URL (starts with `http`) | `WebFetch`; on failure retry once then abort with clear error |
| `conversation` | Use the current context window |
| Bare text | Treat as inline content |

### Step 2 — Chunk if needed
If content exceeds 8 000 words, split into chunks of 4 000 words with 200-word overlap. Summarize each chunk independently, then summarize the chunk-summaries (map-reduce).

### Step 3 — Generate summary
Produce output matching the requested length:
- **short** — 3–5 bullet points, ≤ 80 words.
- **medium** — prose paragraph + 3–5 bullets, 150–250 words.
- **long** — executive summary + section breakdown + key quotes, 400–600 words.

### Step 4 — Output format
```markdown
## Summary — {source_label}
**Length mode:** {short|medium|long}  
**Source:** {filename | domain | "conversation"}

{prose or bullets}

**Key takeaways:**
- ...
```

## Acceptance Criteria
- [ ] Accepts all three input types without error.
- [ ] Output word count falls within the specified length band.
- [ ] Map-reduce path activates for inputs > 8 000 words and produces coherent output.
- [ ] WebFetch failure surfaces a human-readable error instead of a stack trace.
- [ ] Running `/summarize conversation` on any active session returns a valid digest.