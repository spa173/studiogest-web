# Office Installation, Migration, and Tool Connections Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the existing Codex and OpenCode offices with the unified generated office, preserving recoverability and reporting real MCP/connector coverage.

**Architecture:** A manifest-owned installer performs exact-path discovery, dry-run, backup, replacement, validation, and rollback. Tool connections are represented as logical capabilities and detected without reading secret values; a separate helper guides interactive OAuth or provider setup but never fabricates connectivity.

**Tech Stack:** PowerShell 7+, SHA-256 manifests, OpenCode CLI 2.3+, Codex global agent/config directories, existing plugin/MCP connections; no new package dependencies.

**Spec:** `docs/superpowers/specs/2026-11-16-oficina-unificada-codex-opencode-design.md`

## Global Constraints

- Run the core and skill plans first; this plan consumes their generated outputs.
- Replacement is authorized, but every material removal must have an exact validated target and a recoverable backup.
- Never recursively delete a computed Windows path without resolving and checking it against the intended agent/config directory.
- Preserve unrelated MCP servers, plugins, agents, configuration keys, and `AGENTS.md` content.
- Do not read or print secret values.
- Base installation detects and assigns connections; OAuth and external account changes remain interactive.
- Global OpenCode currently has 23 flat office profiles and 30 profiles under `agents/oficina/`; additional inherited project profiles may appear through configuration precedence.
- Codex global custom-agent installation belongs under `~/.codex/agents/`; Director guidance belongs in the managed block of `~/.codex/AGENTS.md`.

## Review Focus

- A modified legacy file with an unexpected hash must not be silently overwritten; Task 1 pins this.
- Backup restoration must recover byte-identical files after a simulated mid-install failure; Task 2 pins this.
- Re-running installation must be idempotent and must not duplicate the managed AGENTS block; Task 3 pins this.
- A configured-but-authentication-required connection must report `needs_auth`, not `connected`; Task 4 pins this.
- OpenCode configuration inherited from parent directories must not leave visible duplicate office agents after migration; Task 5 pins this.

---

### Task 1: Legacy ownership manifest and discovery

**Files:**
- Create: `office/legacy-files.json`
- Create: `scripts/Test-Office.Install.ps1`
- Modify: `scripts/Office.Common.ps1`

**Interfaces:**
- Produces: `Get-OfficeLegacyInventory([string] $Root) -> PSCustomObject`.
- Produces: `Resolve-OfficeTargetPath([string] $Base, [string] $RelativePath) -> string` and throws if the result escapes `$Base`.
- Produces: `Compare-OfficeOwnedFile([string] $Path, [string] $ExpectedHash) -> missing|match|modified`.

- [ ] **Step 1: Write failing exact-target tests**

Use temporary OpenCode and Codex directories. Assert known files are classified, `..` escape paths fail, an unknown file is never claimed, and a changed known file reports `modified`.

- [ ] **Step 2: Run and verify failure**

Run: `pwsh -NoProfile -File scripts/Test-Office.Install.ps1 -Section Inventory`

Expected: FAIL because the manifest and helpers are absent.

- [ ] **Step 3: Create the manifest from observed office-owned paths**

List the 23 current global flat profile paths, the exact 30 relative paths under `agents/oficina/`, old project-scoped office paths found in the current config chain, old generated Codex files, and managed marker names. Store a hash where the canonical prior source is known; use `null` only when ownership is established by an exact dedicated office directory.

- [ ] **Step 4: Implement path and hash validation**

Use `[System.IO.Path]::GetFullPath` and ordinal-ignore-case prefix checks against resolved expected bases. Do not pass enumerated targets between shells.

- [ ] **Step 5: Run and commit**

Run: `pwsh -NoProfile -File scripts/Test-Office.Install.ps1 -Section Inventory`

Expected: PASS.

```powershell
git add office/legacy-files.json scripts/Office.Common.ps1 scripts/Test-Office.Install.ps1
git commit -m "feat: inventory legacy office files"
```

### Task 2: Backup and restore engine

**Files:**
- Create: `scripts/Backup-Office.ps1`
- Create: `scripts/Restore-Office.ps1`
- Modify: `scripts/Test-Office.Install.ps1`

**Interfaces:**
- Produces: `Backup-Office.ps1 -Platform Codex|OpenCode|Both -SourcePaths <string[]> -BackupRoot <string>` returning the created backup path.
- Produces: `Restore-Office.ps1 -Backup <string> -Platform Codex|OpenCode|Both -DryRun`.
- Backup manifest fields: `version`, `created_at`, `platforms`, `files[] { original_path, backup_path, sha256 }`, and `config_sources`.

- [ ] **Step 1: Write failing round-trip tests**

Create temporary files, back them up, mutate/remove them, restore, and assert byte-identical SHA-256 hashes. Add traversal, missing-manifest, and unexpected-target cases that must fail safely.

- [ ] **Step 2: Run and verify failure**

Run: `pwsh -NoProfile -File scripts/Test-Office.Install.ps1 -Section BackupRestore`

Expected: FAIL because scripts are missing.

- [ ] **Step 3: Implement backup with a complete manifest**

Copy only resolved exact files into a timestamped directory on the same user profile. Write the manifest after all copies succeed; never store secret contents from unrelated configuration.

- [ ] **Step 4: Implement explicit and dry-run restore**

Validate every original destination before writing. Restore with native PowerShell operations in one shell and verify hashes afterward.

- [ ] **Step 5: Run and commit**

Run: `pwsh -NoProfile -File scripts/Test-Office.Install.ps1 -Section BackupRestore`

Expected: PASS including simulated partial failure recovery.

```powershell
git add scripts/Backup-Office.ps1 scripts/Restore-Office.ps1 scripts/Test-Office.Install.ps1
git commit -m "feat: add office backup and restore"
```

### Task 3: Idempotent installer and automatic rollback

**Files:**
- Replace: `scripts/Install-Equipo.ps1`
- Create: `scripts/Install-Office.ps1`
- Modify: `scripts/Test-Office.Install.ps1`

**Interfaces:**
- Produces: `Install-Office.ps1 -Platform Codex|OpenCode|Both -Scope Global|Project [-Target <string>] [-DryRun] [-Force]`.
- Produces: structured summary with `backup`, `removed`, `written`, `preserved`, `warnings`, and `validation`.

- [ ] **Step 1: Write failing installer tests**

Cover dry-run with zero writes, first installation, identical second installation, unexpected-hash conflict, preservation of unrelated agents/config, merge of `experimental.subagent_depth = 2`, migration of old managed markers, and rollback after an injected post-write validation failure.

- [ ] **Step 2: Run and verify failure**

Run: `pwsh -NoProfile -File scripts/Test-Office.Install.ps1 -Section Installer`

Expected: FAIL because the installer is absent.

- [ ] **Step 3: Implement dry-run and preflight**

Require successful core/skill build checks before any mutation. Resolve Codex/OpenCode global or project paths, discover config precedence, classify owned files, and display the exact plan.

- [ ] **Step 4: Implement backup, replacement, and managed-block merge**

Call the Task 2 backup engine first. Move only manifest-owned legacy files, install generated outputs and skills, preserve unrelated files, merge OpenCode `experimental.subagent_depth = 2` without replacing sibling settings, and merge Director instructions between owned markers.

- [ ] **Step 5: Implement validation and rollback**

Validate generated inventory, hashes, managed blocks, and platform discovery. On any failure call `Restore-Office.ps1` and exit nonzero.

- [ ] **Step 6: Keep the legacy installer as a wrapper**

`Install-Equipo.ps1` prints a deprecation notice and calls `Install-Office.ps1` without retaining duplicate installation logic.

- [ ] **Step 7: Run and commit**

Run: `pwsh -NoProfile -File scripts/Test-Office.Install.ps1 -Section Installer`

Expected: PASS with dry-run, idempotence, conflict blocking, and rollback proven.

```powershell
git add scripts/Install-Office.ps1 scripts/Install-Equipo.ps1 scripts/Test-Office.Install.ps1
git commit -m "feat: install unified office safely"
```

### Task 4: Capability detection and connection guidance

**Files:**
- Create: `scripts/Test-OfficeConnections.ps1`
- Create: `scripts/Connect-OfficeTools.ps1`
- Create: `docs/connections.md`
- Modify: `scripts/Test-Office.Install.ps1`

**Interfaces:**
- Produces: `Test-OfficeConnections.ps1 -Platform Codex|OpenCode|Both [-Json]`.
- Connection status enum: `connected | needs_auth | missing | not_applicable`.
- Produces: `Connect-OfficeTools.ps1 -Capability <id> -Platform <id> -DryRun`, which prints an official setup action but does not complete OAuth unattended.

- [ ] **Step 1: Write failing status-classification tests**

Use sanitized fixture configs for Codex GitHub/Linear/Notion and OpenCode browse/GitHub/Neon. Cover absent, disabled, configured, and authentication-required states without storing tokens.

- [ ] **Step 2: Run and verify failure**

Run: `pwsh -NoProfile -File scripts/Test-Office.Install.ps1 -Section Connections`

Expected: FAIL because detection scripts are missing.

- [ ] **Step 3: Implement provider-neutral detection**

Read only configuration keys, plugin status, and official CLI status output. Map physical providers to logical capabilities from `office/capabilities.json`; never infer connected from installation alone when authentication is required.

- [ ] **Step 4: Implement interactive guidance helper**

For missing capabilities, show the smallest approved provider set and the official connection step. Preserve an already connected provider. Require the user to choose between Mixpanel and Amplitude.

- [ ] **Step 5: Run and commit**

Run: `pwsh -NoProfile -File scripts/Test-Office.Install.ps1 -Section Connections`

Expected: PASS with no secret values in output.

```powershell
git add scripts/Test-OfficeConnections.ps1 scripts/Connect-OfficeTools.ps1 scripts/Test-Office.Install.ps1 docs/connections.md
git commit -m "feat: detect office tool connections"
```

### Task 5: Global migration to Codex and OpenCode

**Files:**
- Runtime targets: `C:/Users/camilo/.config/opencode/agents/`
- Runtime targets: `C:/Users/camilo/.codex/agents/`
- Runtime managed guidance: `C:/Users/camilo/.codex/AGENTS.md`
- Runtime configuration: existing OpenCode and Codex config files, preserved except owned managed entries

**Interfaces:**
- Consumes: all build, skill, installer, backup, and connection checks.
- Produces: one global office discoverable as real subagents in both platforms and a backup path suitable for explicit restore.

- [ ] **Step 1: Run every repository verification before migration**

Run: `pwsh -NoProfile -File scripts/Test-Office.Core.ps1`

Run: `pwsh -NoProfile -File scripts/Test-Office.Skills.ps1`

Run: `pwsh -NoProfile -File scripts/Test-Office.Install.ps1`

Run: `pwsh -NoProfile -File scripts/Build-Office.ps1 -Platform Both -Check`

Expected: all commands exit 0.

- [ ] **Step 2: Review exact dry-run output**

Run: `pwsh -NoProfile -File scripts/Install-Office.ps1 -Platform Both -Scope Global -DryRun`

Expected: only manifest-owned old profiles and owned managed blocks are listed for replacement; unrelated MCP and config entries are preserved.

- [ ] **Step 3: Execute global installation**

Run: `pwsh -NoProfile -File scripts/Install-Office.ps1 -Platform Both -Scope Global`

Expected: a backup path is printed; installation and validation succeed without rollback.

- [ ] **Step 4: Verify OpenCode discovery**

Run: `$agents = opencode debug agents | ConvertFrom-Json; $agents | Where-Object { -not $_.hidden } | Select-Object id,mode`

Expected: one `directora`, five office coordinators, twenty-five office specialists, built-ins, and no old office-owned duplicates in the active configuration chain.

- [ ] **Step 5: Verify Codex installation**

Run: `Get-ChildItem "$env:USERPROFILE/.codex/agents" -Filter '*.toml' | Measure-Object`

Expected: thirty generated office subagents plus any explicitly preserved unrelated personal agents; every office file passes the core TOML validator and `~/.codex/AGENTS.md` has one managed Director block.

- [ ] **Step 6: Report tool coverage**

Run: `pwsh -NoProfile -File scripts/Test-OfficeConnections.ps1 -Platform Both`

Expected: observed capabilities are reported as `connected`, `needs_auth`, `missing`, or `not_applicable`; no secret values appear.

- [ ] **Step 7: Commit migration evidence without user configuration**

Record commands, counts, backup location category, and statuses in `docs/verification.md`. Do not commit files from the user's global configuration or absolute backup contents.

```powershell
git add docs/verification.md
git commit -m "docs: record unified office verification"
```

### Task 6: Final operational documentation

**Files:**
- Modify: `README.md`
- Replace: `docs/guia-departamentos-y-delegacion.md`
- Create: `docs/recuperacion.md`
- Create: `docs/reference-research.md`

**Interfaces:**
- Consumes: verified commands and actual results from Task 5.
- Produces: start, delegate, connect, verify, and restore instructions for both platforms.

- [ ] **Step 1: Add a failing documentation consistency check**

Assert the documented roster count, script names, marker names, and commands match the registry and filesystem.

- [ ] **Step 2: Run and verify failure**

Run: `pwsh -NoProfile -File scripts/Test-Office.Install.ps1 -Section Documentation`

Expected: FAIL until docs are updated.

- [ ] **Step 3: Write the operational docs**

Explain that Codex main chat is Director and custom TOML files are real subagents; OpenCode uses a primary Director and subagent coordinators/specialists. Include reference-research behavior, connection statuses, backup/restore, and examples that invoke agents by stable ID.

- [ ] **Step 4: Run final verification**

Run: `pwsh -NoProfile -File scripts/Test-Office.Core.ps1`

Run: `pwsh -NoProfile -File scripts/Test-Office.Skills.ps1`

Run: `pwsh -NoProfile -File scripts/Test-Office.Install.ps1`

Expected: all PASS.

- [ ] **Step 5: Commit**

```powershell
git add README.md docs/guia-departamentos-y-delegacion.md docs/recuperacion.md docs/reference-research.md
git commit -m "docs: document unified office operations"
```
