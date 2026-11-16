# Oficina Core and Agent Generation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the canonical registry, contracts, role prompts, and deterministic generators for one 31-profile office shared by Codex and OpenCode.

**Architecture:** JSON files under `office/` are the source of truth. Focused PowerShell functions validate that source and render platform-native files; generated files are never edited manually. The Codex main chat receives the Director rules through a managed `AGENTS.md` block, while OpenCode receives a primary `directora` agent.

**Tech Stack:** PowerShell 7+, JSON Schema-style documents, Markdown prompts, OpenCode agent Markdown, Codex agent TOML; no new package dependencies.

**Spec:** `docs/superpowers/specs/2026-11-16-oficina-unificada-codex-opencode-design.md`

## Global Constraints

- Keep exactly 31 conceptual profiles: one Director, five coordinators, and twenty-five specialists.
- Do not pin a model or provider in generated agents.
- Use JSON rather than YAML for canonical machine-readable data.
- Preserve the role IDs and department ownership fixed by the spec.
- OpenCode may enforce permissions; Codex agents inherit parent permissions and must not claim a separate sandbox.
- Do not touch `helpdesk-saas/` or `studiogest-web/`.
- Generated files must identify their canonical source and reject manual drift in tests.
- Add no runtime dependency beyond PowerShell and tools already used by the kit.

## Review Focus

- Duplicate or cyclic parent IDs must fail validation before generation; Task 1 pins this.
- A coordinator allowlist that omits or adds an agent must fail; Task 2 pins this.
- Markdown containing quotes, Unicode, or multiline instructions must round-trip into valid TOML; Task 4 pins this.
- Regeneration over unchanged input must produce byte-identical output; Tasks 3 and 4 pin this.
- Existing non-office `AGENTS.md` text must survive managed-block generation; Task 4 pins this.

---

### Task 1: Canonical registry, contracts, and validation

**Files:**
- Create: `office/registry.json`
- Create: `office/capabilities.json`
- Create: `office/permission-sets/readonly.json`
- Create: `office/permission-sets/implementer.json`
- Create: `office/permission-sets/operator.json`
- Create: `office/contracts/task.schema.json`
- Create: `office/contracts/handoff.schema.json`
- Create: `office/contracts/gate.schema.json`
- Create: `office/contracts/escalation.schema.json`
- Create: `scripts/Office.Common.ps1`
- Create: `scripts/Test-Office.Core.ps1`

**Interfaces:**
- Produces: `Get-OfficeRegistry([string] $Root) -> PSCustomObject`
- Produces: `Assert-OfficeRegistry([pscustomobject] $Registry, [string] $Root) -> $null` or throws a precise validation error.
- Produces: `Get-OfficeContractSchema([string] $Name, [string] $Root) -> PSCustomObject`.
- Produces: `Assert-OfficeContractInstance([pscustomobject] $Value, [string] $Type, [pscustomobject] $Schema) -> $null` or throws.

- [ ] **Step 1: Write failing registry tests**

Add assertions for 31 unique IDs, one root Director, five coordinators, twenty-five specialists, known parent IDs, no cycles, known permission sets, existing prompt paths, and known capability IDs. Add fixtures in the test script for a duplicate ID, cycle, missing prompt, and unknown permission set; each must throw a matching error.

- [ ] **Step 2: Run the test and verify it fails**

Run: `pwsh -NoProfile -File scripts/Test-Office.Core.ps1 -Section Registry`

Expected: FAIL because `office/registry.json` and `Office.Common.ps1` do not exist.

- [ ] **Step 3: Implement canonical JSON and validation functions**

Create the exact 31-profile roster from the spec. Each registry record has `id`, `kind`, `department`, `parent`, `description`, `prompt`, `permission_set`, `skills`, and `capabilities`. Implement cycle detection and reference validation without external modules.

- [ ] **Step 4: Add contract-schema assertions**

Assert the exact enums and required fields from the spec, including task transitions, gate statuses, escalation triggers, and waiver fields. Add one valid and one invalid instance per contract type; missing required fields, invalid enums, and a waiver without approver/reason must fail.

- [ ] **Step 5: Run the registry section**

Run: `pwsh -NoProfile -File scripts/Test-Office.Core.ps1 -Section Registry`

Expected: PASS with `31 profiles; 4 contracts; 3 permission sets`.

- [ ] **Step 6: Commit**

```powershell
git add office/registry.json office/capabilities.json office/permission-sets office/contracts scripts/Office.Common.ps1 scripts/Test-Office.Core.ps1
git commit -m "feat: define canonical office registry"
```

### Task 2: Canonical prompts and routing graph

**Files:**
- Create: `office/roles/directora.md`
- Create: `office/roles/coord-producto-experiencia.md`
- Create: `office/roles/coord-ingenieria-datos.md`
- Create: `office/roles/coord-calidad-seguridad.md`
- Create: `office/roles/coord-operaciones-entrega.md`
- Create: `office/roles/coord-negocio-gobernanza.md`
- Create: `office/roles/{producto,diseno-web,ux-accesibilidad,seo-growth,data-analytics}.md`
- Create: `office/roles/{arquitectura,frontend,backend,mobile,datos-ia,integraciones}.md`
- Create: `office/roles/{qa,seguridad,auditoria,rendimiento}.md`
- Create: `office/roles/{devops,sre-observabilidad,forensics,release,documentacion}.md`
- Create: `office/roles/{marketing,social-contenido,finanzas,legal,experiencia-cliente}.md`
- Modify: `scripts/Test-Office.Core.ps1`

**Interfaces:**
- Consumes: registry records and contract field names from Task 1.
- Produces: `Get-OfficeRolePrompt([pscustomobject] $Role, [string] $Root) -> string`.

- [ ] **Step 1: Write failing prompt tests**

Assert every prompt names its owned domain, forbidden adjacent domains, expected output, applicable gate, escalation rules, and evidence requirement. Assert the Director can route only to five coordinators and each coordinator only to its registry children.

- [ ] **Step 2: Run and verify failure**

Run: `pwsh -NoProfile -File scripts/Test-Office.Core.ps1 -Section Roles`

Expected: FAIL listing the missing role files.

- [ ] **Step 3: Write the Director and five coordinator prompts**

Use the task/handoff/gate/escalation vocabulary from Task 1. Include minimal-route selection, sequential dependency handling, independent parallelism, human escalation, and evidence-based closure.

- [ ] **Step 4: Write the twenty-five specialist prompts**

Preserve useful constraints from existing profiles, but consolidate removed roles exactly as the spec directs. Keep prompts concise and point method detail to skills instead of duplicating it.

- [ ] **Step 5: Run role tests**

Run: `pwsh -NoProfile -File scripts/Test-Office.Core.ps1 -Section Roles`

Expected: PASS with `31 prompts; routing graph valid`.

- [ ] **Step 6: Commit**

```powershell
git add office/roles scripts/Test-Office.Core.ps1
git commit -m "feat: add unified office role prompts"
```

### Task 3: OpenCode generator

**Files:**
- Create: `scripts/Build-Office.ps1`
- Create: `scripts/render/Render-OpenCodeAgent.ps1`
- Modify: `scripts/Test-Office.Core.ps1`
- Generate: `.opencode/agents/*.md`
- Modify: `opencode.jsonc`

**Interfaces:**
- Consumes: validated registry, prompts, and permission sets.
- Produces: `ConvertTo-OpenCodeAgent([pscustomobject] $Role, [string] $Prompt, [pscustomobject] $PermissionSet) -> string`.
- Produces: `Build-Office.ps1 -Platform OpenCode|Codex|Both -Check` where `-Check` fails on drift without writing.

- [ ] **Step 1: Write failing OpenCode rendering tests**

Assert valid frontmatter, one `primary` Director, thirty `subagent` profiles, no model field, exact subagent allowlists, permission-set translation, generated-file headers, UTF-8 output, `experimental.subagent_depth = 2`, preservation of unrelated experimental keys, and byte-identical second generation.

- [ ] **Step 2: Run and verify failure**

Run: `pwsh -NoProfile -File scripts/Test-Office.Core.ps1 -Section OpenCode`

Expected: FAIL because the renderer is missing.

- [ ] **Step 3: Implement renderer and OpenCode build path**

Use ordered permission rules with broad deny before narrow allow. Render flat stable IDs rather than the old duplicate nested hierarchy. Replace the existing 23 project-generated agent files by exact name and remove only those obsolete outputs; never prune an unknown file by glob. Set `default_agent` to `directora` and merge `experimental.subagent_depth = 2` without changing unrelated OpenCode configuration.

- [ ] **Step 4: Generate and check drift**

Run: `pwsh -NoProfile -File scripts/Build-Office.ps1 -Platform OpenCode`

Run: `pwsh -NoProfile -File scripts/Build-Office.ps1 -Platform OpenCode -Check`

Expected: both succeed; the check reports zero drift.

- [ ] **Step 5: Run OpenCode tests and commit**

Run: `pwsh -NoProfile -File scripts/Test-Office.Core.ps1 -Section OpenCode`

Expected: PASS with `31 OpenCode agents`.

```powershell
git add scripts/Build-Office.ps1 scripts/render/Render-OpenCodeAgent.ps1 scripts/Test-Office.Core.ps1 .opencode/agents opencode.jsonc
git commit -m "feat: generate OpenCode office agents"
```

### Task 4: Codex generator and Director guidance

**Files:**
- Create: `scripts/render/Render-CodexAgent.ps1`
- Create: `templates/AGENTS-oficina.md`
- Modify: `scripts/Build-Office.ps1`
- Modify: `scripts/Test-Office.Core.ps1`
- Generate: `.codex/agents/*.toml`

**Interfaces:**
- Consumes: validated registry and prompts.
- Produces: `ConvertTo-CodexAgentToml([pscustomobject] $Role, [string] $Prompt) -> string` for thirty non-Director profiles.
- Produces: managed Director block bounded by `<!-- oficina-unificada:inicio -->` and `<!-- oficina-unificada:fin -->`.

- [ ] **Step 1: Write failing Codex rendering tests**

Assert thirty TOML files, required `name`, `description`, and `developer_instructions`, no pinned model, generated-file headers, valid multiline escaping, and a Director block that preserves prefix/suffix content in an `AGENTS.md` fixture.

- [ ] **Step 2: Run and verify failure**

Run: `pwsh -NoProfile -File scripts/Test-Office.Core.ps1 -Section Codex`

Expected: FAIL because the Codex renderer is missing.

- [ ] **Step 3: Implement renderer and managed-block helper**

Add `Set-ManagedInstructionBlock([string] $Existing, [string] $Block) -> string` to `Office.Common.ps1`. Escape prompt content with JSON serialization as the existing builder does, then validate the resulting TOML fields. Replace the existing 22 project-generated TOML files by exact name and remove only obsolete known outputs.

- [ ] **Step 4: Generate, check drift, and run tests**

Run: `pwsh -NoProfile -File scripts/Build-Office.ps1 -Platform Codex`

Run: `pwsh -NoProfile -File scripts/Build-Office.ps1 -Platform Codex -Check`

Run: `pwsh -NoProfile -File scripts/Test-Office.Core.ps1 -Section Codex`

Expected: PASS with `30 Codex subagents; Director block valid; zero drift`.

- [ ] **Step 5: Commit**

```powershell
git add scripts/render/Render-CodexAgent.ps1 scripts/Build-Office.ps1 scripts/Office.Common.ps1 scripts/Test-Office.Core.ps1 templates/AGENTS-oficina.md .codex/agents
git commit -m "feat: generate Codex office subagents"
```

### Task 5: Core integration and compatibility entrypoints

**Files:**
- Modify: `scripts/Test-Equipo.ps1`
- Modify: `scripts/Build-Codex-Agents.ps1`
- Modify: `README.md`
- Modify: `docs/guia-departamentos-y-delegacion.md`

**Interfaces:**
- Consumes: `Build-Office.ps1` and `Test-Office.Core.ps1`.
- Produces: old script names as thin compatibility entrypoints with deprecation messages.

- [ ] **Step 1: Add a failing compatibility test**

Assert both legacy scripts invoke the new core without maintaining a second roster, and README names one canonical source.

- [ ] **Step 2: Run and verify failure**

Run: `pwsh -NoProfile -File scripts/Test-Office.Core.ps1 -Section Compatibility`

Expected: FAIL because old scripts still own independent logic.

- [ ] **Step 3: Replace legacy logic with wrappers and update docs**

Keep supported command names but route them to `Build-Office.ps1` and the unified tests. Remove claims about 23/22 profiles and document the 31-profile conceptual roster.

- [ ] **Step 4: Run full core verification**

Run: `pwsh -NoProfile -File scripts/Test-Office.Core.ps1`

Run: `pwsh -NoProfile -File scripts/Build-Office.ps1 -Platform Both -Check`

Expected: PASS; 31 OpenCode profiles, 30 Codex subagents, one Director block, zero drift.

- [ ] **Step 5: Commit**

```powershell
git add scripts/Test-Equipo.ps1 scripts/Build-Codex-Agents.ps1 README.md docs/guia-departamentos-y-delegacion.md
git commit -m "docs: route kit through unified office core"
```
