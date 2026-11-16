param(
    [ValidateSet('OpenCode', 'Codex', 'Both')][string] $Platform = 'Both',
    [switch] $Check
)
$ErrorActionPreference = 'Stop'
$kitRoot = Split-Path -Parent $PSScriptRoot
. (Join-Path $PSScriptRoot 'Office.Common.ps1')
$registry = Get-OfficeRegistry $kitRoot
Assert-OfficeRegistry $registry $kitRoot

# Prepare every output before writing anything, including configuration and markers.
$outputs = [ordered]@{}
$legacyPaths = @()
$summary = [Collections.Generic.List[string]]::new()
# Exact inventory of the original project-generated outputs. Never glob-prune.
$legacySubagents = @('desarrollo', 'diseno', 'diseno-web', 'marketing', 'social-contenido', 'finanzas', 'operaciones', 'legal', 'producto', 'arquitectura', 'ux-web', 'frontend-web', 'backend', 'calidad', 'seguridad', 'plataforma-devops', 'datos-ia', 'documentacion', 'experiencia-cliente', 'direccion-arte', 'movimiento', 'imagenes')
if ($Platform -in @('OpenCode', 'Both')) {
    . (Join-Path $PSScriptRoot 'render/Render-OpenCodeAgent.ps1')
    foreach ($role in $registry.profiles) {
        $role | Add-Member -NotePropertyName allowed_subagents -NotePropertyValue @($registry.profiles | Where-Object parent -CEQ $role.id | Select-Object -ExpandProperty id)
        $prompt = Get-OfficeRolePrompt $role $kitRoot
        $permission = Get-Content -LiteralPath (Join-Path $kitRoot "office/permission-sets/$($role.permission_set).json") -Raw | ConvertFrom-Json
        $outputs[".opencode/agents/$($role.id).md"] = ConvertTo-OpenCodeAgent $role $prompt $permission
    }
    $configPath = Join-Path $kitRoot 'opencode.jsonc'
    $config = if (Test-Path -LiteralPath $configPath -PathType Leaf) {
        # PowerShell 7's JSON reader accepts JSONC comments and trailing commas.
        Get-Content -LiteralPath $configPath -Raw | ConvertFrom-Json -AsHashtable
    } else { [ordered]@{ '$schema' = 'https://opencode.ai/config.json' } }
    if ($config -isnot [Collections.IDictionary]) { throw 'OpenCode configuration must be a JSON object.' }
    $config['default_agent'] = 'directora'
    if (-not $config.Contains('experimental')) { $config['experimental'] = [ordered]@{} }
    if ($config['experimental'] -isnot [Collections.IDictionary]) { throw 'OpenCode experimental configuration must be an object.' }
    $config['experimental']['subagent_depth'] = 2
    $outputs['opencode.jsonc'] = (($config | ConvertTo-Json -Depth 100) -replace "`r`n", "`n") + "`n"
    $legacyPaths += @(@('directora') + $legacySubagents | ForEach-Object { ".opencode/agents/$_.md" })
    $summary.Add('31 OpenCode agents')
}
if ($Platform -in @('Codex', 'Both')) {
    . (Join-Path $PSScriptRoot 'render/Render-CodexAgent.ps1')
    foreach ($role in $registry.profiles | Where-Object kind -CNE 'director') {
        $outputs[".codex/agents/$($role.id).toml"] = ConvertTo-CodexAgentToml $role (Get-OfficeRolePrompt $role $kitRoot)
    }
    $director = $registry.profiles | Where-Object kind -CEQ 'director'
    $template = [IO.File]::ReadAllText((Join-Path $kitRoot 'templates/AGENTS-oficina.md'))
    $block = $template.Replace('{{DIRECTOR_PROMPT}}', (Get-OfficeRolePrompt $director $kitRoot).TrimEnd("`r", "`n"))
    $agentsPath = Join-Path $kitRoot 'AGENTS.md'
    $existing = if (Test-Path -LiteralPath $agentsPath -PathType Leaf) { [IO.File]::ReadAllText($agentsPath) } else { '' }
    $outputs['AGENTS.md'] = Set-ManagedInstructionBlock $existing $block
    $legacyPaths += @($legacySubagents | ForEach-Object { ".codex/agents/$_.toml" })
    $summary.Add('30 Codex subagents; Director block valid')
}
$obsolete = @($legacyPaths | Where-Object { -not $outputs.Contains($_) -and (Test-Path -LiteralPath (Join-Path $kitRoot $_) -PathType Leaf) })
$utf8 = [Text.UTF8Encoding]::new($false)
$drift = [Collections.Generic.List[string]]::new()
foreach ($relative in $outputs.Keys) {
    $path = Join-Path $kitRoot $relative
    $expected = [Convert]::ToBase64String($utf8.GetBytes($outputs[$relative]))
    if (-not (Test-Path -LiteralPath $path -PathType Leaf) -or [Convert]::ToBase64String([IO.File]::ReadAllBytes($path)) -cne $expected) {
        $drift.Add($relative)
    }
}
foreach ($relative in $obsolete) { $drift.Add($relative) }
if ($Check) {
    if ($drift.Count -gt 0) { throw "$Platform drift: $($drift -join ', ')." }
    Write-Output "PASS: $($summary -join '; '); zero drift"
    return
}
foreach ($relative in $outputs.Keys) {
    $path = Join-Path $kitRoot $relative
    New-Item -ItemType Directory -Path (Split-Path -Parent $path) -Force | Out-Null
    [IO.File]::WriteAllText($path, $outputs[$relative], $utf8)
}
foreach ($relative in $obsolete) { Remove-Item -LiteralPath (Join-Path $kitRoot $relative) }
Write-Output "Generated from office/: $($summary -join '; ')."
