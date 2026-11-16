param(
    [ValidateSet('OpenCode', 'Codex', 'Both')][string] $Platform = 'Both',
    [switch] $Check
)
$ErrorActionPreference = 'Stop'
# Task 4 extends this entrypoint; never silently invoke the obsolete generator.
if ($Platform -ne 'OpenCode') { throw 'Codex renderer not implemented yet. Use -Platform OpenCode.' }
$kitRoot = Split-Path -Parent $PSScriptRoot
. (Join-Path $PSScriptRoot 'Office.Common.ps1')
. (Join-Path $PSScriptRoot 'render/Render-OpenCodeAgent.ps1')
$registry = Get-OfficeRegistry $kitRoot
Assert-OfficeRegistry $registry $kitRoot

# Prepare every output before writing anything, including JSONC validation.
$outputs = [ordered]@{}
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

# Exact inventory of the 23 original project-generated outputs. Never glob-prune.
$legacyIds = @('directora', 'desarrollo', 'diseno', 'diseno-web', 'marketing', 'social-contenido', 'finanzas', 'operaciones', 'legal', 'producto', 'arquitectura', 'ux-web', 'frontend-web', 'backend', 'calidad', 'seguridad', 'plataforma-devops', 'datos-ia', 'documentacion', 'experiencia-cliente', 'direccion-arte', 'movimiento', 'imagenes')
$obsolete = @($legacyIds | ForEach-Object { ".opencode/agents/$_.md" } | Where-Object { -not $outputs.Contains($_) -and (Test-Path -LiteralPath (Join-Path $kitRoot $_) -PathType Leaf) })
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
    if ($drift.Count -gt 0) { throw "OpenCode drift: $($drift -join ', ')." }
    Write-Output 'PASS: 31 OpenCode agents; zero drift'
    return
}
foreach ($relative in $outputs.Keys) {
    $path = Join-Path $kitRoot $relative
    New-Item -ItemType Directory -Path (Split-Path -Parent $path) -Force | Out-Null
    [IO.File]::WriteAllText($path, $outputs[$relative], $utf8)
}
foreach ($relative in $obsolete) { Remove-Item -LiteralPath (Join-Path $kitRoot $relative) }
Write-Output 'Generated 31 OpenCode agents from office/; configuration merged.'
