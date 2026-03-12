# self-improving-agent

## Objective

Equip the agent with a structured self-reflection loop so it can detect when output falls short of acceptance criteria, diagnose the root cause, and apply targeted improvements without requiring human re-prompting on every iteration.

## Execution Steps

1. **Baseline capture** - Before starting any task, record the explicit success criteria (tests passing, lint clean, required output format).
2. **Execute and observe** - Run the task normally. Collect all structured feedback: test output, linter results, tool errors, user-defined assertions.
3. **Gap analysis** - Compare actual output against the baseline. Identify specific failure points.
4. **Root-cause hypothesis** - For each gap, generate a 1-2 sentence hypothesis before touching code. Log it inline for auditability.
5. **Targeted fix** - Apply the minimum change that addresses the hypothesis. Scope changes to the identified failure surface only.
6. **Re-validate** - Re-run the same validation from Step 2. If gap is closed, proceed. If not, repeat from Step 3 with an updated hypothesis.
7. **Escalate on stall** - If the same failure persists after 3 iterations, stop the loop and surface the diagnosis to the user.

## Acceptance Criteria

- All originally stated success criteria are met before the skill exits.
- Each iteration produces a distinct hypothesis - no blind retries.
- The agent does not modify files outside the failure surface without explicit user approval.
- On stall (3 failed iterations), the agent outputs a structured escalation report rather than continuing to loop.
- Total autonomous iterations never exceed 5 without a user checkpoint.