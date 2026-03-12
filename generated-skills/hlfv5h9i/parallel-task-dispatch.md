# parallel-task-dispatch

## Goal
Increase throughput on requests that contain two or more independent subtasks by identifying parallelizable work and issuing concurrent tool calls instead of serial ones.

## Trigger
Use this skill when the user's request contains conjunction keywords ("and", "also", "as well as", "both … and", "at the same time") or when the request is clearly decomposable into ≥ 2 subtasks with no data dependency between them.

## Execution Steps

1. **Parse the request** — List every distinct subtask the user is asking for.

2. **Build a dependency graph** — For each pair of subtasks, determine if one must complete before the other can start:
   - If Subtask B needs output from Subtask A → sequential (A then B).
   - If they are independent → parallel.

3. **Dispatch** — Issue all independent subtasks as simultaneous tool calls in a single response turn. Do not wait for one to finish before starting the next unless a data dependency requires it.

4. **Aggregate results** — Once all parallel calls return, merge and present results in the order the user originally requested them.

5. **Announce parallelism** (optional, one line) — e.g., "Running both searches concurrently." Omit if it would be noisy.

## Example
User: "Summarize today's AI news AND check if the deployment pipeline is green."
- Subtask A: web search for AI news (independent)
- Subtask B: check CI status (independent)
→ Dispatch A and B in the same tool-call block; merge answers in one reply.

## Acceptance Criteria
- Two or more independent tool calls are issued in the same response turn (not across multiple turns).
- Final answer covers all subtasks the user requested.
- No subtask is skipped or silently deferred.