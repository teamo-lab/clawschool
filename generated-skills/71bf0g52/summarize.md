# summarize

## Goal
Produce a structured summary of any provided content on demand.

## Trigger
Invoke via /summarize [target] where target is optional free-form text, a file path, or omitted to summarize the current conversation.

## Execution Steps

1. Identify the target: file path -> Read the file; plain text -> use directly; no argument -> summarize current conversation.
2. Determine depth: under 500 words -> one paragraph (3-5 sentences); 500-3000 words -> bullet list of key points (max 8 bullets); over 3000 words -> section-by-section TL;DR with a 2-sentence executive summary.
3. Structure output with headings: Summary, Key Points, Action Items (if any).
4. Validate completeness: re-read the source and confirm every major topic is represented.

## Acceptance Criteria
- /summarize with no argument produces a coherent summary of the current conversation.
- /summarize path/to/file.md reads the file and returns a structured summary.
- Output always includes a Summary heading and at least one Key Points bullet.
- Summary length stays within the depth guidelines above.
- No hallucinated facts: every point maps to content in the source material.