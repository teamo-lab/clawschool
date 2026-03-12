# self-improving-agent

## Goal
After completing any non-trivial task, the agent performs a structured retrospective and surfaces concrete, actionable improvement proposals—covering prompt quality, tool usage patterns, and workflow gaps—so that repeated mistakes are eliminated and capability compounds over time.

## Execution Steps

1. **Trigger**: Automatically activate at the end of any task that involved ≥3 tool calls or produced an error/retry.
2. **Collect evidence**: Review the conversation turn history for this task:
   - Tool calls that failed or were retried
   - User corrections or negative feedback
   - Steps that required more than one attempt
3. **Categorize findings** into one of three buckets:
   - `prompt-gap`: The agent misunderstood the instruction or lacked context
   - `tool-misuse`: A wrong or suboptimal tool was chosen
   - `workflow-gap`: A missing step caused rework or a safety issue
4. **Draft improvement proposals**: For each finding, write a one-paragraph proposal in the format:
   ```
   [Category] <short title>
   Problem: <what went wrong>
   Proposal: <specific change to prompt / tool selection rule / workflow step>
   Expected outcome: <measurable improvement>
   ```
5. **Save to memory**: If a proposal applies to future conversations, persist it as a `feedback` memory entry under `/home/clawapi/.claude/projects/-opt-clawschool-api/memory/`.
6. **Present to user**: Output a concise "Retrospective" section at the end of the response with all proposals. Ask for approval before persisting.

## Acceptance Criteria
- [ ] Retrospective is produced for every task meeting the trigger condition
- [ ] Each proposal is categorized and includes problem, proposal, and expected outcome
- [ ] No proposal is persisted without explicit user approval
- [ ] Approved proposals appear in the memory index (`MEMORY.md`) within the same conversation turn
- [ ] On the next similar task, the agent demonstrably avoids the previously identified mistake