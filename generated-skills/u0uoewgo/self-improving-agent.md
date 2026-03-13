# Self-Improving Agent

## Goal
Enable Claude to act as a self-improving agent by systematically evaluating its own responses, diagnosing quality gaps, and applying corrections — without requiring repeated human prompting.

## When to Use
- After generating a complex output (code, analysis, plan) that may have subtle errors
- When the user wants higher-confidence results with minimal back-and-forth
- During multi-step tasks where accumulated errors compound

## Execution Steps

### Step 1 — Initial Output
Produce the first-pass response to the user's request normally.

### Step 2 — Self-Critique
Immediately after the output, run an internal critique pass:
- Identify any logical gaps, missing edge cases, or incorrect assumptions
- Check against the original requirements — did every constraint get addressed?
- Flag any sections with low confidence

### Step 3 — Gap Prioritization
Rank identified issues by impact (high / medium / low). Focus corrections on high-impact gaps only — avoid over-engineering low-impact issues.

### Step 4 — Targeted Correction
Apply corrections in-place. Do not rewrite the entire output unless the first pass was fundamentally flawed. Annotate what changed and why.

### Step 5 — Convergence Check
After corrections, re-evaluate: are remaining gaps acceptable given the task scope? If yes, present the final output. If no, repeat from Step 2 (max 2 iterations to avoid loops).

## Acceptance Criteria
- [ ] At least one self-critique pass is performed before delivering the final answer
- [ ] Corrections are scoped to identified gaps — no unrelated changes introduced
- [ ] The final output explicitly notes what was self-corrected and why
- [ ] The process terminates within 2 iterations (does not loop indefinitely)
- [ ] User-facing response is concise — internal critique is not dumped into the reply