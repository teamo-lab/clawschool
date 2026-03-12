# parallel-task-decomposer

## Goal
When a user request contains two or more logically independent sub-goals (e.g., "fetch today's news AND summarize yesterday's metrics"), decompose the work into parallel tracks, execute them concurrently, and merge results into a single coherent response.

## When to Activate
- User message contains connectives implying multiple goals: `and`, `also`, `as well as`, `plus`, `both … and`
- Request mixes different tool types (e.g., web search + file read + API call)
- Any task that can be split into ≥ 2 independent subtasks

## Execution Steps

1. **Parse the request** — Identify all distinct sub-goals. Write them out as a numbered list before starting work.
   ```
   Subtasks identified:
   1. [Subtask A — tool/resource needed]
   2. [Subtask B — tool/resource needed]
   ```
2. **Classify dependencies** — Mark each subtask as `INDEPENDENT` or `DEPENDS ON [N]`. Only independent subtasks may run in parallel.
3. **Launch parallel execution** — Fire all `INDEPENDENT` subtasks in a single message using multiple tool calls. Never serialize work that can run concurrently.
4. **Collect and validate results** — After all parallel calls return:
   - Check each result for completeness (non-empty, no error).
   - For search/news tasks: require ≥ 2 corroborating sources before treating a finding as confirmed. Flag single-source findings as `[unverified]`.
5. **Merge into unified response** — Combine results under clearly labeled sections matching the original subtasks. Do not omit any subtask even if its result was partial.
6. **Surface gaps** — If a subtask returned insufficient evidence, explicitly state what is missing and suggest a follow-up action.

## Acceptance Criteria
- [ ] All independent subtasks are launched as parallel tool calls in a single message.
- [ ] No subtask is silently dropped — every identified goal has a corresponding result section.
- [ ] Search/news findings backed by only one source are labeled `[unverified]`.
- [ ] The response is structured with one section per original subtask.
- [ ] Dependencies between subtasks are correctly sequenced (dependent tasks wait for their inputs).