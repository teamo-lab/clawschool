# self-improving-agent

## Goal

After completing a task, automatically reflect and optimize output. Reduce repeated user corrections and continuously improve quality.

## Trigger Conditions

- User requests revision or improvement
- Agent detects potential gaps after completing a complex task
- Output contains TODOs, placeholders, or obvious omissions

## Execution Steps

1. **Self-review**: After task completion, check each output item against the original requirements for completeness, accuracy, and clarity.
2. **Gap identification**: List up to 3 highest-priority improvement points using format: `[GAP] <description>`.
3. **Iterative refinement**: Fix each GAP and mark it `[FIXED]`.
4. **Convergence check**: Stop if no new GAPs remain or 3 iterations are reached. Output final result.
5. **Memory update**: Write improvement summary to memory (type: `feedback`) for future conversations.

## Acceptance Criteria

- [ ] Output contains no unresolved TODOs or placeholders
- [ ] Each iteration has clear GAP to FIXED records
- [ ] Iterations capped at 3 to prevent infinite loops
- [ ] Final output maps to every original requirement with no omissions
- [ ] Improvement summary saved to memory system