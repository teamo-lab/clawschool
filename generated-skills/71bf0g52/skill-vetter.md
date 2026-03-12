# skill-vetter

## Goal
Review a skill's Markdown content against a rubric covering structure, tool safety, prompt injection resistance, and acceptance-criteria completeness. Output a graded report so the user knows exactly what to fix before deploying the skill.

## Execution Steps

1. **Load the skill under review**
   - Accept a file path, skill name, or inline Markdown block as input
   - If a file path is given, use `Read` to load it

2. **Run the rubric checks** (each scored 0–2):

   | # | Check | 0 | 1 | 2 |
   |---|-------|---|---|---|
   | R1 | Has `## Goal` section | missing | vague | clear & scoped |
   | R2 | Has numbered `## Execution Steps` | missing | partial | complete |
   | R3 | Has `## Acceptance Criteria` checklist | missing | present but vague | measurable & checkable |
   | R4 | Tool calls are necessary & justified | unjustified calls | some excess | minimal & justified |
   | R5 | No prompt-injection surface (no `eval`, raw user string interpolated into shell/SQL) | injection present | partial risk | clean |
   | R6 | Error / failure paths are addressed | none | partial | all major paths handled |
   | R7 | Length calibration or output format defined | none | implicit | explicit |

3. **Compute score**: sum of rubric scores; max = 14.

4. **Emit the vetting report**:
   ```
   ## Skill Vetter Report — {skill name}
   **Score:** {n}/14  |  **Verdict:** {PASS ≥ 10 | NEEDS WORK 7–9 | FAIL ≤ 6}

   ### Rubric Results
   | Check | Score | Note |
   |-------|-------|------|
   …

   ### Required Fixes
   - {fix 1}
   - {fix 2}

   ### Suggested Improvements
   - {improvement 1}
   ```

5. **Optionally auto-patch**: if the user passes `--fix`, apply the required fixes directly to the skill file using `Edit` and re-run the rubric to confirm the score improved.

## Acceptance Criteria
- [ ] All 7 rubric checks are evaluated and scored
- [ ] Verdict threshold is applied correctly (PASS / NEEDS WORK / FAIL)
- [ ] Every "Required Fix" maps back to a specific failed rubric check
- [ ] `--fix` mode leaves the skill file syntactically valid Markdown
- [ ] Vetter does not modify any file unless `--fix` is explicitly passed
- [ ] Report is emitted even when the skill file cannot be read (error message replaces score)