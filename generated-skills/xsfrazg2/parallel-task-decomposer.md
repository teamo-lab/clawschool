# parallel-task-decomposer

## Goal

Improve throughput and response quality when handling requests that contain two or more logically independent sub-goals by explicitly decomposing, parallelising, and merging the work.

## When to Invoke

Trigger this skill when the user's message contains:
- Conjunctions implying multiple goals: *"…and also…", "…as well as…", "…plus…"*
- Numbered lists of tasks in a single prompt
- Mixed task types (e.g., research + code generation + data retrieval)

## Execution Steps

1. **Parse & label subtasks** — Re-read the full user message and enumerate every distinct sub-goal as a numbered list (e.g., Task A, Task B, …).
2. **Dependency analysis** — For each pair of subtasks, decide: *independent* (can run in parallel) or *sequential* (B needs A's output). Document the dependency graph.
3. **Dispatch independent tasks in parallel** — Launch all independent subtasks simultaneously using a single message with multiple tool calls (Agent, WebSearch, Read, etc.). Never serialize work that can be parallelized.
4. **Execute sequential tasks in order** — For dependent subtasks, wait for the upstream result before starting the downstream task.
5. **Collect & validate results** — For each subtask, verify the output meets its individual acceptance criterion before merging.
6. **Synthesize a unified response** — Combine all subtask results into one coherent, clearly-structured reply. Use headings or sections labelled by the original subtask.
7. **Surface gaps** — If any subtask returned insufficient evidence (e.g., a web search with no authoritative source), explicitly flag it and suggest a follow-up action rather than silently omitting it.

## Acceptance Criteria

- [ ] Every distinct sub-goal in the original request is explicitly identified and tracked.
- [ ] Independent subtasks are dispatched in a single parallel tool-call batch, not one-by-one.
- [ ] No subtask result is silently dropped; gaps are flagged with a follow-up suggestion.
- [ ] The final response is structured so the user can clearly map each section back to the original sub-goal.
- [ ] Total wall-clock tool calls is minimised compared to a purely sequential approach.