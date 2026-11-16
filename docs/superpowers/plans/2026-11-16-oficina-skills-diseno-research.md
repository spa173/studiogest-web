# Office Skills and Design Research Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bundle nine focused method skills and make reference-led branding and landing-page research a verifiable part of Web Design work.

**Architecture:** Agent profiles own routing and responsibility; skills own repeatable domain methods. Existing `taste-skill` and `frontend-developer` are imported from the approved ZIP, while seven new skills follow one compact structure and share contract terminology from the office core.

**Tech Stack:** Markdown Agent Skills, existing Python `audit_taste.py`, PowerShell validation, optional web/browser and image capabilities supplied by the host.

**Spec:** `docs/superpowers/specs/2026-11-16-oficina-unificada-codex-opencode-design.md`

## Global Constraints

- Use `workspace-01a1e1cf-1c19-7939-9646-891d2bc49d21.zip` as the approved source for `taste-skill` and `frontend-developer`.
- Create exactly seven additional method skills: backend, QA, security, platform, forensics, analytics, and SEO/Growth.
- Every skill needs activation metadata, limits, input/output contract, method, gate, references, and four evals.
- Do not repeat department-routing logic inside skills.
- Web Design research is mandatory for new sites, landing pages, and significant redesigns; optional for small changes within an approved system.
- Research uses 3–6 current references and records URLs and consultation dates; it must not clone protected identity, copy, imagery, animation, or trade dress.
- Do not add dependencies to run skill validation.

## Review Focus

- A backend-only task must not trigger `taste-skill`; Task 1 preserves its anti-trigger.
- Missing web access must produce a declared limitation rather than fabricated research; Task 6 pins this.
- A skill reference path that does not exist must fail validation; Task 7 pins this.
- Security and forensics must preserve evidence and avoid unauthorized exploitation or remediation; Tasks 3 and 5 pin this.
- Two skills claiming the same decision must fail the authority check; Task 7 pins this.

---

### Task 1: Import and validate the approved design and frontend skills

**Files:**
- Create: `skills/taste-skill/**` from the approved ZIP
- Create: `skills/frontend-developer/SKILL.md` from the approved ZIP
- Create: `scripts/Test-Office.Skills.ps1`

**Interfaces:**
- Produces: `Get-OfficeSkillManifest([string] $SkillsRoot) -> object[]`.
- Produces: `Assert-OfficeSkill([string] $SkillPath) -> $null` or throws.

- [ ] **Step 1: Write failing import tests**

Assert both skills exist, names match their folders, descriptions are present, every referenced file exists, `taste-skill` has its auditor and eval fixture, and `frontend-developer` explicitly cedes visual authority.

- [ ] **Step 2: Run and verify failure**

Run: `pwsh -NoProfile -File scripts/Test-Office.Skills.ps1 -Section Imported`

Expected: FAIL because `skills/` is absent.

- [ ] **Step 3: Import the approved files without rewriting their content**

Use the extracted archive under the task workspace as source. Preserve UTF-8 and all assets, references, evals, and scripts.

- [ ] **Step 4: Repair the missing motion asset exposed by validation**

The approved ZIP references `assets/motion.css` but does not contain it. Add that focused asset from the motion tokens and patterns already specified in `references/movimiento.md`; do not broaden the design rules or silently delete the reference.

- [ ] **Step 5: Run the imported skill tests**

Run: `pwsh -NoProfile -File scripts/Test-Office.Skills.ps1 -Section Imported`

Run: `python skills/taste-skill/scripts/audit_taste.py skills/taste-skill/assets --profile 3`

Expected: skill validation passes; the approved clean asset fixture reports zero errors.

- [ ] **Step 6: Commit**

```powershell
git add skills/taste-skill skills/frontend-developer scripts/Test-Office.Skills.ps1
git commit -m "feat: bundle design and frontend skills"
```

### Task 2: Backend developer skill

**Files:**
- Create: `skills/backend-developer/SKILL.md`
- Create: `skills/backend-developer/references/api-data-auth.md`
- Create: `skills/backend-developer/evals/evals.md`
- Modify: `scripts/Test-Office.Skills.ps1`

**Interfaces:**
- Consumes: task, handoff, and gate terminology from the core plan.
- Produces: an implementation contract covering API, data, auth, validation, observability, migrations, and integration tests.

- [ ] **Step 1: Add failing eval-shape and authority tests**

Assert four evals exist and the skill owns backend implementation but not product scope, visual tokens, security sign-off, or deployment approval.

- [ ] **Step 2: Run and verify failure**

Run: `pwsh -NoProfile -File scripts/Test-Office.Skills.ps1 -Skill backend-developer`

Expected: FAIL because the skill is missing.

- [ ] **Step 3: Write the minimal skill and focused reference**

Require existing architecture inspection, contract-first changes, reversible migrations, boundary validation, authorization checks, integration evidence, and explicit limits. Avoid framework-specific dependencies.

- [ ] **Step 4: Run and commit**

Run: `pwsh -NoProfile -File scripts/Test-Office.Skills.ps1 -Skill backend-developer`

Expected: PASS.

```powershell
git add skills/backend-developer scripts/Test-Office.Skills.ps1
git commit -m "feat: add backend developer skill"
```

### Task 3: QA and security skills

**Files:**
- Create: `skills/qa-engineer/SKILL.md`
- Create: `skills/qa-engineer/references/test-strategy.md`
- Create: `skills/qa-engineer/evals/evals.md`
- Create: `skills/security-auditor/SKILL.md`
- Create: `skills/security-auditor/references/review-method.md`
- Create: `skills/security-auditor/evals/evals.md`
- Modify: `scripts/Test-Office.Skills.ps1`

**Interfaces:**
- Produces: QA report with acceptance coverage, reproduction, executed evidence, and go/no-go.
- Produces: security report with severity, evidence, affected boundary, remediation, and gate recommendation.

- [ ] **Step 1: Add failing tests for review-only behavior**

Assert QA may execute tests but does not silently fix during review; Security is read-only, never prints secret values, and does not claim scanner results it did not execute.

- [ ] **Step 2: Run and verify failure**

Run: `pwsh -NoProfile -File scripts/Test-Office.Skills.ps1 -Skill qa-engineer,security-auditor`

Expected: FAIL because both skills are missing.

- [ ] **Step 3: Implement both skills and their four evals**

Use risk-based depth, concrete evidence, severity ordering, and the gate enums from the spec. Keep penetration actions out of scope unless the user explicitly authorizes the exact target.

- [ ] **Step 4: Run and commit**

Run: `pwsh -NoProfile -File scripts/Test-Office.Skills.ps1 -Skill qa-engineer,security-auditor`

Expected: PASS.

```powershell
git add skills/qa-engineer skills/security-auditor scripts/Test-Office.Skills.ps1
git commit -m "feat: add QA and security skills"
```

### Task 4: Platform and delivery skill

**Files:**
- Create: `skills/devops-platform/SKILL.md`
- Create: `skills/devops-platform/references/delivery-observability.md`
- Create: `skills/devops-platform/evals/evals.md`
- Modify: `scripts/Test-Office.Skills.ps1`

**Interfaces:**
- Produces: delivery plan with build artifact, environment, health checks, observability, rollback, and approval boundary.

- [ ] **Step 1: Add failing safety tests**

Assert the skill may prepare and inspect but requires explicit approval for production deploys, infrastructure writes, real rollback, and destructive commands.

- [ ] **Step 2: Run and verify failure**

Run: `pwsh -NoProfile -File scripts/Test-Office.Skills.ps1 -Skill devops-platform`

Expected: FAIL because the skill is missing.

- [ ] **Step 3: Implement the skill and evals**

Cover CI/CD, infrastructure as code, secrets boundaries, health checks, logs/metrics/traces, rollback, and cost awareness without assuming a cloud provider.

- [ ] **Step 4: Run and commit**

Run: `pwsh -NoProfile -File scripts/Test-Office.Skills.ps1 -Skill devops-platform`

Expected: PASS.

```powershell
git add skills/devops-platform scripts/Test-Office.Skills.ps1
git commit -m "feat: add platform delivery skill"
```

### Task 5: Forensics and incident-response skill

**Files:**
- Create: `skills/forensics-incident/SKILL.md`
- Create: `skills/forensics-incident/references/evidence-and-timeline.md`
- Create: `skills/forensics-incident/evals/evals.md`
- Modify: `scripts/Test-Office.Skills.ps1`

**Interfaces:**
- Produces: incident timeline, evidence inventory, impact, hypotheses/root cause, containment recommendations, and follow-up actions.

- [ ] **Step 1: Add failing evidence-preservation tests**

Assert evidence collection precedes remediation, facts remain separate from hypotheses, destructive containment requires approval, and sensitive values are redacted.

- [ ] **Step 2: Run and verify failure**

Run: `pwsh -NoProfile -File scripts/Test-Office.Skills.ps1 -Skill forensics-incident`

Expected: FAIL because the skill is missing.

- [ ] **Step 3: Implement the skill and evals**

Include incident severity, chain-of-custody-lite fields suitable for software teams, timeline reconstruction, blameless post-mortem, and handoff to Security/DevOps/Documentation.

- [ ] **Step 4: Run and commit**

Run: `pwsh -NoProfile -File scripts/Test-Office.Skills.ps1 -Skill forensics-incident`

Expected: PASS.

```powershell
git add skills/forensics-incident scripts/Test-Office.Skills.ps1
git commit -m "feat: add incident forensics skill"
```

### Task 6: Analytics, SEO/Growth, and reference-led design research

**Files:**
- Create: `skills/data-analytics/SKILL.md`
- Create: `skills/data-analytics/references/tracking-and-analysis.md`
- Create: `skills/data-analytics/evals/evals.md`
- Create: `skills/seo-growth/SKILL.md`
- Create: `skills/seo-growth/references/technical-seo-experiments.md`
- Create: `skills/seo-growth/evals/evals.md`
- Create: `skills/taste-skill/references/reference-research.md`
- Create: `skills/taste-skill/assets/reference-study-template.md`
- Modify: `skills/taste-skill/SKILL.md`
- Modify: `office/roles/diseno-web.md`
- Modify: `scripts/Test-Office.Skills.ps1`

**Interfaces:**
- Produces: analytics tracking plan with events, properties, privacy, validation, and success metrics.
- Produces: SEO/Growth audit or experiment plan with indexability, CWV, structured data, hypothesis, metric, and stopping rule.
- Produces: `reference-study.md` with 3–6 dated references, transferable patterns, avoid list, and original direction.

- [ ] **Step 1: Add failing domain and research tests**

Assert analytics does not invent metrics, SEO does not promise ranking, and Web Design requires reference research for new sites/landings/redesigns but not for a small approved-system adjustment. Add a no-web case that must return a limitation rather than fabricated URLs.

- [ ] **Step 2: Run and verify failure**

Run: `pwsh -NoProfile -File scripts/Test-Office.Skills.ps1 -Skill data-analytics,seo-growth,taste-skill`

Expected: FAIL on the missing skills and research reference.

- [ ] **Step 3: Implement analytics and SEO/Growth skills**

Use provider-neutral methods. Make one analytics provider selectable, not two by default. Require source dates for volatile SEO guidance.

- [ ] **Step 4: Implement the reference-research method**

Require real brand sites plus curated galleries and authoritative technical guidance. Capture URL, date, page type, viewport, relevant pattern, and risks. Explicitly prohibit copying identity, copy, images, distinctive motion, or trade dress.

- [ ] **Step 5: Run and commit**

Run: `pwsh -NoProfile -File scripts/Test-Office.Skills.ps1 -Skill data-analytics,seo-growth,taste-skill`

Expected: PASS, including the no-web limitation case.

```powershell
git add skills/data-analytics skills/seo-growth skills/taste-skill office/roles/diseno-web.md scripts/Test-Office.Skills.ps1
git commit -m "feat: add analytics SEO and design research workflows"
```

### Task 7: Cross-skill authority and full verification

**Files:**
- Modify: `scripts/Test-Office.Skills.ps1`
- Modify: `office/registry.json`
- Modify: `README.md`

**Interfaces:**
- Consumes: nine complete skills and the core registry.
- Produces: one validation command for skill discovery, reference integrity, eval coverage, and authority ownership.

- [ ] **Step 1: Add failing cross-skill tests**

Map each decision domain to exactly one owning skill; fail duplicate ownership, missing registry skill paths, missing eval categories, and missing referenced assets.

- [ ] **Step 2: Run and verify the test exposes incomplete mappings**

Run: `pwsh -NoProfile -File scripts/Test-Office.Skills.ps1`

Expected: FAIL until every registry mapping and README inventory is complete.

- [ ] **Step 3: Complete mappings and documentation**

Document which agents use each skill and when Design research is mandatory. Do not add skills to agents that only consume their output.

- [ ] **Step 4: Run full skill verification**

Run: `pwsh -NoProfile -File scripts/Test-Office.Skills.ps1`

Run: `python skills/taste-skill/scripts/audit_taste.py skills/taste-skill/assets --profile 3`

Expected: PASS; nine skills, four eval classes each, no broken references, no authority conflicts, Taste assets clean.

- [ ] **Step 5: Commit**

```powershell
git add office/registry.json scripts/Test-Office.Skills.ps1 README.md
git commit -m "test: validate office skill authority"
```
