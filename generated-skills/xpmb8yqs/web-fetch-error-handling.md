# Skill: web-fetch-error-handling

## Goal

Ensure every `WebFetch` call in a task has explicit error handling so that a failed page load never silently blocks progress. The agent must detect failure, communicate it clearly, and attempt at least one recovery path before giving up.

## Execution Steps

1. **Attempt the fetch** — call `WebFetch` with the target URL.
2. **Detect failure** — treat any of the following as a fetch failure:
   - Tool returns an error message (e.g., `connection refused`, `timeout`, `404`, `403`, `SSL error`).
   - Response body is empty or contains only an HTTP error status line.
3. **Log the failure reason** — output a one-line diagnostic to the user:
   > `WebFetch failed for <url>: <reason>`
4. **Apply a recovery strategy** (choose the most appropriate):
   - **Retry with a cached/archive URL** — prepend `https://webcache.googleusercontent.com/search?q=cache:` or use the Wayback Machine snapshot URL if the original host is unreachable.
   - **Search for the content instead** — use `WebSearch` with the page title or key terms to find an equivalent source.
   - **Ask the user** — if no alternative is found, use `AskUserQuestion` to request a mirror URL or a local copy of the document.
5. **Confirm success or escalate** — after the recovery attempt, verify the content is usable. If still failing after one recovery, escalate to the user with a clear summary of both attempts.

## Acceptance Criteria

- [ ] A fetch failure is never swallowed silently; the user always sees a diagnostic message.
- [ ] At least one automatic recovery path (archive, cache, or search) is attempted before asking the user.
- [ ] If both the original and recovery fetch fail, the agent explicitly states it cannot retrieve the page and explains why.
- [ ] The agent does not retry the identical failing URL more than once without a change in strategy.
- [ ] All URLs used in recovery are derived from existing knowledge or tool results — no guessed URLs.