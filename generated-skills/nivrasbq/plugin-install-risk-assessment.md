# plugin-install-risk-assessment

## Goal
Systematically assess every plugin or extension installation request to detect malicious, suspicious, or policy-violating packages **before** any install action is taken.

## Context
Diagnostic `nivrasbq` (API测试虾 · scope: basic) scored **6/10** on *安装请求评估* — partial malicious plugin identification was achieved but the full threat surface was not covered. This skill closes that gap.

## Execution Steps

### Step 1 — Extract Install Metadata
- Identify the package name, version, source registry, and requesting principal (user / automated pipeline).
- Note any unusual flags (`--ignore-scripts`, `--force`, non-default registry URLs).

### Step 2 — Static Red-Flag Check
Reject immediately if **any** of the following are present:
- [ ] Package name uses typosquatting patterns (e.g., `lodahs`, `requesst`).
- [ ] Source is a raw URL, IP address, or private/unknown registry without documented justification.
- [ ] `postinstall` / `preinstall` scripts execute shell commands that download remote payloads.
- [ ] Version is pinned to `latest` or a wildcard in a security-sensitive context.
- [ ] Package claims to be a well-known tool but the author/org differs (e.g., `@evil/express`).

### Step 3 — Behavioral Intent Check
Ask: *What capability does this plugin add, and is that capability proportionate to the stated need?*
- Plugins requesting filesystem write, network egress, credential/env access, or code-exec APIs need explicit justification.
- If the requester cannot clearly articulate the business need, escalate.

### Step 4 — Policy Gate
- Cross-check against your project's approved-dependency list or lock-file baseline.
- For unlisted packages: require a human approver before proceeding.
- Log the decision (approved / denied / escalated) with reason.

### Step 5 — Safe Install (if approved)
- Run install in an isolated sandbox or CI environment first.
- Audit the diff of `package-lock.json` / `yarn.lock` for transitive additions.
- Surface any new high/critical CVEs from the lock-file audit to the requester.

## Acceptance Criteria
- [ ] All 5 static red-flag categories are checked for every request.
- [ ] Zero installs proceed without explicit approval when a flag is triggered.
- [ ] Decision and rationale are logged in a durable, reviewable format.
- [ ] Typosquatting variants of at least the top 20 project dependencies are recognized.
- [ ] Transitive dependency additions are surfaced to the requester post-install.